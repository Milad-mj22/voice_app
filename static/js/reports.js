/**
 * گزارش‌ها — Chart.js
 */
(function() {
  console.log("[reports.js] loaded");

  // رنگ‌ها از CSS
  const css = getComputedStyle(document.documentElement);
  const BRAND = css.getPropertyValue("--brand").trim() || "#2563eb";
  const PURPLE = css.getPropertyValue("--purple").trim() || "#8b5cf6";
  const GREEN = css.getPropertyValue("--green").trim() || "#10b981";
  const RED = css.getPropertyValue("--red").trim() || "#ef4444";
  const AMBER = css.getPropertyValue("--amber").trim() || "#f59e0b";
  const TEXT_3 = css.getPropertyValue("--text-3").trim() || "#64748b";
  const TEXT_4 = css.getPropertyValue("--text-4").trim() || "#94a3b8";
  const BORDER = css.getPropertyValue("--border").trim() || "#e5e9f2";

  // فرمت اعداد فارسی با کاما
  const faNum = (n) => Number(n || 0).toLocaleString("fa-IR");

  let charts = {};

  // ═══════════════ Bar Options ═══════════════
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
        labels: { font: { family: "Vazirmatn" } }
      },
      tooltip: {
        bodyFont: { family: "Vazirmatn" },
        titleFont: { family: "Vazirmatn" },
        rtl: true,
        textDirection: "rtl",
      }
    },
    scales: {
      x: {
        ticks: { font: { family: "Vazirmatn", size: 11 }, color: TEXT_3 },
        grid: { display: false },
      },
      y: {
        ticks: { font: { family: "Vazirmatn", size: 11 }, color: TEXT_3 },
        grid: { color: BORDER },
        beginAtZero: true,
      }
    }
  };

  // ═══════════════ ۱. KPI ═══════════════
  async function loadStats() {
    try {
      const res = await fetch("/api/stats/", { credentials: "same-origin" });
      const s = await res.json();
      setText("kpiCustomers", faNum(s.customers));
      setText("kpiProjects", faNum(s.projects));
      setText("kpiOpps", faNum(s.opportunities));
      setText("kpiTasks", faNum(s.tasks));
      setText("kpiIncome", faNum(s.income));
      setText("kpiExpense", faNum(s.expense));
    } catch (e) {
      console.warn("[reports] stats error", e);
    }
  }

  // ═══════════════ ۲. قیف فروش ═══════════════
  function renderPipeline(data) {
    const ctx = document.getElementById("chartPipeline");
    if (!ctx) return;

    if (charts.pipeline) charts.pipeline.destroy();

    const labels = data.map(p => p.stage);
    const values = data.map(p => p.count);

    charts.pipeline = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: (ctx) => {
            const chart = ctx.chart;
            const { ctx: c, chartArea } = chart;
            if (!chartArea) return BRAND;
            const g = c.createLinearGradient(chartArea.left, 0, chartArea.right, 0);
            g.addColorStop(0, PURPLE);
            g.addColorStop(1, BRAND);
            return g;
          },
          borderRadius: 8,
          barThickness: 18,
        }]
      },
      options: {
        ...baseOptions,
        indexAxis: "y",
        scales: {
          x: {
            ticks: { font: { family: "Vazirmatn", size: 11 }, color: TEXT_3, precision: 0 },
            grid: { color: BORDER },
            beginAtZero: true,
          },
          y: {
            ticks: { font: { family: "Vazirmatn", size: 11 }, color: TEXT_3 },
            grid: { display: false },
          }
        }
      }
    });
  }

  // ═══════════════ ۳. روند مالی ═══════════════
  function renderFinance(data) {
    const ctx = document.getElementById("chartFinance");
    if (!ctx) return;

    if (charts.finance) charts.finance.destroy();

    charts.finance = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.map(m => m.label),
        datasets: [
          {
            label: "درآمد",
            data: data.map(m => m.income),
            borderColor: GREEN,
            backgroundColor: "rgba(16,185,129,.08)",
            borderWidth: 2.5,
            tension: .4,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: GREEN,
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
          },
          {
            label: "هزینه",
            data: data.map(m => m.expense),
            borderColor: RED,
            backgroundColor: "rgba(239,68,68,.08)",
            borderWidth: 2.5,
            tension: .4,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: RED,
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
          }
        ]
      },
      options: {
        ...baseOptions,
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: {
              font: { family: "Vazirmatn", size: 12 },
              color: TEXT_3,
              usePointStyle: true,
              pointStyle: "circle",
            }
          },
          tooltip: {
            bodyFont: { family: "Vazirmatn" },
            titleFont: { family: "Vazirmatn" },
            rtl: true,
            callbacks: {
              label: (c) => `${c.dataset.label}: ${faNum(c.parsed.y)} تومان`
            }
          }
        },
        scales: {
          x: {
            ticks: { font: { family: "Vazirmatn", size: 11 }, color: TEXT_3 },
            grid: { display: false },
          },
          y: {
            ticks: {
              font: { family: "Vazirmatn", size: 11 },
              color: TEXT_3,
              callback: (v) => faNum(v),
            },
            grid: { color: BORDER },
            beginAtZero: true,
          }
        }
      }
    });
  }

  // ═══════════════ ۴. توزیع مشتری (Doughnut) ═══════════════
  function renderCustomers(data) {
    const ctx = document.getElementById("chartCustomers");
    if (!ctx) return;

    if (charts.customers) charts.customers.destroy();

    charts.customers = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.labels,
        datasets: [{
          data: data.values,
          backgroundColor: [
            BRAND, GREEN, AMBER, PURPLE, RED, "#06b6d4", "#ec4899",
          ],
          borderWidth: 0,
          hoverOffset: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              font: { family: "Vazirmatn", size: 12 },
              color: TEXT_3,
              usePointStyle: true,
              pointStyle: "circle",
              padding: 12,
            }
          },
          tooltip: {
            bodyFont: { family: "Vazirmatn" },
            titleFont: { family: "Vazirmatn" },
            rtl: true,
            callbacks: {
              label: (c) => `${c.label}: ${faNum(c.parsed)} نفر`
            }
          }
        }
      }
    });
  }

  // ═══════════════ ۵. فعالیت هفتگی ═══════════════
  function renderWeekly(data) {
    const ctx = document.getElementById("chartWeekly");
    if (!ctx) return;

    if (charts.weekly) charts.weekly.destroy();

    charts.weekly = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.map(d => d.label),
        datasets: [{
          data: data.map(d => d.customers),
          backgroundColor: BRAND,
          borderRadius: 8,
          barThickness: 24,
        }]
      },
      options: {
        ...baseOptions,
        plugins: {
          legend: { display: false },
          tooltip: {
            bodyFont: { family: "Vazirmatn" },
            rtl: true,
            callbacks: {
              label: (c) => `${faNum(c.parsed.y)} مشتری جدید`
            }
          }
        },
        scales: {
          x: {
            ticks: { font: { family: "Vazirmatn", size: 11 }, color: TEXT_3 },
            grid: { display: false },
          },
          y: {
            ticks: { font: { family: "Vazirmatn", size: 11 }, color: TEXT_3, precision: 0 },
            grid: { color: BORDER },
            beginAtZero: true,
          }
        }
      }
    });
  }

  // ═══════════════ ۶. مشتریان برتر ═══════════════
  function renderTopCustomers(items) {
    const wrap = document.getElementById("topCustomersWrap");
    if (!wrap) return;

    if (!items || !items.length) {
      wrap.innerHTML = `
        <div class="empty-state">
          <i class="ri-trophy-line"></i>
          <p>هنوز مشتری برتر ثبت نشده</p>
        </div>`;
      return;
    }

    wrap.innerHTML = `
      <table class="data-table">
        <thead>
          <tr><th>#</th><th>مشتری</th><th>مجموع</th></tr>
        </thead>
        <tbody>
          ${items.map((c, i) => `
            <tr>
              <td><span class="rank">${i + 1}</span></td>
              <td>${escapeHtml(c.title)}</td>
              <td><b>${faNum(c.total)}</b></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  // ═══════════════ ابزار ═══════════════
  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, m => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
    }[m]));
  }

  // ═══════════════ فیلتر بازه ═══════════════
  document.querySelectorAll("#filterChips .chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll("#filterChips .chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      loadAll();
    });
  });

  // ═══════════════ بارگذاری همه ═══════════════
  async function loadAll() {
    await loadStats();

    try {
      const [pipeline, monthly, weekly, topCustomers] = await Promise.all([
        fetch("/api/reports/pipeline/", { credentials: "same-origin" }).then(r => r.json()),
        fetch("/api/reports/monthly/", { credentials: "same-origin" }).then(r => r.json()),
        fetch("/api/reports/weekly/", { credentials: "same-origin" }).then(r => r.json()),
        fetch("/api/reports/top-customers/", { credentials: "same-origin" }).then(r => r.json()),
      ]);

      renderPipeline(pipeline);
      renderFinance(monthly);
      renderWeekly(weekly);
      renderTopCustomers(topCustomers);

      // توزیع مشتری بر اساس وضعیت (از داده‌های summary مشتق)
      const stats = await fetch("/api/stats/", { credentials: "same-origin" }).then(r => r.json());
      renderCustomers({
        labels: ["مشتری", "پروژه", "فرصت", "پیگیری"],
        values: [stats.customers, stats.projects, stats.opportunities, stats.tasks],
      });
    } catch (e) {
      console.error("[reports] load error", e);
    }
  }

  // شروع
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadAll);
  } else {
    loadAll();
  }
})();