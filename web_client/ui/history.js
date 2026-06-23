export function createHistoryView({
  store,
  historyEl,
  historyLogEl,
  historyContentEl,
  historyToggleEl,
  bufferSelectEl,
  a11y,
  initialMutedBuffers = [],
  onMutedBuffersChange = () => {},
  localize = (key, params = {}) => {
    let value = String(key || "");
    for (const [name, raw] of Object.entries(params || {})) {
      value = value.replaceAll(`{${name}}`, String(raw));
    }
    return value;
  },
  localizeBufferName = (name) => String(name || ""),
}) {
  const mutedBuffers = new Set();
  const bufferPositions = {};
  const isMobileLike = window.matchMedia("(pointer: coarse)").matches;
  let mobileCollapsed = isMobileLike;
  let renderedLogBuffer = "";
  let renderedLogValue = "";
  let renderScheduled = false;

  setMutedBuffers(initialMutedBuffers, { notify: false });

  function ensureBufferPosition(bufferName) {
    if (!Object.hasOwn(bufferPositions, bufferName)) {
      bufferPositions[bufferName] = 0;
    }
  }

  function normalizeBufferName(bufferName) {
    if (bufferName === "chats") {
      return "chat";
    }
    return String(bufferName || "misc");
  }

  function isBufferDirectlyMuted(bufferName) {
    return mutedBuffers.has(normalizeBufferName(bufferName));
  }

  function isBufferMuted(bufferName) {
    const name = normalizeBufferName(bufferName);
    return mutedBuffers.has("all") || mutedBuffers.has(name);
  }

  function getMutedBuffers() {
    return Array.from(mutedBuffers).sort();
  }

  function setMutedBuffers(bufferNames, { notify = false } = {}) {
    mutedBuffers.clear();
    for (const bufferName of Array.isArray(bufferNames) ? bufferNames : []) {
      const normalized = normalizeBufferName(bufferName);
      if (normalized) {
        mutedBuffers.add(normalized);
      }
    }
    render();
    if (notify) {
      onMutedBuffersChange(getMutedBuffers());
    }
  }

  function getBufferNames() {
    return Object.keys(store.state.historyBuffers);
  }

  function getCurrentBufferName() {
    return store.state.historyBuffer || "all";
  }

  function getCurrentBufferLines() {
    const bufferName = getCurrentBufferName();
    return store.state.historyBuffers[bufferName] || [];
  }

  function getCurrentBufferInfo() {
    const name = getCurrentBufferName();
    const lines = getCurrentBufferLines();
    const position = bufferPositions[name] || 0;
    return {
      name,
      count: lines.length,
      position,
      muted: isBufferDirectlyMuted(name),
      effectivelyMuted: isBufferMuted(name),
    };
  }

  function announceBufferInfo() {
    const info = getCurrentBufferInfo();
    const status = info.muted ? `, ${localize("buffer-status-muted")}` : "";
    a11y.announce(localize("main-buffer-info", {
      name: localizeBufferName(info.name),
      status,
      count: info.count,
    }), { assertive: true });
  }

  function getCurrentItemText() {
    const lines = getCurrentBufferLines();
    if (!lines.length) {
      return "";
    }
    const name = getCurrentBufferName();
    const position = Math.max(0, Math.min(lines.length - 1, bufferPositions[name] || 0));
    const index = lines.length - 1 - position;
    if (index < 0 || index >= lines.length) {
      return "";
    }
    return lines[index] || "";
  }

  function announceCurrentItem() {
    const text = getCurrentItemText();
    if (text) {
      a11y.announce(text, { assertive: true });
    } else {
      a11y.announce(localize("main-buffer-empty"), { assertive: true });
    }
  }

  function flushRender() {
    renderScheduled = false;
    for (const name of getBufferNames()) {
      ensureBufferPosition(name);
    }
    const bufferName = store.state.historyBuffer;
    const lines = isBufferMuted(bufferName) ? [] : (store.state.historyBuffers[bufferName] || []);
    if (bufferSelectEl && bufferSelectEl.value !== bufferName) {
      bufferSelectEl.value = bufferName;
    }
    const joined = lines.join("\n");
    if (renderedLogBuffer === bufferName && renderedLogValue === joined) {
      return;
    }
    renderedLogBuffer = bufferName;
    renderedLogValue = joined;

    historyEl.value = joined;
    historyEl.scrollTop = historyEl.scrollHeight;

    if (historyLogEl) {
      const fragment = document.createDocumentFragment();
      for (const line of lines) {
        const row = document.createElement("p");
        row.className = "history-line";
        row.textContent = line;
        fragment.appendChild(row);
      }
      historyLogEl.replaceChildren(fragment);
      historyLogEl.scrollTop = historyLogEl.scrollHeight;
    }
  }

  function render() {
    if (renderScheduled) {
      return;
    }
    renderScheduled = true;
    requestAnimationFrame(flushRender);
  }

  function renderMobileVisibility() {
    if (!historyContentEl || !historyToggleEl || !historyLogEl) {
      return;
    }
    if (!isMobileLike) {
      historyToggleEl.hidden = false;
      historyToggleEl.tabIndex = -1;
      historyToggleEl.setAttribute("aria-expanded", "true");
      historyContentEl.hidden = false;
      historyLogEl.setAttribute("aria-live", "off");
      historyLogEl.hidden = true;
      return;
    }
    historyToggleEl.tabIndex = -1;
    historyContentEl.hidden = mobileCollapsed;
    historyLogEl.setAttribute("aria-live", "off");
    historyLogEl.hidden = false;
    historyToggleEl.setAttribute("aria-expanded", mobileCollapsed ? "false" : "true");
  }

  function addEntry(text, options = {}) {
    const {
      buffer = "misc",
      announce = true,
      assertive = false,
    } = options;

    const normalizedBuffer = normalizeBufferName(buffer);
    const incomingBufferMuted = isBufferMuted(normalizedBuffer);
    const sourceDirectlyMuted = normalizedBuffer !== "all" && isBufferDirectlyMuted(normalizedBuffer);
    store.addHistory(normalizedBuffer, text, { includeAll: !sourceDirectlyMuted });
    if (announce && !incomingBufferMuted) {
      a11y.announce(text, { assertive });
    }
    return !incomingBufferMuted;
  }

  function switchBuffer({ step = 0, boundary = null } = {}) {
    const names = getBufferNames();
    if (!names.length) {
      return;
    }

    let nextIndex = Math.max(0, names.indexOf(getCurrentBufferName()));
    if (boundary === "first") {
      nextIndex = 0;
    } else if (boundary === "last") {
      nextIndex = names.length - 1;
    } else {
      nextIndex = Math.max(0, Math.min(names.length - 1, nextIndex + step));
    }
    store.setHistoryBuffer(names[nextIndex]);
    announceBufferInfo();
  }

  function moveInCurrentBuffer(direction) {
    const info = getCurrentBufferInfo();
    const maxPosition = Math.max(0, info.count - 1);
    let next = info.position;

    if (direction === "older") {
      next = Math.min(maxPosition, info.position + 1);
    } else if (direction === "newer") {
      next = Math.max(0, info.position - 1);
    } else if (direction === "oldest") {
      next = maxPosition;
    } else if (direction === "newest") {
      next = 0;
    }

    bufferPositions[info.name] = next;
    announceCurrentItem();
  }

  function toggleMuteCurrentBuffer() {
    const info = getCurrentBufferInfo();
    if (!info.name) {
      return;
    }
    if (mutedBuffers.has(info.name)) {
      mutedBuffers.delete(info.name);
    } else {
      mutedBuffers.add(info.name);
    }
    render();
    onMutedBuffersChange(getMutedBuffers());
    const status = localize(mutedBuffers.has(info.name) ? "buffer-status-muted" : "buffer-status-unmuted");
    a11y.announce(localize("main-buffer-status", {
      name: localizeBufferName(info.name),
      status,
    }), { assertive: true });
  }

  if (bufferSelectEl) {
    bufferSelectEl.addEventListener("change", () => {
      store.setHistoryBuffer(bufferSelectEl.value);
    });
  }
  if (historyToggleEl) {
    historyToggleEl.addEventListener("click", () => {
      mobileCollapsed = !mobileCollapsed;
      renderMobileVisibility();
    });
  }

  store.subscribe(render);
  renderMobileVisibility();
  flushRender();

  return {
    addEntry,
    isBufferMuted,
    getMutedBuffers,
    setMutedBuffers,
    render,
    previousBuffer() {
      switchBuffer({ step: -1 });
    },
    nextBuffer() {
      switchBuffer({ step: 1 });
    },
    firstBuffer() {
      switchBuffer({ boundary: "first" });
    },
    lastBuffer() {
      switchBuffer({ boundary: "last" });
    },
    olderMessage() {
      moveInCurrentBuffer("older");
    },
    newerMessage() {
      moveInCurrentBuffer("newer");
    },
    oldestMessage() {
      moveInCurrentBuffer("oldest");
    },
    newestMessage() {
      moveInCurrentBuffer("newest");
    },
    toggleCurrentBufferMute: toggleMuteCurrentBuffer,
    setCollapsed(collapsed) {
      mobileCollapsed = Boolean(collapsed);
      renderMobileVisibility();
    },
  };
}
