/**
 * مرداس — منطق اصلی
 */

// ═══════════════ Drawer ═══════════════
window.openDrawer = function() {
  document.getElementById("drawer")?.classList.add("show");
  document.getElementById("drawerOverlay")?.classList.add("show");
  document.body.style.overflow = "hidden";
};

window.closeDrawer = function() {
  document.getElementById("drawer")?.classList.remove("show");
  document.getElementById("drawerOverlay")?.classList.remove("show");
  document.body.style.overflow = "";
};

// ═══════════════ Search ═══════════════
window.focusSearch = function() {
  const bar = document.getElementById("searchBar");
  bar?.classList.add("show");
  setTimeout(() => document.getElementById("search")?.focus(), 100);
};

window.closeSearch = function() {
  document.getElementById("searchBar")?.classList.remove("show");
  const res = document.getElementById("searchResults");
  if (res) res.innerHTML = "";
  const input = document.getElementById("search");
  if (input) input.value = "";
};

// ═══════════════ CRUD (بدون تغییر خیلی) ═══════════════
const TYPES = {
  customer: "مشتری", project: "پروژه",
  opportunity: "فرصت فروش", task: "پیگیری",
  supplier: "تأمین‌کننده", colleague: "همکار",
  competitor: "رقیب", finance: "مالی", strategy: "استراتژی",
};

let currentType = "customer";
let editingId = null;

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": window.CSRF_TOKEN || "",
    },
    credentials: "same-origin",
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

window.openType = async function(type) {
  closeDrawer();
  currentType = type;
  // نمایش صفحه‌ی type
  const main = document.querySelector(".app-main");
  if (!main) return;
  main.innerHTML = `
    <div class="section-head">
      <h2>${TYPES[type] || type}</h2>
      <a href="#" onclick="newRecord('${type}'); return false;">
        <i class="ri-add-line"></i> افزودن
      </a>
    </div>
    <div id="typeList">
      <div class="empty-state">
        <i class="ri-loader-4-line"></i>
        <p>در حال بارگذاری...</p>
      </div>
    </div>
  `;
  try {
    const items = await api(`/api/${type}/`);
    renderTypeList(items);
  } catch (e) {
    document.getElementById("typeList").innerHTML = `
      <div class="empty-state">
        <i class="ri-error-warning-line"></i>
        <p>خطا: ${e.message}</p>
      </div>
    `;
  }
};

function renderTypeList(items) {
  const wrap = document.getElementById("typeList");
  if (!items.length) {
    wrap.innerHTML = `
      <div class="empty-state">
        <i class="ri-inbox-line"></i>
        <p>هنوز موردی ثبت نشده</p>
        <button class="btn btn-primary" onclick="newRecord('${currentType}')">
          <i class="ri-add-line"></i> افزودن اولین مورد
        </button>
      </div>
    `;
    return;
  }
  wrap.innerHTML = items.map(r => `
    <div class="card" style="margin-bottom:10px">
      <div style="display:flex;align-items:flex-start;gap:10px">
        <div style="flex:1;min-width:0">
          <b style="font-size:14px;display:block;margin-bottom:4px">${esc(r.title)}</b>
          <small style="color:var(--text-3);font-size:12px">
            ${r.company ? esc(r.company) + " · " : ""}${r.status || ""}
          </small>
          ${r.notes ? `<p style="margin:8px 0 0;font-size:13px;color:var(--text-2)">${esc(r.notes)}</p>` : ""}
        </div>
      </div>
      <div style="display:flex;gap:6px;margin-top:10px">
        <button class="btn btn-ghost" style="flex:1;padding:8px" onclick="editRecord(${r.id})">
          <i class="ri-edit-line"></i> ویرایش
        </button>
        <button class="btn btn-danger" style="flex:1;padding:8px" onclick="deleteRecord(${r.id})">
          <i class="ri-delete-bin-line"></i> حذف
        </button>
      </div>
    </div>
  `).join("");
}

window.newRecord = function(type) {
  if (type) currentType = type;
  editingId = null;
  showEditor("ثبت " + (TYPES[currentType] || ""), {});
};

window.editRecord = async function(id) {
  try {
    const r = await api(`/api/${currentType}/${id}/`);
    editingId = id;
    showEditor("ویرایش " + (TYPES[currentType] || ""), r);
  } catch (e) {
    alert("خطا: " + e.message);
  }
};

function showEditor(title, data) {
  const main = document.querySelector(".app-main");
  main.innerHTML = `
    <div class="section-head">
      <h2>${title}</h2>
      <a href="#" onclick="location.reload(); return false;">
        <i class="ri-arrow-right-line"></i> بازگشت
      </a>
    </div>

    <div class="card">
      <div class="form-group">
        <label class="form-label">عنوان / نام *</label>
        <input id="fTitle" class="form-input" value="${esc(data.title || "")}">
      </div>

      <div class="form-group">
        <label class="form-label">شماره تماس</label>
        <input id="fPhone" class="form-input" dir="ltr" value="${esc(data.phone || "")}">
      </div>

      <div class="form-group">
        <label class="form-label">شرکت / پروژه</label>
        <input id="fCompany" class="form-input" value="${esc(data.company || "")}">
      </div>

      <div class="form-group">
        <label class="form-label">وضعیت</label>
        <select id="fStatus" class="form-input">
          <option ${data.status === "جدید" ? "selected" : ""}>جدید</option>
          <option ${data.status === "در حال پیگیری" ? "selected" : ""}>در حال پیگیری</option>
          <option ${data.status === "فعال" ? "selected" : ""}>فعال</option>
          <option ${data.status === "انجام شد" ? "selected" : ""}>انجام شد</option>
          <option ${data.status === "بایگانی" ? "selected" : ""}>بایگانی</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">یادداشت</label>
        <textarea id="fNotes" class="form-input">${esc(data.notes || "")}</textarea>
      </div>

      <button class="btn btn-primary btn-block" onclick="saveRecord()">
        <i class="ri-save-line"></i> ذخیره
      </button>
    </div>
  `;
}

window.saveRecord = async function() {
  const title = document.getElementById("fTitle").value.trim();
  if (!title) { alert("عنوان الزامی است."); return; }

  const payload = {
    title,
    phone: document.getElementById("fPhone").value.trim(),
    company: document.getElementById("fCompany").value.trim(),
    status: document.getElementById("fStatus").value,
    notes: document.getElementById("fNotes").value.trim(),
  };

  try {
    if (editingId) {
      await api(`/api/${currentType}/${editingId}/`, {
        method: "PUT", body: JSON.stringify(payload),
      });
    } else {
      await api(`/api/${currentType}/`, {
        method: "POST", body: JSON.stringify(payload),
      });
    }
    location.reload();
  } catch (e) {
    alert("خطا: " + e.message);
  }
};

window.deleteRecord = async function(id) {
  if (!confirm("این مورد حذف شود؟")) return;
  try {
    await api(`/api/${currentType}/${id}/`, { method: "DELETE" });
    openType(currentType);
  } catch (e) {
    alert("خطا: " + e.message);
  }
};

// ═══════════════ Search (زنده) ═══════════════
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search");
  if (!searchInput) return;

  let timer;
  searchInput.addEventListener("input", () => {
    clearTimeout(timer);
    const q = searchInput.value.trim();
    const res = document.getElementById("searchResults");
    if (!q) { res.innerHTML = ""; return; }

    timer = setTimeout(async () => {
      res.innerHTML = '<div class="empty-state"><i class="ri-loader-4-line"></i></div>';
      try {
        const items = await api(`/api/search/?q=${encodeURIComponent(q)}`);
        if (!items.length) {
          res.innerHTML = '<div class="empty-state"><i class="ri-search-line"></i><p>نتیجه‌ای پیدا نشد</p></div>';
          return;
        }
        res.innerHTML = items.map(r => `
          <a href="#" class="search-result" onclick="closeSearch(); openType('${r.type}'); return false;">
            <b>${esc(r.title)}</b>
            <small>${esc(r.type_label)}${r.company ? " · " + esc(r.company) : ""}</small>
          </a>
        `).join("");
      } catch (e) {
        res.innerHTML = `<div class="empty-state"><p>خطا: ${e.message}</p></div>`;
      }
    }, 300);
  });
});

// ═══════════════ helpers ═══════════════
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, m => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[m]));
}

// پاک کردن body overflow وقتی drawer بسته شد
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeDrawer();
    closeSearch();
    window.closeVoice?.();
  }
});