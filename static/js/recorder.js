/**
 * VoiceRecorder — ضبط صدا با پشتیبانی iOS
 */
class VoiceRecorder {
  constructor() {
    this.recorder = null;
    this.stream = null;
    this.chunks = [];
    this.mimeType = "";
    this.extension = "webm";
  }

  // انتخاب بهترین فرمت ممکن بر اساس مرورگر
  static pickMimeType() {
    const candidates = [
      { mime: "audio/webm;codecs=opus", ext: "webm" },  // کروم/اندروید/فایرفاکس
      { mime: "audio/webm", ext: "webm" },
      { mime: "audio/mp4;codecs=mp4a.40.2", ext: "m4a" }, // iOS Safari
      { mime: "audio/mp4", ext: "m4a" },
      { mime: "audio/mpeg", ext: "mp3" },
      { mime: "audio/ogg;codecs=opus", ext: "ogg" },
      { mime: "audio/wav", ext: "wav" },
    ];

    if (typeof MediaRecorder === "undefined") {
      return { mime: "", ext: "webm" };
    }

    for (const c of candidates) {
      if (MediaRecorder.isTypeSupported(c.mime)) {
        return { mime: c.mime, ext: c.ext };
      }
    }

    return { mime: "", ext: "webm" };
  }

  async start() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("مرورگر شما از ضبط صدا پشتیبانی نمی‌کند.");
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
    } catch (err) {
      if (err.name === "NotAllowedError") {
        throw new Error("دسترسی به میکروفن رد شد.");
      }
      if (err.name === "NotFoundError") {
        throw new Error("میکروفنی پیدا نشد.");
      }
      throw new Error("خطا در دسترسی به میکروفن.");
    }

    const picked = VoiceRecorder.pickMimeType();
    this.mimeType = picked.mime;
    this.extension = picked.ext;

    console.log("[recorder] using:", this.mimeType || "(default)", "ext:", this.extension);

    const options = this.mimeType ? { mimeType: this.mimeType } : {};
    this.recorder = new MediaRecorder(this.stream, options);
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
        // بلاب با mimeType درست
        const mimeForBlob = this.mimeType || "audio/webm";
        const blob = new Blob(this.chunks, { type: mimeForBlob });
        this.chunks = [];
        if (this.stream) {
          this.stream.getTracks().forEach(t => t.stop());
          this.stream = null;
        }
        resolve({
          blob,
          extension: this.extension,
          mimeType: mimeForBlob,
        });
      };

      this.recorder.stop();
    });
  }

  isRecording() {
    return this.recorder && this.recorder.state === "recording";
  }
}