/**
 * Voice Assistant — نسخه HTTP با یک کلیک
 */
(function() {
  console.log("[voice.js] loaded (HTTP mode, click-to-record)");

  const modal = document.getElementById("voiceModal");
  const btn = document.getElementById("voiceRecordBtn");
  const statusEl = document.getElementById("voiceStatus");
  const logEl = document.getElementById("voiceLog");

  // پلیر
  const player = document.getElementById("voicePlayer");
  const playBtn = document.getElementById("voicePlayBtn");
  const muteBtn = document.getElementById("voiceMuteBtn");
  const progressBar = document.getElementById("voicePlayerProgress");

  let recorder = null;
  let isBusy = false;
  let isRecording = false;

  let currentAudio = null;
  let isMuted = false;
  let currentAudioUrl = null;

  // ═══════════ ابزارها ═══════════
  function setStatus(text, type = "") {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.className = "voice-status " + type;
  }

  function addLine(type, text) {
    if (!logEl) return;
    const empty = logEl.querySelector(".voice-line-empty");
    if (empty) empty.remove();
    const div = document.createElement("div");
    div.className = `voice-line voice-line-${type}`;
    div.textContent = text;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function getCSRFToken() {
    if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }

  function formatAction(action) {
    const r = action.result || {};
    if (r.ok === false) return r.error || "خطا در عملیات";
    return r.message || action.name;
  }

  // ═══════════ پخش صدا ═══════════
  function loadAudio(b64) {
    if (!b64) return;

    // آزادسازی قبلی
    if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl);

    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const blob = new Blob([bytes], { type: "audio/mpeg" });
    currentAudioUrl = URL.createObjectURL(blob);

    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    currentAudio = new Audio(currentAudioUrl);
    currentAudio.muted = isMuted;

    // نمایش پلیر
    if (player) player.style.display = "flex";
    updatePlayIcon();

    // آپدیت پروگرس
    currentAudio.ontimeupdate = () => {
      if (!currentAudio.duration) return;
      const pct = (currentAudio.currentTime / currentAudio.duration) * 100;
      if (progressBar) progressBar.style.width = pct + "%";
    };

    currentAudio.onended = () => {
      updatePlayIcon();
      if (progressBar) progressBar.style.width = "0%";
    };

    // پخش خودکار
    currentAudio.play().catch(e => {
      console.warn("[voice.js] autoplay blocked:", e);
      setStatus("برای پخش صدا دکمه ▶ رو بزن");
    });
  }

  function updatePlayIcon() {
    if (!playBtn) return;
    if (currentAudio && !currentAudio.paused) {
      playBtn.innerHTML = '<i class="ri-pause-fill"></i>';
    } else {
      playBtn.innerHTML = '<i class="ri-play-fill"></i>';
    }
  }

  function togglePlay() {
    if (!currentAudio) return;
    if (currentAudio.paused) {
      currentAudio.play();
    } else {
      currentAudio.pause();
    }
    setTimeout(updatePlayIcon, 50);
  }

  function toggleMute() {
    isMuted = !isMuted;
    if (currentAudio) currentAudio.muted = isMuted;
    if (muteBtn) {
      muteBtn.classList.toggle("muted", isMuted);
      muteBtn.innerHTML = isMuted
        ? '<i class="ri-volume-mute-line"></i>'
        : '<i class="ri-volume-up-line"></i>';
    }
  }

  // ═══════════ ضبط صدا (یک کلیک شروع/توقف) ═══════════
  async function toggleRecording() {
    if (isBusy) return;

    // اگه در حال ضبطه → توقف
    if (isRecording) {
      await stopRecording();
      return;
    }

    // اگه تازه می‌خواد شروع کنه
    if (typeof VoiceRecorder === "undefined") {
      setStatus("ماژول ضبط بارگذاری نشده.", "error");
      return;
    }

    recorder = new VoiceRecorder();
    try {
      await recorder.start();
      isRecording = true;
      btn?.classList.add("recording");
      btn.innerHTML = '<i class="ri-stop-fill"></i>';
      setStatus("🔴 در حال ضبط… دوباره بزن تا بفرسته");
    } catch (e) {
      console.error("[voice.js] start error", e);
      setStatus(e.message, "error");
    }
  }

  async function stopRecording() {
    if (!recorder || !isRecording) return;

    isRecording = false;
    btn?.classList.remove("recording");
    btn.innerHTML = '<i class="ri-mic-line"></i>';
    setStatus("⏳ در حال پردازش…");

    const result = await recorder.stop();
    if (!result || !result.blob || result.blob.size === 0) {
      setStatus("صدایی ضبط نشد.", "error");
      return;
    }

    isBusy = true;
    await sendToServer(result.blob, result.extension);
    isBusy = false;
  }

  // ═══════════ ارسال به سرور ═══════════
  async function sendToServer(blob, extension) {
    const fd = new FormData();
    fd.append("audio", blob, `voice.${extension || "webm"}`);

    const csrf = getCSRFToken();

    try {
      const res = await fetch("/api/voice/", {
        method: "POST",
        body: fd,
        credentials: "same-origin",
        headers: csrf ? { "X-CSRFToken": csrf } : {},
      });

      if (!res.ok) {
        const txt = await res.text();
        console.error("[voice.js] server error:", res.status, txt);
        setStatus("خطا در سرور: " + res.status, "error");
        addLine("error", "❌ خطای سرور " + res.status);
        return;
      }

      const data = await res.json();

      if (!data.ok) {
        setStatus(data.error || "خطا در پردازش", "error");
        addLine("error", "❌ " + (data.error || "خطا"));
        return;
      }

      if (data.transcript) addLine("user", "🗣 " + data.transcript);

      if (data.actions && data.actions.length) {
        data.actions.forEach(a => addLine("action", "⚙️ " + formatAction(a)));
      }

      if (data.reply) addLine("reply", "💬 " + data.reply);

      if (data.audio) loadAudio(data.audio);

      setStatus("✅ می‌تونی دوباره بزنی و حرف بزنی", "ok");

    } catch (e) {
      console.error("[voice.js] fetch error", e);
      setStatus("خطا در ارتباط با سرور", "error");
      addLine("error", "❌ " + e.message);
    }
  }

  // ═══════════ رویدادها ═══════════
  if (btn) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      toggleRecording();
    });
    console.log("[voice.js] record button attached (click mode)");
  }

  if (playBtn) {
    playBtn.addEventListener("click", togglePlay);
  }
  if (muteBtn) {
    muteBtn.addEventListener("click", toggleMute);
  }

  // FAB در Bottom Nav
  const fab = document.querySelector(".bnav-fab");
  if (fab) {
    fab.addEventListener("click", () => window.openVoice());
  }

  // کلیک روی overlay → بستن
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) window.closeVoice();
    });
  }

  // ═══════════ API عمومی ═══════════
  window.openVoice = function() {
    if (modal) modal.classList.add("show");
    setStatus("دکمه رو بزن و حرف بزن");
  };

  window.closeVoice = function() {
    if (modal) modal.classList.remove("show");
    if (recorder && isRecording) {
      recorder.stop();
      isRecording = false;
    }
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
  };

  console.log("[voice.js] ready");
})();