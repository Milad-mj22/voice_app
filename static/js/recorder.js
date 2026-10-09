/**
 * VoiceRecorder — ضبط صدا و برگرداندن یک Blob کامل
 */
class VoiceRecorder {
  constructor() {
    this.recorder = null;
    this.stream = null;
    this.chunks = [];
  }

  async start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        }
      });
    } catch (err) {
      throw new Error("دسترسی به میکروفن رد شد.");
    }

    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";

    this.recorder = new MediaRecorder(this.stream, { mimeType: mime });
    this.chunks = [];

    this.recorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data);
    };

    this.recorder.start(250);
  }

  stop() {
    return new Promise((resolve) => {
      if (!this.recorder || this.recorder.state === "inactive") {
        resolve(null);
        return;
      }

      this.recorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: "audio/webm" });
        this.chunks = [];
        if (this.stream) {
          this.stream.getTracks().forEach(t => t.stop());
          this.stream = null;
        }
        resolve(blob);
      };

      this.recorder.stop();
    });
  }

  isRecording() {
    return this.recorder && this.recorder.state === "recording";
  }
}