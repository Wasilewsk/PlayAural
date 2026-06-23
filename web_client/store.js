const HISTORY_BUFFER_ORDER = ["all", "chat", "game", "system", "misc"];
const HISTORY_BUFFER_LIMIT = 500;

function createHistoryBuffers() {
  return Object.fromEntries(HISTORY_BUFFER_ORDER.map((name) => [name, []]));
}

function normalizeHistoryBuffer(buffer) {
  if (buffer === "chats") {
    return "chat";
  }
  return HISTORY_BUFFER_ORDER.includes(buffer) ? buffer : "misc";
}

function pushCapped(buffer, text) {
  buffer.push(text);
  if (buffer.length > HISTORY_BUFFER_LIMIT) {
    buffer.splice(0, buffer.length - HISTORY_BUFFER_LIMIT);
  }
}

export function createStore() {
  const state = {
    connection: {
      status: "disconnected",
      authenticated: false,
      serverUrl: "",
      username: "",
      lastError: "",
    },
    currentMenu: {
      menuId: null,
      items: [],
      selection: 0,
      multiletterEnabled: true,
      escapeBehavior: "keybind",
      gridEnabled: false,
      gridWidth: 1,
    },
    historyBuffers: createHistoryBuffers(),
    historyBuffer: "all",
    audioUnlocked: false,
    pendingInput: null,
    serverOptions: {
      games: [],
      languages: {},
    },
  };

  const listeners = new Set();

  function notify() {
    for (const listener of listeners) {
      listener(state);
    }
  }

  return {
    state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setConnection(patch) {
      Object.assign(state.connection, patch);
      notify();
    },
    setMenu(menuPatch) {
      Object.assign(state.currentMenu, menuPatch);
      notify();
    },
    addHistory(buffer, text) {
      const normalized = normalizeHistoryBuffer(buffer);
      pushCapped(state.historyBuffers[normalized], text);
      if (normalized !== "all") {
        pushCapped(state.historyBuffers.all, text);
      }
      notify();
    },
    clearUi() {
      state.currentMenu = {
        menuId: null,
        items: [],
        selection: 0,
        multiletterEnabled: true,
        escapeBehavior: "keybind",
        gridEnabled: false,
        gridWidth: 1,
      };
      notify();
    },
    setHistoryBuffer(buffer) {
      state.historyBuffer = HISTORY_BUFFER_ORDER.includes(buffer) ? buffer : "all";
      notify();
    },
    setAudioUnlocked(unlocked) {
      state.audioUnlocked = unlocked;
      notify();
    },
    setPendingInput(inputState) {
      state.pendingInput = inputState;
      notify();
    },
    setServerOptions(patch) {
      Object.assign(state.serverOptions, patch);
      notify();
    },
  };
}
