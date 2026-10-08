document.addEventListener("DOMContentLoaded", () => {
  const ws = window.remoteWS;

  // DOM Elements
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  const trackpad = document.getElementById("trackpad");
  const trackpadDot = document.getElementById("trackpad-dot");
  const btnNext = document.getElementById("btn-next");
  const btnPrev = document.getElementById("btn-prev");
  const btnBlackout = document.getElementById("btn-blackout");
  const btnWhiteout = document.getElementById("btn-whiteout");
  const btnStart = document.getElementById("btn-start");
  const btnResume = document.getElementById("btn-resume");
  const btnLaserToggle = document.getElementById("btn-laser-toggle");
  const btnExit = document.getElementById("btn-exit");
  const btnFullscreen = document.getElementById("btn-fullscreen");
  const btnMore = document.getElementById("btn-more");
  const btnCloseDrawer = document.getElementById("btn-close-drawer");
  const extraDrawer = document.getElementById("extra-drawer");
  const timerDisplay = document.getElementById("timer-display");
  const btnTimerToggle = document.getElementById("btn-timer-toggle");
  const btnTimerReset = document.getElementById("btn-timer-reset");
  const canvaBtns = document.querySelectorAll(".canva-btn");
  const gyroToggle = document.getElementById("gyro-toggle");
  const gyroSpeedBtn = document.getElementById("gyro-speed");

  // Gyroscope Speed Modes (RPS & Sensitivity)
  const speedModes = [
    { text: "⚡ Kecepatan: 1x (Normal)", mult: 1.0 },
    { text: "⚡ Kecepatan: 2x (Cepat)", mult: 2.0 },
    { text: "⚡ Kecepatan: 3x (Turbo)", mult: 3.5 }
  ];
  let speedModeIndex = 1; // Default 2x
  let gyroSpeedMultiplier = 2.0;

  if (gyroSpeedBtn) {
    gyroSpeedBtn.addEventListener("click", () => {
      speedModeIndex = (speedModeIndex + 1) % speedModes.length;
      gyroSpeedMultiplier = speedModes[speedModeIndex].mult;
      gyroSpeedBtn.textContent = speedModes[speedModeIndex].text;
      vibrate(25);
    });
  }

  // State
  let lastTouchX = 0;
  let lastTouchY = 0;
  let touchStartTime = 0;
  let touchStartDist = 0;
  let isTouching = false;
  let sensitivity = 2.2;
  let laserColor = "red";
  let wakeLock = null;

  // Timer State
  let timerInterval = null;
  let timerSeconds = 0;
  let isTimerRunning = false;

  // Gyroscope State
  let isGyroActive = false;
  let lastGyroBeta = null;
  let lastGyroGamma = null;

  // Haptic feedback utility
  const vibrate = (pattern = 30) => {
    if ("vibrate" in navigator) {
      try {
        navigator.vibrate(pattern);
      } catch (e) {}
    }
  };

  // Screen WakeLock to keep screen on during presentation
  const requestWakeLock = async () => {
    if ("wakeLock" in navigator && !wakeLock) {
      try {
        wakeLock = await navigator.wakeLock.request("screen");
        console.log("[WakeLock] Screen wake lock active");
      } catch (err) {
        console.warn("[WakeLock] Could not acquire wake lock:", err);
      }
    }
  };

  // WebSocket Connection Handlers
  ws.on("open", () => {
    statusDot.classList.add("connected");
    statusText.textContent = "Terhubung";
  });

  ws.on("close", () => {
    statusDot.classList.remove("connected");
    statusText.textContent = "Menghubungkan...";
  });

  ws.on("message", (msg) => {
    if (msg.type === "pong") {
      // heartbeats if needed
    }
  });

  // Start WS connection
  ws.connect();

  // Slide Navigation with client-side debounce guard
  let lastNavTime = 0;
  const navDebounceMs = 250;

  const triggerNav = (action, vibTime = 30) => {
    const now = Date.now();
    if (now - lastNavTime < navDebounceMs) return;
    lastNavTime = now;
    vibrate(vibTime);
    requestWakeLock();
    ws.sendAction(action);
  };
  window.triggerNav = triggerNav;

  btnNext.addEventListener("click", (e) => {
    e.preventDefault();
    triggerNav("next", 40);
  });

  btnPrev.addEventListener("click", (e) => {
    e.preventDefault();
    triggerNav("prev", 30);
  });

  // Keyboard shortcut listener on mobile (e.g. Volume Keys if wrapped or hardware keyboard)
  window.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === "PageDown" || e.code === "VolumeUp") {
      triggerNav("next", 30);
    } else if (e.key === "ArrowLeft" || e.key === "PageUp" || e.code === "VolumeDown") {
      triggerNav("prev", 30);
    }
  });

  // Quick Tools
  if (btnBlackout) {
    btnBlackout.addEventListener("click", () => {
      vibrate(35);
      ws.sendAction("blackout");
    });
  }

  if (btnWhiteout) {
    btnWhiteout.addEventListener("click", () => {
      vibrate(35);
      ws.sendAction("whiteout");
    });
  }

  if (btnStart) {
    btnStart.addEventListener("click", () => {
      vibrate(50);
      ws.sendAction("start");
    });
  }

  if (btnResume) {
    btnResume.addEventListener("click", () => {
      vibrate(40);
      ws.sendAction("resume");
    });
  }

  let isLaserPointerOn = false;
  if (btnLaserToggle) {
    btnLaserToggle.addEventListener("click", () => {
      isLaserPointerOn = !isLaserPointerOn;
      vibrate(35);
      ws.sendLaserState(isLaserPointerOn);
      btnLaserToggle.classList.toggle("active", isLaserPointerOn);
    });
  }

  btnExit.addEventListener("click", () => {
    vibrate(35);
    ws.sendAction("exit");
  });

  btnFullscreen.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  });

  // Extra Drawer (Canva & Advanced shortcuts)
  btnMore.addEventListener("click", () => {
    extraDrawer.classList.add("open");
  });

  btnCloseDrawer.addEventListener("click", () => {
    extraDrawer.classList.remove("open");
  });

  canvaBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const effect = btn.getAttribute("data-effect");
      vibrate(30);
      ws.sendAction("canva", { effect });
    });
  });

  // Laser Pointer Trackpad
  // Laser Pointer Trackpad (Supports Touch and Mouse Pointer Drag)
  let isPointerActive = false;

  const updateTrackpadDotPos = (clientX, clientY) => {
    const rect = trackpad.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, clientX - rect.left));
    const y = Math.max(0, Math.min(rect.height, clientY - rect.top));
    trackpadDot.style.left = `${x}px`;
    trackpadDot.style.top = `${y}px`;
  };

  const startPointer = (clientX, clientY) => {
    requestWakeLock();
    isTouching = true;
    lastTouchX = clientX;
    lastTouchY = clientY;
    touchStartTime = Date.now();
    touchStartDist = 0;

    trackpad.classList.add("active");
    trackpadDot.style.display = "block";
    updateTrackpadDotPos(clientX, clientY);

    vibrate(15);
    ws.sendLaserState(true);
  };

  const movePointer = (clientX, clientY) => {
    if (!isTouching) return;
    const dx = clientX - lastTouchX;
    const dy = clientY - lastTouchY;

    const dist = Math.hypot(dx, dy);
    touchStartDist += dist;
    lastTouchX = clientX;
    lastTouchY = clientY;

    updateTrackpadDotPos(clientX, clientY);

    // Dynamic power-law ballistics acceleration (high-RPS mouse physics)
    const accel = 1.0 + Math.min(dist * 0.12, 3.5);
    const dynamicSens = 3.6 * gyroSpeedMultiplier * accel;
    ws.sendLaserMove(dx, dy, true, dynamicSens);
  };

  const endPointer = () => {
    if (!isTouching) return;
    isTouching = false;
    trackpad.classList.remove("active");
    trackpadDot.style.display = "none";
    ws.sendLaserState(false);

    // Tap detection for click
    const duration = Date.now() - touchStartTime;
    if (duration < 220 && touchStartDist < 10) {
      vibrate(35);
      ws.sendAction("click", { button: "left" });
    }
  };

  // Touch Listeners
  trackpad.addEventListener("touchstart", (e) => {
    if (e.touches.length === 1) {
      startPointer(e.touches[0].clientX, e.touches[0].clientY);
    }
  }, { passive: false });

  trackpad.addEventListener("touchmove", (e) => {
    e.preventDefault();
    if (isTouching && e.touches.length === 1) {
      movePointer(e.touches[0].clientX, e.touches[0].clientY);
    }
  }, { passive: false });

  trackpad.addEventListener("touchend", endPointer);
  trackpad.addEventListener("touchcancel", endPointer);

  // Mouse drag support for trackpad (Desktop browser testing)
  trackpad.addEventListener("mousedown", (e) => {
    isPointerActive = true;
    startPointer(e.clientX, e.clientY);
  });

  window.addEventListener("mousemove", (e) => {
    if (isPointerActive) {
      movePointer(e.clientX, e.clientY);
    }
  });

  window.addEventListener("mouseup", () => {
    if (isPointerActive) {
      isPointerActive = false;
      endPointer();
    }
  });

  // Gyroscope / Air-Mouse Mode
  function handleGyroDelta(dX, dY) {
    if (!isGyroActive) return;

    // Filter micro-tremors with fine deadzone
    const deadzone = 0.05;
    const absX = Math.abs(dX);
    const absY = Math.abs(dY);

    if (absX > deadzone || absY > deadzone) {
      // Dynamic velocity acceleration (ballistics power-law like high-RPS mouse)
      const speed = Math.hypot(dX, dY);
      const accel = 1.0 + Math.min(speed * 0.75, 4.0);
      const dynamicGain = 20.0 * gyroSpeedMultiplier * accel;

      const moveX = absX > deadzone ? dX * dynamicGain : 0;
      const moveY = absY > deadzone ? dY * dynamicGain : 0;

      ws.sendLaserMove(moveX, moveY, true, 1.0);
    }
  }

  let lastGyroYaw = null;
  let lastGyroPitch = null;

  function handleDeviceOrientation(e) {
    if (!isGyroActive) return;
    // In phone portrait pointing forward:
    // alpha = compass heading / yaw (0 to 360)
    // beta = pitch (-180 to 180)
    const yaw = typeof e.alpha !== "undefined" && e.alpha !== null ? e.alpha : (typeof e.yaw !== "undefined" ? e.yaw : null);
    const pitch = typeof e.beta !== "undefined" && e.beta !== null ? e.beta : (typeof e.pitch !== "undefined" ? e.pitch : null);
    if (yaw === null || pitch === null) return;

    if (lastGyroYaw !== null && lastGyroPitch !== null) {
      let dYaw = yaw - lastGyroYaw;
      let dPitch = pitch - lastGyroPitch;

      // Compass boundary wrapping (0 - 360)
      if (dYaw > 180) dYaw -= 360;
      if (dYaw < -180) dYaw += 360;

      // Turning phone right decreases alpha in browser -> negate for positive screen X
      handleGyroDelta(-dYaw, dPitch);
    }

    lastGyroYaw = yaw;
    lastGyroPitch = pitch;
  }

  // Native Android Bridge hooks
  window.onNativeOrientation = (yaw, pitch) => {
    handleDeviceOrientation({ alpha: yaw, beta: pitch });
  };

  window.onNativeGyroDelta = (dX, dY) => {
    handleGyroDelta(dX, dY);
  };

  if (gyroToggle) {
    gyroToggle.addEventListener("click", async () => {
      if (!isGyroActive) {
        // 1. Android Native Sensors Bridge if available
        if (window.AndroidSensors && typeof window.AndroidSensors.start === "function") {
          window.AndroidSensors.start();
        }

        // 2. Request iOS/Safari permission if needed
        if (typeof DeviceOrientationEvent !== "undefined" && typeof DeviceOrientationEvent.requestPermission === "function") {
          try {
            const perm = await DeviceOrientationEvent.requestPermission();
            if (perm !== "granted") {
              alert("Izin sensor giroskop ditolak.");
              return;
            }
          } catch (e) {
            console.error("Gyro permission error:", e);
          }
        }

        // 3. Web DeviceOrientation listener
        window.addEventListener("deviceorientation", handleDeviceOrientation);
        isGyroActive = true;
        gyroToggle.classList.add("active");
        gyroToggle.textContent = "🛑 Matikan Gyro";
        ws.sendLaserState(true);
        vibrate(40);
      } else {
        if (window.AndroidSensors && typeof window.AndroidSensors.stop === "function") {
          window.AndroidSensors.stop();
        }
        window.removeEventListener("deviceorientation", handleDeviceOrientation);
        isGyroActive = false;
        gyroToggle.classList.remove("active");
        gyroToggle.textContent = "🎯 Air-Mouse (Gyro)";
        lastGyroYaw = null;
        lastGyroPitch = null;
        ws.sendLaserState(false);
        vibrate(20);
      }
    });
  }

  // Presentation Timer / Stopwatch
  const formatTime = (totalSeconds) => {
    const m = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
    const s = (totalSeconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  btnTimerToggle.addEventListener("click", () => {
    vibrate(20);
    if (!isTimerRunning) {
      isTimerRunning = true;
      btnTimerToggle.innerHTML = "⏸";
      timerInterval = setInterval(() => {
        timerSeconds++;
        timerDisplay.textContent = formatTime(timerSeconds);
        // Highlight when 20, 30, or 45 mins passed
        if (timerSeconds === 1200 || timerSeconds === 1800) {
          vibrate([100, 100, 100]);
        }
      }, 1000);
    } else {
      isTimerRunning = false;
      btnTimerToggle.innerHTML = "▶";
      clearInterval(timerInterval);
    }
  });

  btnTimerReset.addEventListener("click", () => {
    vibrate(20);
    isTimerRunning = false;
    clearInterval(timerInterval);
    btnTimerToggle.innerHTML = "▶";
    timerSeconds = 0;
    timerDisplay.textContent = "00:00";
  });
});
