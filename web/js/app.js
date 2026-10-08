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
  trackpad.addEventListener("touchstart", (e) => {
    requestWakeLock();
    if (e.touches.length === 1) {
      isTouching = true;
      const t = e.touches[0];
      lastTouchX = t.clientX;
      lastTouchY = t.clientY;
      touchStartTime = Date.now();
      touchStartDist = 0;

      trackpad.classList.add("active");
      trackpadDot.style.display = "block";
      updateTrackpadDot(t);

      vibrate(15);
      ws.sendLaserState(true);
    }
  }, { passive: false });

  trackpad.addEventListener("touchmove", (e) => {
    e.preventDefault(); // Prevent scroll/pull-to-refresh
    if (!isTouching || e.touches.length !== 1) return;

    const t = e.touches[0];
    const dx = t.clientX - lastTouchX;
    const dy = t.clientY - lastTouchY;

    touchStartDist += Math.hypot(dx, dy);
    lastTouchX = t.clientX;
    lastTouchY = t.clientY;

    updateTrackpadDot(t);
    ws.sendLaserMove(dx, dy, true, sensitivity);
  }, { passive: false });

  const endTouch = () => {
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

  trackpad.addEventListener("touchend", endTouch);
  trackpad.addEventListener("touchcancel", endTouch);

  function updateTrackpadDot(touch) {
    const rect = trackpad.getBoundingClientRect();
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;
    trackpadDot.style.left = `${x}px`;
    trackpadDot.style.top = `${y}px`;
  }



  // Gyroscope / Air-Mouse Mode
  if (gyroToggle) {
    gyroToggle.addEventListener("click", async () => {
      if (!isGyroActive) {
        // Request iOS/Safari permission if needed
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

        window.addEventListener("deviceorientation", handleDeviceOrientation);
        isGyroActive = true;
        gyroToggle.classList.add("active");
        gyroToggle.textContent = "🛑 Matikan Gyro";
        ws.sendLaserState(true);
        vibrate(40);
      } else {
        window.removeEventListener("deviceorientation", handleDeviceOrientation);
        isGyroActive = false;
        gyroToggle.classList.remove("active");
        gyroToggle.textContent = "🎯 Air-Mouse (Gyro)";
        lastGyroBeta = null;
        lastGyroGamma = null;
        ws.sendLaserState(false);
        vibrate(20);
      }
    });
  }

  function handleDeviceOrientation(e) {
    if (!isGyroActive) return;
    const beta = e.beta;   // Pitch (-180 to 180)
    const gamma = e.gamma; // Roll (-90 to 90)

    if (lastGyroBeta !== null && lastGyroGamma !== null) {
      let dGamma = gamma - lastGyroGamma;
      let dBeta = beta - lastGyroBeta;

      // Handle roll boundary wrapping
      if (dGamma > 180) dGamma -= 360;
      if (dGamma < -180) dGamma += 360;

      // Apply deadzone to avoid sensor micro-jitter
      const deadzone = 0.15;
      const moveX = Math.abs(dGamma) > deadzone ? dGamma * 8.0 : 0;
      const moveY = Math.abs(dBeta) > deadzone ? dBeta * 8.0 : 0;

      if (moveX !== 0 || moveY !== 0) {
        ws.sendLaserMove(moveX, moveY, true, 1.0);
      }
    }

    lastGyroBeta = beta;
    lastGyroGamma = gamma;
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
