/**
 * Voice Assistant — نسخه HTTP با ویس + متن
 */
(function() {
  console.log("[voice.js] loaded (voice + text mode)");

  const modal = document.getElementById("voiceModal");
  const btn = document.getElementById("voiceRecordBtn");
  const statusEl = document.getElementById("voiceStatus");
  const logEl = document.getElementById("voiceLog");

  // پلیر
  const player = document.getElementById("voicePlayer");
  const playBtn = document.getElementById("voicePlayBtn");
  const muteBtn = document.getElementById("voiceMuteBtn");
  const progressBar = document.getElementById("voicePlayerProgress");

  // باکس متن
  const textInput = document.getElementById("voiceTextInput");
  const textSendBtn = document.getElementById("voiceTextSendBtn");

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

  function setBusy(busy) {
    isBusy = busy;
    if (textSendBtn) textSendBtn.disabled = busy;
    if (btn) btn.disabled = busy;
  }

  // ═══════════ پخش صدا ═══════════
  function loadAudio(b64) {
    if (!b64) return;

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

    if (player) player.style.display = "flex";
    updatePlayIcon();

    currentAudio.ontimeupdate = () => {
      if (!currentAudio.duration) return;
      const pct = (currentAudio.currentTime / currentAudio.duration) * 100;
      if (progressBar) progressBar.style.width = pct + "%";
    };

    currentAudio.onended = () => {
      updatePlayIcon();
      if (progressBar) progressBar.style.width = "0%";
    };

    currentAudio.play().catch(e => {
      console.warn("[voice.js] autoplay blocked:", e);
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
    if (currentAudio.paused) currentAudio.play();
    else currentAudio.pause();
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

  // ═══════════ ضبط صدا ═══════════
  async function toggleRecording() {
    if (isBusy) return;

    if (isRecording) {
      await stopRecording();
      return;
    }

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

    setBusy(true);
    await sendAudioToServer(result.blob, result.extension);
    setBusy(false);
  }

  // ═══════════ ارسال صدا ═══════════
  async function sendAudioToServer(blob, extension) {
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

      await handleResponse(res);

    } catch (e) {
      console.error("[voice.js] fetch error", e);
      setStatus("خطا در ارتباط با سرور", "error");
      addLine("error", "❌ " + e.message);
    }
  }

  // ═══════════ ارسال متن ═══════════
  async function sendTextToServer() {
    if (isBusy) return;

    const text = (textInput?.value || "").trim();
    if (!text) {
      setStatus("متن خالیه. یه چیزی بنویس.", "error");
      textInput?.focus();
      return;
    }

    // نمایش پیام کاربر
    addLine("user", "🗣 " + text);
    if (textInput) textInput.value = "";

    setBusy(true);
    setStatus("⏳ در حال پردازش…");

    const csrf = getCSRFToken();

    try {
      const res = await fetch("/api/voice/text/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify({ text }),
      });

      await handleResponse(res);

    } catch (e) {
      console.error("[voice.js] text fetch error", e);
      setStatus("خطا در ارتباط با سرور", "error");
      addLine("error", "❌ " + e.message);
    } finally {
      setBusy(false);
    }
  }

  // ═══════════ پردازش پاسخ سرور ═══════════
  async function handleResponse(res) {
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

    // اگه از صدا اومده بود، متن transcript رو نشون بده
    if (data.transcript && data.source === "voice") {
      addLine("user", "🗣 " + data.transcript);
    }

    if (data.actions && data.actions.length) {
      data.actions.forEach(a => addLine("action", "⚙️ " + formatAction(a)));
    }

    if (data.reply) addLine("reply", "💬 " + data.reply);

    if (data.audio) loadAudio(data.audio);

    setStatus("✅ می‌تونی دوباره بپرسی", "ok");
  }

  // ═══════════ رویدادها ═══════════
  if (btn) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      toggleRecording();
    });
  }

  if (playBtn) playBtn.addEventListener("click", togglePlay);
  if (muteBtn) muteBtn.addEventListener("click", toggleMute);

  if (textSendBtn) {
    textSendBtn.addEventListener("click", (e) => {
      e.preventDefault();
      sendTextToServer();
    });
  }

  if (textInput) {
    // Enter = ارسال (Shift+Enter = خط جدید)
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendTextToServer();
      }
    });
  }

  // FAB در Bottom Nav
  const fab = document.querySelector(".bnav-fab");
  if (fab) {
    fab.addEventListener("click", () => window.openVoice());
  }

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) window.closeVoice();
    });
  }

  // ═══════════ API عمومی ═══════════
  window.openVoice = function() {
    if (modal) modal.classList.add("show");
    setStatus("دکمه رو بزن و حرف بزن، یا متن بنویس");
    setTimeout(() => textInput?.focus(), 300);
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