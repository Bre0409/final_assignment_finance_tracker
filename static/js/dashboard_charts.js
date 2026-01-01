(function () {
  function parseJsonScript(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
  }

  function sumArray(arr) {
    if (!arr || !arr.length) return 0;
    return arr.reduce((a, b) => a + (Number(b) || 0), 0);
  }

  if (typeof Chart === "undefined") {
    console.error("Chart.js not loaded. Check the Chart.js CDN in dashboard.html.");
    return;
  }

  const PALETTE = [
    "#3BA3FF",
    "#FF5F8A",
    "#FFAA3B",
    "#FFD35A",
    "#42D6C5",
    "#9B7CFF",
    "#7FE26B",
    "#FF6B6B",
  ];

  // ---- Trend charts ----
  const trendLabels = parseJsonScript("trend-labels");
  const trendSeries = parseJsonScript("trend-series");
  const trendBudgetLine = parseJsonScript("trend-budget-line");

  // Trend line with optional red budget limit line (high contrast for dark theme)
  const trendCanvas = document.getElementById("expenseTrendChart");
  if (trendCanvas && trendLabels && trendSeries) {
    const datasets = [
      {
        label: "Daily expenses",
        data: trendSeries,
        tension: 0.25,
        fill: false,
        borderColor: "#3BA3FF",
        borderWidth: 3,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: "#3BA3FF",
        pointBorderColor: "#0b0f16",
        pointBorderWidth: 2
      }
    ];

    if (trendBudgetLine && Array.isArray(trendBudgetLine)) {
      datasets.push({
        label: "Daily budget limit",
        data: trendBudgetLine,
        borderColor: "#FF4D4D",
        borderWidth: 3,
        pointRadius: 0,
        tension: 0,
        fill: false,
        borderDash: [6, 6]
      });
    }

    new Chart(trendCanvas, {
      type: "line",
      data: {
        labels: trendLabels,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            display: true,
            labels: { color: "rgba(255,255,255,0.85)" }
          }
        },
        scales: {
          x: {
            grid: { color: "rgba(255,255,255,0.06)" },
            ticks: { color: "rgba(255,255,255,0.65)" }
          },
          y: {
            beginAtZero: true,
            grid: { color: "rgba(255,255,255,0.06)" },
            ticks: { color: "rgba(255,255,255,0.65)" }
          }
        }
      }
    });
  }

  // Daily budget vs expenses bars (last 14 days)
  const dailyBarsCanvas = document.getElementById("dailyBudgetVsExpenseBars");
  if (dailyBarsCanvas && trendLabels && trendSeries) {
    const take = 14;
    const labelsSlice = trendLabels.slice(-take);
    const expenseSlice = trendSeries.slice(-take);

    let budgetSlice = null;
    if (trendBudgetLine && Array.isArray(trendBudgetLine)) {
      budgetSlice = trendBudgetLine.slice(-take);
    }

    const datasets = [];
    if (budgetSlice) datasets.push({ label: "Budget", data: budgetSlice });
    datasets.push({ label: "Expenses", data: expenseSlice });

    new Chart(dailyBarsCanvas, {
      type: "bar",
      data: { labels: labelsSlice, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, labels: { color: "rgba(255,255,255,0.85)" } }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: "rgba(255,255,255,0.65)" }
          },
          y: {
            beginAtZero: true,
            grid: { color: "rgba(255,255,255,0.06)" },
            ticks: { color: "rgba(255,255,255,0.65)" }
          }
        }
      }
    });
  }

  // ---- Doughnut chart with % labels drawn manually ----
  const pieLabels = parseJsonScript("spend-pie-labels");
  const pieSeries = parseJsonScript("spend-pie-series");
  const pieCanvas = document.getElementById("spendPieChart");

  const percentLabelsPlugin = {
    id: "percentLabels",
    afterDatasetsDraw(chart) {
      const dataset = chart.data.datasets[0];
      const meta = chart.getDatasetMeta(0);
      if (!meta || !meta.data || !dataset || !dataset.data) return;

      const total = dataset.data.reduce((a, b) => a + (Number(b) || 0), 0);
      if (!total) return;

      const ctx = chart.ctx;
      ctx.save();
      ctx.font = "700 12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      meta.data.forEach((arc, i) => {
        const value = Number(dataset.data[i]) || 0;
        const pct = Math.round((value / total) * 100);
        if (pct <= 3) return;

        const pos = arc.tooltipPosition();
        ctx.fillText(`${pct}%`, pos.x, pos.y);
      });

      ctx.restore();
    }
  };

  if (pieCanvas && pieLabels && pieSeries) {
    const total = sumArray(pieSeries);
    const colors = pieLabels.map((_, i) => PALETTE[i % PALETTE.length]);

    const chart = new Chart(pieCanvas, {
      type: "doughnut",
      data: {
        labels: pieLabels,
        datasets: [{
          label: "Spending",
          data: pieSeries,
          backgroundColor: colors,
          borderColor: "#0b0f16",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "55%",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const value = Number(ctx.raw) || 0;
                const pct = total ? Math.round((value / total) * 100) : 0;
                return `${ctx.label}: ${value.toFixed(2)} (${pct}%)`;
              }
            }
          }
        }
      },
      plugins: [percentLabelsPlugin]
    });

    const table = document.getElementById("spendBreakdownTable");
    if (table) {
      const rows = table.querySelectorAll("tbody tr[data-slice-index]");
      rows.forEach((row) => {
        const idx = Number(row.getAttribute("data-slice-index")) || 0;
        const color = colors[idx % colors.length];

        const swatch = row.querySelector("[data-swatch]");
        if (swatch) swatch.style.backgroundColor = color;

        const badge = row.querySelector("[data-percent-badge]");
        if (badge) {
          badge.style.backgroundColor = "rgba(255,255,255,0.06)";
          badge.style.borderColor = "rgba(255,255,255,0.12)";
          badge.style.color = "#e8eefc";
          badge.style.boxShadow = `0 0 0 1px ${color}33 inset`;
        }

        row.addEventListener("mouseenter", () => {
          chart.setActiveElements([{ datasetIndex: 0, index: idx }]);
          chart.update();
        });

        row.addEventListener("mouseleave", () => {
          chart.setActiveElements([]);
          chart.update();
        });
      });
    }
  }
})();
