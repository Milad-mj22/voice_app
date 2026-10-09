/**
 * تنظیمات — آپلود لوگو + پیش‌نمایش
 */
(function() {
  const input = document.getElementById("logoInput");
  const preview = document.getElementById("logoPreview");
  const placeholder = document.getElementById("logoPlaceholder");

  if (!input) return;

  input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      alert("حجم لوگو باید کمتر از ۲ مگابایت باشد.");
      input.value = "";
      return;
    }

    // پیش‌نمایش فوری
    const reader = new FileReader();
    reader.onload = (ev) => {
      if (preview) {
        preview.src = ev.target.result;
        preview.style.display = "block";
      }
      if (placeholder) placeholder.style.display = "none";
    };
    reader.readAsDataURL(file);

    // آپلود به سرور
    const fd = new FormData();
    fd.append("logo", file);
    fd.append("csrfmiddlewaretoken", window.CSRF_TOKEN);

    fetch("/accounts/api/upload-logo/", {
      method: "POST",
      body: fd,
      credentials: "same-origin",
    })
      .then(r => r.json())
      .then(d => {
        if (d.ok) {
          console.log("[settings] لوگو آپلود شد");
        } else {
          alert(d.error || "خطا در آپلود");
        }
      })
      .catch(() => alert("خطا در آپلود"));
  });
})();