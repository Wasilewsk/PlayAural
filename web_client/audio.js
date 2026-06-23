function isAbsoluteUrl(path) {
  return /^https?:\/\//i.test(path);
}

function isCrossOriginUrl(url) {
  try {
    const target = new URL(url, window.location.href);
    return target.origin !== window.location.origin;
  } catch {
    return false;
  }
}

function createAudioElement(url) {
  const audio = new Audio();
  if (isCrossOriginUrl(url)) {
    // Required for Web Audio processing of cross-origin media.
    audio.crossOrigin = "anonymous";
  }
  audio.src = url;
  return audio;
}

function toSoundUrl(name, soundBaseUrl, soundVersion = "") {
  const rawName = String(name || "");
  if (!rawName) {
    return "";
  }
  if (isAbsoluteUrl(rawName) || rawName.startsWith("/")) {
    if (!soundVersion) {
      return rawName;
    }
    try {
      const url = new URL(rawName, window.location.href);
      url.searchParams.set("v", soundVersion);
      return url.toString();
    } catch {
      return rawName;
    }
  }
  const base = String(soundBaseUrl || "./sounds").replace(/\/+$/, "");
  const version = soundVersion ? `?v=${encodeURIComponent(soundVersion)}` : "";
  return `${base}/${rawName}${version}`;
}

const MAX_EFFECT_START_DELAY_MS = 1500;
const MAX_EFFECT_CACHE_ENTRIES = 96;
const PRELOAD_CONCURRENCY = 3;
const DEFAULT_PRELOAD_EFFECTS = [
  "menuclick.ogg",
  "menuenter.ogg",
  "chat.ogg",
  "chatlocal.ogg",
  "notify.ogg",
  "welcome.ogg",
  "pingstart.ogg",
  "pingstop.ogg",
  "typing1.ogg",
  "typing2.ogg",
  "typing3.ogg",
  "typing4.ogg",
];

export function createAudioEngine(options = {}) {
  const soundBaseUrl = options.soundBaseUrl || "./sounds";
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const context = AudioCtx ? new AudioCtx() : null;

  let effectsGain = null;
  let musicGain = null;
  let ambienceGain = null;
  let currentMusic = null;
  let currentMusicNodes = null;
  let currentMusicName = "";
  let currentMusicLooping = true;
  let pendingMusicPacket = null;
  let currentAmbience = null;
  let currentAmbienceNodes = null;
  let currentAmbienceLoop = null;
  let currentAmbienceLoopNodes = null;
  let currentAmbienceLoopName = "";
  let pendingAmbiencePacket = null;
  const pendingEffectPackets = [];
  const MAX_PENDING_EFFECTS = 24;
  const activeEffects = new Map();
  const activeBufferEffects = new Set();
  const effectBufferCache = new Map();
  const preloadQueue = [];
  const preloadQueued = new Set();
  const effectBaseVolumes = new WeakMap();
  let activePreloads = 0;
  let muted = false;
  let soundVersion = "";

  if (context) {
    effectsGain = context.createGain();
    musicGain = context.createGain();
    ambienceGain = context.createGain();

    effectsGain.gain.value = 1.0;
    musicGain.gain.value = 0.2;
    ambienceGain.gain.value = 1.0;

    effectsGain.connect(context.destination);
    musicGain.connect(context.destination);
    ambienceGain.connect(context.destination);
  }

  async function unlock() {
    if (!context) {
      retryPendingPlayback();
      return false;
    }
    if (context.state !== "running") {
      await context.resume();
    }
    preloadEffects(DEFAULT_PRELOAD_EFFECTS);
    retryPendingPlayback();
    return context.state === "running";
  }

  function safePlay(audio, { onRejected } = {}) {
    audio.muted = muted;
    try {
      const maybePromise = audio.play();
      if (maybePromise && typeof maybePromise.catch === "function") {
        maybePromise.catch(() => {
          if (onRejected) {
            onRejected();
          }
        });
      }
    } catch {
      if (onRejected) {
        onRejected();
      }
    }
  }

  function connectElement(audio, gainNode, panValue = 0, url = "") {
    if (!context || !gainNode) {
      return null;
    }

    if (isCrossOriginUrl(url)) {
      // Cross-origin media can be silenced by Web Audio without CORS;
      // let the element play directly as a fallback.
      return null;
    }

    try {
      const source = context.createMediaElementSource(audio);
      if (typeof context.createStereoPanner === "function") {
        const panner = context.createStereoPanner();
        panner.pan.value = Math.max(-1, Math.min(1, panValue));
        source.connect(panner);
        panner.connect(gainNode);
        return { source, panner };
      }
      source.connect(gainNode);
      return { source, panner: null };
    } catch {
      // Fallback to direct element playback if node creation fails.
      return null;
    }
  }

  function disconnectNodes(nodes) {
    if (!nodes) return;
    try { nodes.source.disconnect(); } catch { /* already disconnected */ }
    if (nodes.panner) {
      try { nodes.panner.disconnect(); } catch { /* already disconnected */ }
    }
  }

  function canUseBufferedEffects(url = "") {
    return Boolean(context && effectsGain && window.fetch && !isCrossOriginUrl(url));
  }

  function touchBufferCache(key) {
    const buffer = effectBufferCache.get(key);
    if (!buffer) {
      return null;
    }
    effectBufferCache.delete(key);
    effectBufferCache.set(key, buffer);
    return buffer;
  }

  function trimBufferCache() {
    while (effectBufferCache.size > MAX_EFFECT_CACHE_ENTRIES) {
      const oldest = effectBufferCache.keys().next().value;
      if (oldest === undefined) {
        return;
      }
      effectBufferCache.delete(oldest);
    }
  }

  async function loadEffectBuffer(url) {
    if (!canUseBufferedEffects(url)) {
      return null;
    }
    const cached = touchBufferCache(url);
    if (cached) {
      return cached;
    }
    const response = await fetch(url, { cache: "force-cache" });
    if (!response.ok) {
      return null;
    }
    const arrayBuffer = await response.arrayBuffer();
    const decoded = await context.decodeAudioData(arrayBuffer);
    effectBufferCache.set(url, decoded);
    trimBufferCache();
    return decoded;
  }

  function pumpPreloadQueue() {
    if (!context || context.state !== "running") {
      return;
    }
    while (activePreloads < PRELOAD_CONCURRENCY && preloadQueue.length) {
      const url = preloadQueue.shift();
      if (!url || effectBufferCache.has(url)) {
        preloadQueued.delete(url);
        continue;
      }
      activePreloads += 1;
      loadEffectBuffer(url)
        .catch(() => null)
        .finally(() => {
          activePreloads -= 1;
          preloadQueued.delete(url);
          pumpPreloadQueue();
        });
    }
  }

  function preloadEffects(names = []) {
    if (!context) {
      return;
    }
    for (const name of names) {
      const url = toSoundUrl(name, soundBaseUrl, soundVersion);
      if (!url || !canUseBufferedEffects(url) || effectBufferCache.has(url) || preloadQueued.has(url)) {
        continue;
      }
      preloadQueued.add(url);
      preloadQueue.push(url);
    }
    pumpPreloadQueue();
  }

  function cleanupBufferEffect(effect) {
    if (!activeBufferEffects.has(effect)) {
      return;
    }
    activeBufferEffects.delete(effect);
    try { effect.source.disconnect(); } catch { /* already disconnected */ }
    if (effect.panner) {
      try { effect.panner.disconnect(); } catch { /* already disconnected */ }
    }
    try { effect.gain.disconnect(); } catch { /* already disconnected */ }
    if (effect.timeoutId) {
      window.clearTimeout(effect.timeoutId);
    }
  }

  function playBufferedEffect(packet, url, queuedAt = performance.now()) {
    if (!canUseBufferedEffects(url) || context.state !== "running") {
      return false;
    }

    const cached = touchBufferCache(url);
    if (!cached) {
      loadEffectBuffer(url).catch(() => null);
      return false;
    }

    if (performance.now() - queuedAt > MAX_EFFECT_START_DELAY_MS) {
      return true;
    }

    let effect = null;
    try {
      const source = context.createBufferSource();
      const gain = context.createGain();
      const baseVolume = Math.max(0, Math.min(1, (packet.volume ?? 100) / 100));
      source.buffer = cached;
      source.playbackRate.value = Math.max(0.5, Math.min(2, (packet.pitch ?? 100) / 100));
      gain.gain.value = muted ? 0 : baseVolume;

      let panner = null;
      if (typeof context.createStereoPanner === "function") {
        panner = context.createStereoPanner();
        panner.pan.value = Math.max(-1, Math.min(1, (packet.pan ?? 0) / 100));
        source.connect(panner);
        panner.connect(gain);
      } else {
        source.connect(gain);
      }
      gain.connect(effectsGain);

      effect = { source, gain, panner, timeoutId: null, done: false, baseVolume };
      activeBufferEffects.add(effect);
      const finish = () => {
        if (effect.done) {
          return;
        }
        effect.done = true;
        cleanupBufferEffect(effect);
        if (typeof packet.onEnded === "function") {
          packet.onEnded();
        }
      };
      source.addEventListener("ended", finish, { once: true });
      effect.timeoutId = window.setTimeout(finish, Math.max(250, cached.duration * 1000 + 500));
      source.start(0);
      return true;
    } catch {
      if (effect) {
        cleanupBufferEffect(effect);
      }
      return false;
    }
  }

  function playSound(packet) {
    const name = packet.name || packet.sound || "";
    const url = toSoundUrl(name, soundBaseUrl, soundVersion);
    if (!url) {
      return;
    }

    const queuedAt = performance.now();
    if (playBufferedEffect(packet, url, queuedAt)) {
      return;
    }

    const audio = createAudioElement(url);
    audio.muted = muted;
    audio.preload = "auto";
    const baseVolume = Math.max(0, Math.min(1, (packet.volume ?? 100) / 100));
    audio.volume = baseVolume;
    effectBaseVolumes.set(audio, baseVolume);
    audio.playbackRate = Math.max(0.5, Math.min(2, (packet.pitch ?? 100) / 100));

    try {
      const nodes = connectElement(audio, effectsGain, (packet.pan ?? 0) / 100, url);
      if (!nodes && effectsGain) {
        audio.volume = baseVolume * effectsGain.gain.value;
      }
      activeEffects.set(audio, nodes);
      const cleanup = () => {
        activeEffects.delete(audio);
        effectBaseVolumes.delete(audio);
        disconnectNodes(nodes);
      };
      audio.addEventListener("ended", cleanup);
      audio.addEventListener("error", cleanup);
      if (typeof packet.onEnded === "function") {
        audio.addEventListener("ended", packet.onEnded, { once: true });
      }
      safePlay(audio, {
        onRejected: () => {
          cleanup();
          if (pendingEffectPackets.length >= MAX_PENDING_EFFECTS) {
            pendingEffectPackets.shift();
          }
          pendingEffectPackets.push({
            name,
            volume: packet.volume ?? 100,
            pan: packet.pan ?? 0,
            pitch: packet.pitch ?? 100,
          });
        },
      });
    } catch {
      // Ignore autoplay/stream failures before unlock.
    }
  }

  function playMusic(packet) {
    const name = packet.name || packet.music || "";
    const url = toSoundUrl(name, soundBaseUrl, soundVersion);
    if (!url) {
      return;
    }
    const looping = packet.looping ?? true;

    // Match desktop behavior: don't restart music if the same track is already active.
    if (currentMusic && currentMusicName === name && currentMusicLooping === looping) {
      if (currentMusic.paused) {
        safePlay(currentMusic, {
          onRejected: () => {
            pendingMusicPacket = { name, looping };
          },
        });
      }
      return;
    }

    stopMusic();

    const audio = createAudioElement(url);
    audio.muted = muted;
    audio.preload = "auto";
    audio.loop = looping;
    audio.volume = 1.0;

    try {
      const nodes = connectElement(audio, musicGain, 0, url);
      if (!nodes && musicGain) {
        audio.volume *= musicGain.gain.value;
      }
      currentMusic = audio;
      currentMusicNodes = nodes;
      currentMusicName = name;
      currentMusicLooping = looping;
      pendingMusicPacket = null;
      if (typeof packet.onEnded === "function") {
        audio.addEventListener("ended", packet.onEnded, { once: true });
      }
      safePlay(audio, {
        onRejected: () => {
          pendingMusicPacket = { name, looping };
        },
      });
    } catch {
      currentMusic = audio;
      currentMusicNodes = null;
      currentMusicName = name;
      currentMusicLooping = looping;
      pendingMusicPacket = { name, looping };
    }
  }

  function stopMusic() {
    if (!currentMusic) {
      return;
    }
    try {
      currentMusic.pause();
      currentMusic.currentTime = 0;
    } catch {
      // Ignore stop failures.
    }
    disconnectNodes(currentMusicNodes);
    currentMusic = null;
    currentMusicNodes = null;
    currentMusicName = "";
    currentMusicLooping = true;
    pendingMusicPacket = null;
  }

  function stopAmbience() {
    if (currentAmbience) {
      try {
        currentAmbience.pause();
        currentAmbience.currentTime = 0;
      } catch {
        // Ignore stop failures.
      }
      disconnectNodes(currentAmbienceNodes);
      currentAmbience = null;
      currentAmbienceNodes = null;
    }
    if (currentAmbienceLoop) {
      try {
        currentAmbienceLoop.pause();
        currentAmbienceLoop.currentTime = 0;
      } catch {
        // Ignore stop failures.
      }
      disconnectNodes(currentAmbienceLoopNodes);
      currentAmbienceLoop = null;
      currentAmbienceLoopNodes = null;
    }
    currentAmbienceLoopName = "";
    pendingAmbiencePacket = null;
  }

  function playAmbience(packet) {
    const loopName = packet.loop || "";
    const introName = packet.intro || "";
    if (!loopName) {
      return;
    }
    if (currentAmbienceLoop && currentAmbienceLoopName === loopName) {
      if (currentAmbienceLoop.paused) {
        safePlay(currentAmbienceLoop, {
          onRejected: () => {
            pendingAmbiencePacket = {
              loop: loopName,
              intro: introName,
              outro: packet.outro || "",
            };
          },
        });
      }
      return;
    }

    stopAmbience();

    const loopAudio = createAudioElement(toSoundUrl(loopName, soundBaseUrl, soundVersion));
    loopAudio.muted = muted;
    loopAudio.preload = "auto";
    loopAudio.loop = true;
    loopAudio.volume = 1.0;
    const loopUrl = toSoundUrl(loopName, soundBaseUrl, soundVersion);
    const loopNodes = connectElement(loopAudio, ambienceGain, 0, loopUrl);
    if (!loopNodes && ambienceGain) {
      loopAudio.volume *= ambienceGain.gain.value;
    }

    const startLoop = () => {
      currentAmbienceLoop = loopAudio;
      currentAmbienceLoopNodes = loopNodes;
      currentAmbienceLoopName = loopName;
      pendingAmbiencePacket = null;
      safePlay(loopAudio, {
        onRejected: () => {
          pendingAmbiencePacket = {
            loop: loopName,
            intro: introName,
            outro: packet.outro || "",
          };
        },
      });
    };

    if (introName) {
      const introAudio = createAudioElement(toSoundUrl(introName, soundBaseUrl, soundVersion));
      introAudio.muted = muted;
      introAudio.preload = "auto";
      introAudio.loop = false;
      introAudio.volume = 1.0;
      const introUrl = toSoundUrl(introName, soundBaseUrl, soundVersion);
      const introNodes = connectElement(introAudio, ambienceGain, 0, introUrl);
      if (!introNodes && ambienceGain) {
        introAudio.volume *= ambienceGain.gain.value;
      }
      introAudio.addEventListener("ended", () => {
        disconnectNodes(introNodes);
        currentAmbienceNodes = null;
        startLoop();
      }, { once: true });
      currentAmbience = introAudio;
      currentAmbienceNodes = introNodes;
      safePlay(introAudio, {
        onRejected: () => {
          pendingAmbiencePacket = {
            loop: loopName,
            intro: introName,
            outro: packet.outro || "",
          };
          startLoop();
        },
      });
      return;
    }

    startLoop();
  }

  function retryPendingPlayback() {
    if (pendingMusicPacket) {
      const packet = pendingMusicPacket;
      pendingMusicPacket = null;
      playMusic(packet);
    }
    if (pendingAmbiencePacket) {
      const packet = pendingAmbiencePacket;
      pendingAmbiencePacket = null;
      playAmbience(packet);
    }
    if (pendingEffectPackets.length > 0) {
      const packets = pendingEffectPackets.splice(0, pendingEffectPackets.length);
      for (const packet of packets) {
        playSound(packet);
      }
    }
  }

  function setMusicVolumePercent(percent) {
    const bounded = Math.max(0, Math.min(100, Number(percent)));
    if (musicGain) {
      musicGain.gain.value = bounded / 100;
    } else if (currentMusic) {
      currentMusic.volume = bounded / 100;
    }
    return bounded;
  }

  function setAmbienceVolumePercent(percent) {
    const bounded = Math.max(0, Math.min(100, Number(percent)));
    if (ambienceGain) {
      ambienceGain.gain.value = bounded / 100;
    } else {
      if (currentAmbience) {
        currentAmbience.volume = bounded / 100;
      }
      if (currentAmbienceLoop) {
        currentAmbienceLoop.volume = bounded / 100;
      }
    }
    return bounded;
  }

  function setEffectsVolumePercent(percent) {
    const bounded = Math.max(0, Math.min(100, Number(percent)));
    if (effectsGain) {
      effectsGain.gain.value = bounded / 100;
    }
    for (const [audio, nodes] of activeEffects) {
      if (!nodes) {
        audio.volume = (effectBaseVolumes.get(audio) ?? 1) * (bounded / 100);
      }
    }
    return bounded;
  }

  function setMuted(nextMuted) {
    muted = Boolean(nextMuted);
    if (currentMusic) {
      currentMusic.muted = muted;
    }
    if (currentAmbience) {
      currentAmbience.muted = muted;
    }
    if (currentAmbienceLoop) {
      currentAmbienceLoop.muted = muted;
    }
    for (const effect of activeEffects.keys()) {
      effect.muted = muted;
    }
    for (const effect of activeBufferEffects) {
      try {
        effect.gain.gain.value = muted ? 0 : effect.baseVolume;
      } catch {
        // Ignore effects that are already ending.
      }
    }
  }

  function isMuted() {
    return muted;
  }

  function getMusicVolumePercent() {
    if (musicGain) {
      return Math.round(musicGain.gain.value * 100);
    }
    if (currentMusic) {
      return Math.round(currentMusic.volume * 100);
    }
    return 20;
  }

  function getAmbienceVolumePercent() {
    if (ambienceGain) {
      return Math.round(ambienceGain.gain.value * 100);
    }
    if (currentAmbienceLoop) {
      return Math.round(currentAmbienceLoop.volume * 100);
    }
    return 100;
  }

  function getEffectsVolumePercent() {
    if (effectsGain) {
      return Math.round(effectsGain.gain.value * 100);
    }
    return 100;
  }

  function setSoundVersion(version) {
    const nextVersion = String(version || "");
    if (nextVersion === soundVersion) {
      return;
    }
    soundVersion = nextVersion;
    effectBufferCache.clear();
    preloadQueue.length = 0;
    preloadQueued.clear();
  }

  function stopAll() {
    stopMusic();
    stopAmbience();
    for (const [audio, nodes] of activeEffects) {
      try {
        audio.pause();
        audio.currentTime = 0;
      } catch {
        // Ignore per-element stop failures.
      }
      disconnectNodes(nodes);
    }
    activeEffects.clear();
    for (const effect of Array.from(activeBufferEffects)) {
      try {
        effect.done = true;
        effect.source.stop();
      } catch {
        // Ignore per-buffer stop failures.
      }
      cleanupBufferEffect(effect);
    }
  }

  return {
    unlock,
    playSound,
    playMusic,
    playAmbience,
    stopMusic,
    stopAmbience,
    stopAll,
    setMusicVolumePercent,
    setAmbienceVolumePercent,
    setEffectsVolumePercent,
    getMusicVolumePercent,
    getAmbienceVolumePercent,
    getEffectsVolumePercent,
    setSoundVersion,
    preloadEffects,
    setMuted,
    isMuted,
    retryPendingPlayback,
  };
}
