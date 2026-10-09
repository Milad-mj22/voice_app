/**
 * Voice Assistant — نسخه HTTP (بدون WebSocket)
 * مناسب cPanel و هر هاست اشتراکی
 */
(function() {
  console.log("[voice.js] loaded (HTTP mode)");

  const modal = document.getElementById("voiceModal");
  const btn = document.getElementById("voiceRecordBtn");
  const statusEl = document.getElementById("voiceStatus");
  const logEl = document.getElementById("voiceLog");

  let recorder = null;
  let isBusy = false;

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

  function clearLog() {
    if (!logEl) return;
    logEl.innerHTML = `
      <div class="voice-line voice-line-empty">
        اینجا گفتگو نمایش داده می‌شه…
      </div>`;
  }

  function playAudio(b64) {
    if (!b64) return;
    try {
      const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
      const blob = new Blob([bytes], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play().catch(e => console.warn("پخش صدا:", e));
    } catch (e) {
      console.error("[voice.js] play error", e);
    }
  }

  function formatAction(action) {
    const r = action.result || {};
    if (r.ok === false) return r.error || "خطا در عملیات";
    return r.message || action.name;
  }

  // ═══════════ ضبط صدا ═══════════
  async function startRecording() {
    if (isBusy) return;

    if (typeof VoiceRecorder === "undefined") {
      setStatus("ماژول ضبط بارگذاری نشده.", "error");
      return;
    }

    if (recorder && recorder.isRecording()) return;

    recorder = new VoiceRecorder();
    try {
      await recorder.start();
      btn?.classList.add("recording");
      setStatus("🔴 در حال ضبط…", "ok");
    } catch (e) {
      console.error("[voice.js] start error", e);
      setStatus(e.message, "error");
    }
  }

  async function stopRecording() {
    if (!recorder || !recorder.isRecording()) return;
    if (isBusy) return;

    btn?.classList.remove("recording");
    setStatus("⏳ در حال ارسال…");

    const result = await recorder.stop();
    if (!result || !result.blob || result.blob.size === 0) {
      setStatus("صدایی ضبط نشد.", "error");
      return;
    }

    isBusy = true;
    await sendToServer(result.blob, result.extension, result.mimeType);
    isBusy = false;
  }

    isBusy = true;
    await sendToServer(blob);
    isBusy = false;
  }

  // ═══════════ ارسال به سرور ═══════════
  async function sendToServer(blob, extension, mimeType) {
    const fd = new FormData();
    const filename = `voice.${extension || "webm"}`;
    fd.append("audio", blob, filename);

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

      if (data.transcript) {
        addLine("user", "🗣 " + data.transcript);
      }

      if (data.actions && data.actions.length) {
        data.actions.forEach(a => {
          addLine("action", "⚙️ " + formatAction(a));
        });
      }

      if (data.reply) {
        addLine("reply", "💬 " + data.reply);
      }

      if (data.audio) {
        playAudio(data.audio);
      }

      setStatus("✅ انجام شد", "ok");

      setTimeout(() => {
        if (!isBusy) setStatus("دکمه رو نگه دار و صحبت کن");
      }, 2500);

    } catch (e) {
      console.error("[voice.js] fetch error", e);
      setStatus("خطا در ارتباط با سرور", "error");
      addLine("error", "❌ " + e.message);
    }
  }
  function getCSRFToken() {
    // اول از window.CSRF_TOKEN
    if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
    // بعد از کوکی
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }

  // ═══════════ رویدادها ═══════════
  if (btn) {
    btn.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      startRecording();
    });
    btn.addEventListener("pointerup", (e) => {
      e.preventDefault();
      stopRecording();
    });
    btn.addEventListener("pointerleave", () => {
      if (recorder && recorder.isRecording()) stopRecording();
    });
    btn.addEventListener("contextmenu", (e) => e.preventDefault());
    console.log("[voice.js] record button attached");
  }

  // FAB در Bottom Nav
  const fab = document.querySelector(".bnav-fab");
  if (fab) {
    fab.addEventListener("click", () => window.openVoice());
    console.log("[voice.js] FAB attached");
  }

  // کلیک روی overlay → بستن
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) window.closeVoice();
    });
  }

  // ═══════════ API عمومی ═══════════
  window.openVoice = function() {
    console.log("[voice.js] openVoice");
    if (modal) modal.classList.add("show");
    setStatus("دکمه رو نگه دار و صحبت کن");
  };

  window.closeVoice = function() {
    console.log("[voice.js] closeVoice");
    if (modal) modal.classList.remove("show");
    if (recorder && recorder.isRecording()) recorder.stop();
  };

  console.log("[voice.js] ready");
})();