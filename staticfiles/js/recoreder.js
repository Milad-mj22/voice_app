/**
 * VoiceRecorder — ضبط صدا با MediaRecorder و ارسال chunk به chunk
 */
class VoiceRecorder {
  constructor(onChunk, onStart, onStop) {
    this.onChunk = onChunk;
    this.onStart = onStart;
    this.onStop = onStop;
    this.recorder = null;
    this.stream = null;
  }

  async start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true }
      });
    } catch (err) {
      throw new Error("دسترسی به میکروفن رد شد.");
    }

    // انتخاب بهترین فرمت ممکن
    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";

    this.recorder = new MediaRecorder(this.stream, { mimeType: mime });

    this.recorder.ondataavailable = async (e) => {
      if (e.data.size === 0) return;
      const buf = await e.data.arrayBuffer();
      // تبدیل به base64
      const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
      this.onChunk(b64);
    };

    this.recorder.start(250); // هر ۲۵۰ میلی‌ثانیه
    if (this.onStart) this.onStart();
  }

  stop() {
    if (!this.recorder || this.recorder.state === "inactive") return;
    this.recorder.stop();
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.onStop) this.onStop();
  }

  isRecording() {
    return this.recorder && this.recorder.state === "recording";
  }
}