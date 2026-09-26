class RemoteWS {
  constructor() {
    this.ws = null;
    this.reconnectTimer = null;
    this.isConnected = false;
    this.listeners = {
      open: [],
      close: [],
      message: []
    };
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws`;

    console.log(`[WS] Connecting to ${wsUrl}...`);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.isConnected = true;
      console.log("[WS] Connected to Presentation Server");
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
      this.trigger("open");
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      console.warn("[WS] Disconnected. Reconnecting in 2s...");
      this.trigger("close");
      this.scheduleReconnect();
    };

    this.ws.onerror = (err) => {
      console.error("[WS] Error:", err);
      this.ws.close();
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.trigger("message", msg);
      } catch (e) {
        console.error("[WS] Failed to parse message:", e);
      }
    };
  }

  scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 2000);
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  sendAction(action, extra = {}) {
    return this.send({
      type: "action",
      action: action,
      ...extra
    });
  }

  sendLaserMove(dx, dy, visible = true, sensitivity = 2.0) {
    return this.send({
      type: "laser_move",
      dx: dx,
      dy: dy,
      visible: visible,
      sensitivity: sensitivity
    });
  }

  sendLaserPos(xNorm, yNorm, visible = true) {
    return this.send({
      type: "laser_pos",
      x: xNorm,
      y: yNorm,
      visible: visible
    });
  }

  sendLaserState(visible) {
    return this.send({
      type: "laser_state",
      visible: visible
    });
  }

  sendLaserConfig(color, mode = "laser") {
    return this.send({
      type: "laser_config",
      color: color,
      mode: mode
    });
  }

  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
  }

  trigger(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

window.remoteWS = new RemoteWS();
