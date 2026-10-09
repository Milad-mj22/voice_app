/**
 * Voice Assistant — WebSocket + UI مودال
 */
(function() {
  console.log("[voice.js] loaded");

  const modal = document.getElementById("voiceModal");
  const btn = document.getElementById("voiceRecordBtn");
  const statusEl = document.getElementById("voiceStatus");
  const logEl = document.getElementById("voiceLog");

  let ws = null;
  let recorder = null;
  let reconnectTimer = null;

  // ---------- WebSocket ----------
  function connectWS() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${location.host}/ws/voice/`;
    console.log("[voice.js] connecting to", url);
    ws = new WebSocket(url);
    window.ws = ws;

    ws.onopen = () => {
      console.log("[voice.js] WS open");
      setStatus("آماده — دکمه رو نگه دار و صحبت کن");
    };
    ws.onclose = (e) => {
      console.log("[voice.js] WS closed:", e.code, e.reason);
      if (e.code === 4001) setStatus("لطفاً اول وارد شوید.", "error");
      else if (e.code === 4002) setStatus("کسب‌وکار پیدا نشد.", "error");
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWS, 3000);
    };
    ws.onerror = (e) => console.log("[voice.js] WS error", e);
    ws.onmessage = (e) => {
      let m; try { m = JSON.parse(e.data); } catch { return; }
      console.log("[voice.js] ←", m.type, m);
      handleMessage(m);
    };
  }

  function handleMessage(m) {
    switch (m.type) {
      case "ready":
        setStatus("آماده — دکمه رو نگه دار و صحبت کن");
        break;
      case "recording":
        setStatus("🔴 در حال ضبط...", "ok");
        break;
      case "transcript":
        addLine("user", "🗣 " + m.text);
        setStatus("⏳ در حال پردازش...");
        break;
      case "action":
        addLine("action", "⚙️ " + formatAction(m));
        break;
      case "reply_text":
        addLine("reply", "💬 " + m.text);
        setStatus("✅ انجام شد", "ok");
        break;
      case "reply_audio":
        playAudio(m.data);
        break;
      case "error":
        addLine("error", "❌ " + m.message);
        setStatus(m.message, "error");
        break;
    }
  }

  function formatAction(m) {
    const r = m.result || {};
    if (r.ok === false) return (r.error || "خطا در عملیات");
    return (r.message || m.name);
  }

  function playAudio(b64) {
    try {
      const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
      const blob = new Blob([bytes], { type: "audio/mpeg" });
      new Audio(URL.createObjectURL(blob)).play();
    } catch (e) { console.error("[voice.js] play error", e); }
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

  function setStatus(text, type = "") {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.className = "voice-status " + type;
  }

  // ---------- ضبط ----------
  async function startRecording() {
    console.log("[voice.js] startRecording called");
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setStatus("اتصال برقرار نیست. صبر کن...", "error");
      return;
    }
    if (recorder && recorder.isRecording()) return;

    if (typeof VoiceRecorder === "undefined") {
      setStatus("ماژول ضبط بارگذاری نشده.", "error");
      return;
    }

    recorder = new VoiceRecorder(
      (b64) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "audio", data: b64 }));
        }
      },
      () => {
        btn?.classList.add("recording");
        ws.send(JSON.stringify({ type: "start" }));
        console.log("[voice.js] recording started");
      },
      () => {
        btn?.classList.remove("recording");
        ws.send(JSON.stringify({ type: "stop" }));
        console.log("[voice.js] recording stopped");
      }
    );

    try {
      await recorder.start();
    } catch (e) {
      console.error("[voice.js] start error", e);
      setStatus(e.message, "error");
    }
  }

  function stopRecording() {
    if (recorder) recorder.stop();
  }

  // ---------- دکمه ضبط داخل مودال ----------
  if (btn) {
    btn.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      startRecording();
    });
    btn.addEventListener("pointerup", (e) => {
      e.preventDefault();
      stopRecording();
    });
    btn.addEventListener("pointerleave", () => stopRecording());
    btn.addEventListener("contextmenu", (e) => e.preventDefault());
    console.log("[voice.js] record button attached");
  }

  // ---------- FAB در Bottom Nav ----------
  const fab = document.querySelector(".bnav-fab");
  if (fab) {
    fab.addEventListener("click", () => window.openVoice());
    console.log("[voice.js] FAB attached to .bnav-fab");
  } else {
    console.warn("[voice.js] .bnav-fab not found");
  }

  // ---------- کلیک روی overlay ----------
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) window.closeVoice();
    });
  }

  // ---------- API عمومی ----------
  window.openVoice = function() {
    console.log("[voice.js] openVoice");
    if (modal) modal.classList.add("show");
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      connectWS();
    }
  };

  window.closeVoice = function() {
    console.log("[voice.js] closeVoice");
    if (modal) modal.classList.remove("show");
    if (recorder && recorder.isRecording()) recorder.stop();
  };

  // ---------- شروع ----------
  connectWS();
})();