(function () {
  var core = window.PayrollCore;
  var SERVICE_CATEGORIES = ["Army National Guard", "Air National Guard", "Texas State Guard"];

  var state = {
    payInput: null,
    payResult: null,
    correctionInput: null,
    correctionResult: null,
  };

  function $(id) { return document.getElementById(id); }

  function todayYmd() {
    var now = new Date();
    return now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0") + "-" + String(now.getDate()).padStart(2, "0");
  }

  function metric(title, value) {
    return '<div class="metric"><div class="k">' + title + '</div><div class="v">' + value + '</div></div>';
  }

  function setSelectOptions(selectEl, values) {
    selectEl.innerHTML = "";
    values.forEach(function (v) {
      var op = document.createElement("option");
      op.value = v;
      op.textContent = v;
      selectEl.appendChild(op);
    });
  }

  function fillCommonControls() {
    setSelectOptions($("service_category"), SERVICE_CATEGORIES);
    setSelectOptions($("o_service_category"), SERVICE_CATEGORIES);
    setSelectOptions($("c_service_category"), SERVICE_CATEGORIES);

    var grades = core.getAvailableGrades();
    setSelectOptions($("military_grade"), grades);
    setSelectOptions($("o_military_grade"), grades);
    setSelectOptions($("c_military_grade"), grades);

    ["start_date", "end_date", "o_start_date", "o_end_date", "c_start_date", "c_end_date"].forEach(function (id) {
      $(id).value = todayYmd();
    });
  }

  function toggleMilitaryFields(prefix) {
    var cat = $(prefix + "service_category").value;
    var isTexasSg = cat === "Texas State Guard";
    $(prefix + "military_grade").disabled = isTexasSg;
    $(prefix + "years_of_service").disabled = isTexasSg;
    $(prefix + "has_dependents").disabled = isTexasSg;

    var block = $(prefix + "special_block") || $("special_duty_block");
    if (block) block.style.display = isTexasSg ? "none" : "grid";

    togglePresentDuty(prefix);
  }

  function togglePresentDuty(prefix) {
    var h = $(prefix + "hazardous_duty").checked;
    var hd = $(prefix + "hardship_duty").checked;
    var b = $(prefix + "at_border").checked;
    var p = $(prefix + "present_this_month");
    var enable = h || hd || b;
    p.disabled = !enable;
    if (!enable) p.checked = false;
  }

  function buildInput(prefix) {
    return {
      service_category: $(prefix + "service_category").value,
      grade: $(prefix + "military_grade").value,
      years_of_service: Number($(prefix + "years_of_service").value || 0),
      start_date: $(prefix + "start_date").value,
      end_date: $(prefix + "end_date").value,
      has_dependents: $(prefix + "has_dependents").checked,
      hazardous_duty: $(prefix + "hazardous_duty").checked,
      hardship_duty: $(prefix + "hardship_duty").checked,
      at_border: $(prefix + "at_border").checked,
      present_this_month: $(prefix + "present_this_month").checked,
    };
  }

  function clearError(id) { $(id).textContent = ""; }
  function showError(id, msg) { $(id).textContent = msg; }

  function validateInput(input, errorId) {
    clearError(errorId);
    if (!input.start_date || !input.end_date) {
      showError(errorId, "Please select start and end dates.");
      return false;
    }
    if (input.end_date < input.start_date) {
      showError(errorId, "End date must be after start date.");
      return false;
    }
    return true;
  }

  function renderPayResult(input, payInfo) {
    var dailyHtml = "";
    if (input.service_category === "Texas State Guard") {
      dailyHtml += metric("Daily Base Pay Rate", core.formatCurrency(payInfo.daily_base_rate));
      dailyHtml += metric("Daily Special Pay", core.formatCurrency(payInfo.daily_special_rate));
      dailyHtml += metric("Daily Allowance", core.formatCurrency(payInfo.daily_allowance_rate));
    } else {
      dailyHtml += metric("Daily Base Pay Rate", core.formatCurrency(payInfo.daily_base_rate));
      dailyHtml += metric("Daily BAH Rate", core.formatCurrency(payInfo.daily_bah_rate));
      dailyHtml += metric("Daily BAS Rate", core.formatCurrency(payInfo.daily_bas_rate));
      dailyHtml += metric("Daily Per Diem Rate", core.formatCurrency(payInfo.daily_per_diem_rate));
      if (payInfo.daily_adjustment_rate > 0) {
        dailyHtml += metric("Min Income Adjustment", core.formatCurrency(payInfo.daily_adjustment_rate));
      }
    }
    $("daily_metrics").innerHTML = dailyHtml;
    $("grand_total").textContent = core.formatCurrency(payInfo.grand_total);
    $("total_days").textContent = "Total Pay for " + payInfo.total_days + " days";

    var monthlyHost = $("monthly_breakdown");
    monthlyHost.innerHTML = "";
    Object.keys(payInfo.monthly_breakdown).forEach(function (monthKey) {
      var d = payInfo.monthly_breakdown[monthKey];
      var rowHtml = "";
      if (input.service_category === "Texas State Guard") {
        rowHtml += metric("Base Pay", core.formatCurrency(d.base_pay));
        rowHtml += metric("Special Pay", core.formatCurrency(d.special_pay));
        rowHtml += metric("Allowances", core.formatCurrency(d.allowances));
        rowHtml += metric("Monthly Total", core.formatCurrency(d.total));
      } else {
        rowHtml += metric("Base Pay", core.formatCurrency(d.base_pay));
        rowHtml += metric("BAH", core.formatCurrency(d.bah));
        rowHtml += metric("BAS", core.formatCurrency(d.bas));
        rowHtml += metric("Per Diem", core.formatCurrency(d.per_diem));
        rowHtml += metric("Min Income Adj", core.formatCurrency(d.minimum_income_adjustment || 0));
        rowHtml += metric("Hazard Pay", core.formatCurrency(d.hazard_pay));
        rowHtml += metric("Hardship Pay", core.formatCurrency(d.hardship_pay));
        rowHtml += metric("Danger Pay", core.formatCurrency(d.danger_pay));
        rowHtml += metric("Monthly Total", core.formatCurrency(d.total));
      }

      var card = document.createElement("article");
      card.className = "month";
      card.innerHTML = "<h4>" + monthKey + " (" + d.days + " days)</h4><div class='month-grid'>" + rowHtml + "</div>";
      monthlyHost.appendChild(card);
    });

    $("summary_panel").hidden = false;
    $("export_pay_pdf").disabled = false;
    $("export_pay_excel").disabled = false;
  }

  function mergeMonths(a, b) {
    var map = {};
    Object.keys(a).forEach(function (k) { map[k] = true; });
    Object.keys(b).forEach(function (k) { map[k] = true; });
    return Object.keys(map);
  }

  function renderCorrectionResult(origInput, origPay, corrInput, corrPay) {
    var diff = Number((corrPay.grand_total - origPay.grand_total).toFixed(2));
    var statusText = "No difference detected.";
    var statusClass = "ok";
    if (diff > 0) {
      statusText = "Underpayment detected: " + core.formatCurrency(diff);
      statusClass = "warn";
    } else if (diff < 0) {
      statusText = "Overpayment detected: " + core.formatCurrency(Math.abs(diff));
      statusClass = "bad";
    }

    $("correction_metrics").innerHTML =
      metric("Original Total Pay", core.formatCurrency(origPay.grand_total)) +
      metric("Correct Total Pay", core.formatCurrency(corrPay.grand_total)) +
      metric("Difference", core.formatCurrency(diff));

    var status = $("correction_status");
    status.className = "status " + statusClass;
    status.textContent = statusText;

    var host = $("correction_monthly");
    host.innerHTML = "";

    mergeMonths(origPay.monthly_breakdown, corrPay.monthly_breakdown).sort().forEach(function (monthKey) {
      var o = origPay.monthly_breakdown[monthKey] || {};
      var c = corrPay.monthly_breakdown[monthKey] || {};
      var mt = Number(((c.total || 0) - (o.total || 0)).toFixed(2));

      var rows = [
        ["Base Pay", o.base_pay || 0, c.base_pay || 0],
        ["BAH", o.bah || 0, c.bah || 0],
        ["BAS", o.bas || 0, c.bas || 0],
        ["Per Diem", o.per_diem || 0, c.per_diem || 0],
        ["Min Adj", o.minimum_income_adjustment || 0, c.minimum_income_adjustment || 0],
        ["Hazard", o.hazard_pay || 0, c.hazard_pay || 0],
        ["Hardship", o.hardship_pay || 0, c.hardship_pay || 0],
        ["Danger", o.danger_pay || 0, c.danger_pay || 0],
        ["Total", o.total || 0, c.total || 0],
      ];

      if (origInput.service_category === "Texas State Guard" || corrInput.service_category === "Texas State Guard") {
        rows = [
          ["Base Pay", o.base_pay || 0, c.base_pay || 0],
          ["Special Pay", o.special_pay || 0, c.special_pay || 0],
          ["Allowances", o.allowances || 0, c.allowances || 0],
          ["Total", o.total || 0, c.total || 0],
        ];
      }

      var rowHtml = rows.map(function (r) {
        var d = Number((r[2] - r[1]).toFixed(2));
        return metric(r[0] + " (Orig)", core.formatCurrency(r[1])) +
          metric(r[0] + " (Corr)", core.formatCurrency(r[2])) +
          metric(r[0] + " (Diff)", core.formatCurrency(d));
      }).join("");

      var card = document.createElement("article");
      card.className = "month";
      card.innerHTML = "<h4>" + monthKey + "</h4><div class='month-grid'>" + rowHtml + "</div><div class='sub'>Monthly Total Difference: " + core.formatCurrency(mt) + "</div>";
      host.appendChild(card);
    });

    $("correction_results").hidden = false;
    $("export_corr_pdf").disabled = false;
    $("export_corr_excel").disabled = false;
  }

  function buildPayExportRows(input, payInfo) {
    var rows = [];
    Object.keys(payInfo.monthly_breakdown).forEach(function (monthKey) {
      var d = payInfo.monthly_breakdown[monthKey];
      if (input.service_category === "Texas State Guard") {
        rows.push({ Month: monthKey, Component: "Base Pay", Amount: d.base_pay });
        rows.push({ Month: monthKey, Component: "Special Pay", Amount: d.special_pay });
        rows.push({ Month: monthKey, Component: "Allowances", Amount: d.allowances });
        rows.push({ Month: monthKey, Component: "Monthly Total", Amount: d.total });
      } else {
        rows.push({ Month: monthKey, Component: "Base Pay", Amount: d.base_pay });
        rows.push({ Month: monthKey, Component: "BAH", Amount: d.bah });
        rows.push({ Month: monthKey, Component: "BAS", Amount: d.bas });
        rows.push({ Month: monthKey, Component: "Per Diem", Amount: d.per_diem });
        rows.push({ Month: monthKey, Component: "Min Income Adjustment", Amount: d.minimum_income_adjustment || 0 });
        rows.push({ Month: monthKey, Component: "Hazard Pay", Amount: d.hazard_pay });
        rows.push({ Month: monthKey, Component: "Hardship Pay", Amount: d.hardship_pay });
        rows.push({ Month: monthKey, Component: "Danger Pay", Amount: d.danger_pay });
        rows.push({ Month: monthKey, Component: "Monthly Total", Amount: d.total });
      }
    });
    rows.push({ Month: "ALL", Component: "Grand Total", Amount: payInfo.grand_total });
    return rows;
  }

  function buildCorrectionExportRows(corrState) {
    var rows = [];
    var o = corrState.originalResult;
    var c = corrState.correctResult;
    mergeMonths(o.monthly_breakdown, c.monthly_breakdown).sort().forEach(function (monthKey) {
      var om = o.monthly_breakdown[monthKey] || {};
      var cm = c.monthly_breakdown[monthKey] || {};
      ["base_pay","bah","bas","per_diem","minimum_income_adjustment","hazard_pay","hardship_pay","danger_pay","special_pay","allowances","total"].forEach(function (k) {
        var ov = Number(om[k] || 0);
        var cv = Number(cm[k] || 0);
        if (ov !== 0 || cv !== 0 || k === "total") {
          rows.push({
            Month: monthKey,
            Component: k,
            Original: ov,
            Correct: cv,
            Difference: Number((cv - ov).toFixed(2)),
          });
        }
      });
    });
    rows.push({
      Month: "ALL",
      Component: "grand_total",
      Original: o.grand_total,
      Correct: c.grand_total,
      Difference: Number((c.grand_total - o.grand_total).toFixed(2)),
    });
    return rows;
  }

  function exportExcel(filename, rows, sheetName) {
    if (!window.XLSX) {
      alert("Excel export library did not load. Please check internet access for CDN scripts.");
      return;
    }
    var rowsWithCredit = rows.slice();
    if (rowsWithCredit.length > 0) {
      var firstKey = Object.keys(rowsWithCredit[0])[0];
      var noteRow = {};
      noteRow[firstKey] = "Developed by George Mikhael";
      rowsWithCredit.push({});
      rowsWithCredit.push(noteRow);
    }
    var ws = XLSX.utils.json_to_sheet(rowsWithCredit);
    var wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, sheetName || "Report");
    XLSX.writeFile(wb, filename);
  }

  function exportPdf(title, subtitleLines, headers, rows, filename) {
    if (!window.jspdf || !window.jspdf.jsPDF) {
      alert("PDF export library did not load. Please check internet access for CDN scripts.");
      return;
    }
    var doc = new window.jspdf.jsPDF({ unit: "pt", format: "letter" });
    function addPageBranding() {
      try {
        var logo = document.querySelector(".logo");
        if (logo) {
          var pageWidth = doc.internal.pageSize.getWidth();
          var logoW = 72;
          var logoH = 72;
          doc.addImage(logo, "PNG", pageWidth - logoW - 36, 18, logoW, logoH);
        }
      } catch (e) {
      }
      var pageHeight = doc.internal.pageSize.getHeight();
      doc.setFontSize(9);
      doc.text("Developed by George Mikhael", 40, pageHeight - 20);
    }

    doc.setFontSize(16);
    doc.text(title, 40, 40);
    doc.setFontSize(10);
    var y = 58;
    subtitleLines.forEach(function (line) {
      doc.text(String(line), 40, y);
      y += 14;
    });
    doc.text("Developed by George Mikhael", 40, y);
    y += 14;

    if (typeof doc.autoTable === "function") {
      doc.autoTable({
        head: [headers],
        body: rows,
        startY: y + 8,
        styles: { fontSize: 8 },
        headStyles: { fillColor: [15, 94, 168] },
        didDrawPage: function () {
          addPageBranding();
        },
      });
    } else {
      addPageBranding();
    }

    doc.save(filename);
  }

  function calculatePay() {
    var input = buildInput("");
    if (!validateInput(input, "pay_error")) {
      $("summary_panel").hidden = true;
      $("export_pay_pdf").disabled = true;
      $("export_pay_excel").disabled = true;
      return;
    }
    var result = core.calculateTotalPay(input);
    state.payInput = input;
    state.payResult = result;
    renderPayResult(input, result);
  }

  function compareCorrection() {
    var original = buildInput("o_");
    var corrected = buildInput("c_");

    clearError("corr_error");
    if (!validateInput(original, "corr_error") || !validateInput(corrected, "corr_error")) {
      $("correction_results").hidden = true;
      $("export_corr_pdf").disabled = true;
      $("export_corr_excel").disabled = true;
      return;
    }

    var originalResult = core.calculateTotalPay(original);
    var correctResult = core.calculateTotalPay(corrected);

    state.correctionInput = { original: original, corrected: corrected };
    state.correctionResult = { originalResult: originalResult, correctResult: correctResult };

    renderCorrectionResult(original, originalResult, corrected, correctResult);
  }

  function setupTabs() {
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
    tabs.forEach(function (btn) {
      btn.addEventListener("click", function () {
        tabs.forEach(function (b) {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
          var panel = $(b.dataset.tab);
          panel.classList.remove("active");
          panel.hidden = true;
        });
        btn.classList.add("active");
        btn.setAttribute("aria-selected", "true");
        var p = $(btn.dataset.tab);
        p.classList.add("active");
        p.hidden = false;
      });
    });
  }

  function setupTheme() {
    $("theme_mode").addEventListener("change", function () {
      document.body.setAttribute("data-theme", this.value);
    });
  }

  function setupListeners() {
    ["", "o_", "c_"].forEach(function (prefix) {
      $(prefix + "service_category").addEventListener("change", function () { toggleMilitaryFields(prefix); });
      $(prefix + "hazardous_duty").addEventListener("change", function () { togglePresentDuty(prefix); });
      $(prefix + "hardship_duty").addEventListener("change", function () { togglePresentDuty(prefix); });
      $(prefix + "at_border").addEventListener("change", function () { togglePresentDuty(prefix); });
    });

    $("calculate_btn").addEventListener("click", calculatePay);
    $("compare_btn").addEventListener("click", compareCorrection);

    $("export_pay_excel").addEventListener("click", function () {
      if (!state.payResult || !state.payInput) return;
      var rows = buildPayExportRows(state.payInput, state.payResult);
      exportExcel("pay_calculation_report.xlsx", rows, "Pay Calculation");
    });

    $("export_pay_pdf").addEventListener("click", function () {
      if (!state.payResult || !state.payInput) return;
      var rows = buildPayExportRows(state.payInput, state.payResult).map(function (r) {
        return [r.Month, r.Component, core.formatCurrency(r.Amount)];
      });
      var meta = [
        "Service Category: " + state.payInput.service_category,
        "Grade: " + state.payInput.grade,
        "Years of Service: " + state.payInput.years_of_service,
        "Date Range: " + state.payInput.start_date + " to " + state.payInput.end_date,
        "Grand Total: " + core.formatCurrency(state.payResult.grand_total),
      ];
      exportPdf("SAD Pay Calculator Report", meta, ["Month", "Component", "Amount"], rows, "pay_calculation_report.pdf");
    });

    $("export_corr_excel").addEventListener("click", function () {
      if (!state.correctionResult) return;
      var rows = buildCorrectionExportRows(state.correctionResult);
      exportExcel("pay_correction_report.xlsx", rows, "Pay Correction");
    });

    $("export_corr_pdf").addEventListener("click", function () {
      if (!state.correctionResult || !state.correctionInput) return;
      var rows = buildCorrectionExportRows(state.correctionResult).map(function (r) {
        return [r.Month, r.Component, core.formatCurrency(r.Original), core.formatCurrency(r.Correct), core.formatCurrency(r.Difference)];
      });
      var diff = Number((state.correctionResult.correctResult.grand_total - state.correctionResult.originalResult.grand_total).toFixed(2));
      var meta = [
        "Original: " + state.correctionInput.original.service_category + " | " + state.correctionInput.original.grade + " | " + state.correctionInput.original.start_date + " to " + state.correctionInput.original.end_date,
        "Correct: " + state.correctionInput.corrected.service_category + " | " + state.correctionInput.corrected.grade + " | " + state.correctionInput.corrected.start_date + " to " + state.correctionInput.corrected.end_date,
        "Total Difference: " + core.formatCurrency(diff),
      ];
      exportPdf("SAD Pay Correction Report", meta, ["Month", "Component", "Original", "Correct", "Difference"], rows, "pay_correction_report.pdf");
    });
  }

  function init() {
    fillCommonControls();
    setupTabs();
    setupTheme();
    setupListeners();
    ["", "o_", "c_"].forEach(function (prefix) { toggleMilitaryFields(prefix); });
  }

  init();
})();
