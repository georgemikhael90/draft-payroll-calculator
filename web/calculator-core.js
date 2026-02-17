(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory;
  } else {
    root.PayrollCore = factory(root.PAYROLL_DATA);
  }
})(typeof self !== "undefined" ? self : this, function createPayrollCore(data) {
  if (!data) {
    throw new Error("PAYROLL_DATA missing.");
  }

  var TEXAS_SG_RATES = data.TEXAS_SG_RATES;
  var PER_DIEM_RATE = data.PER_DIEM_RATE;
  var MINIMUM_DAILY_RATE = data.MINIMUM_DAILY_RATE;
  var PAY_GRADES = data.PAY_GRADES;
  var BAH_RATES = data.BAH_RATES;

  function round2(n) {
    return Math.round((n + Number.EPSILON) * 100) / 100;
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(amount || 0));
  }

  function parseYmdToUtcDate(ymd) {
    var parts = ymd.split("-");
    return new Date(Date.UTC(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])));
  }

  function toMonthKey(d) {
    return d.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
  }

  function firstOfMonth(d) {
    return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1));
  }

  function firstOfNextMonth(d) {
    return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1));
  }

  function addDays(d, days) {
    return new Date(d.getTime() + days * 86400000);
  }

  function minDate(a, b) {
    return a.getTime() <= b.getTime() ? a : b;
  }

  function maxDate(a, b) {
    return a.getTime() >= b.getTime() ? a : b;
  }

  function daysInclusive(start, end) {
    return Math.floor((end.getTime() - start.getTime()) / 86400000) + 1;
  }

  function calculateMinimumIncomeAdjustment(dailyBaseRate, dailyBahRate, dailyBasRate) {
    var dailyTotal = dailyBaseRate + dailyBahRate + dailyBasRate + PER_DIEM_RATE;
    if (dailyTotal < MINIMUM_DAILY_RATE) {
      return MINIMUM_DAILY_RATE - dailyTotal;
    }
    return 0;
  }

  function getBasePayRate(grade, yearsOfService) {
    var gradePay = PAY_GRADES[grade] || PAY_GRADES["E-1"];
    var years = Object.keys(gradePay)
      .map(function (k) { return Number(k); })
      .filter(function (y) { return y <= yearsOfService; })
      .sort(function (a, b) { return a - b; });

    var bracket = years.length ? years[years.length - 1] : 0;
    return Number(gradePay[String(bracket)]);
  }

  function getBahRate(grade, hasDependents) {
    var rates = BAH_RATES[grade] || BAH_RATES["E-1"];
    return hasDependents ? rates.with : rates.without;
  }

  function getBasRate(grade) {
    if (grade.indexOf("O-") === 0 || grade === "O1E" || grade === "O2E" || grade === "O3E") {
      return 10.69;
    }
    return 15.53;
  }

  function getHazardousDutyPay(hasCompleted365Days, presentThisMonth) {
    return hasCompleted365Days && presentThisMonth ? 1000 : 0;
  }

  function getHardshipDutyPay(presentThisMonth) {
    return presentThisMonth ? 500 : 0;
  }

  function getImminentDangerPay(presentThisMonth, atBorder) {
    return presentThisMonth && atBorder ? 225 : 0;
  }

  function calculateTexasSgPay(startDate, endDate) {
    var current = new Date(startDate.getTime());
    var monthly = {};

    while (current.getTime() <= endDate.getTime()) {
      var monthKey = toMonthKey(current);
      var monthStart = maxDate(startDate, firstOfMonth(current));
      var monthEnd = minDate(endDate, addDays(firstOfNextMonth(current), -1));
      var days = daysInclusive(monthStart, monthEnd);

      var basePay = TEXAS_SG_RATES.daily_base_rate * days;
      var specialPay = TEXAS_SG_RATES.special_pay * days;
      var allowances = TEXAS_SG_RATES.daily_allowance * days;
      var monthlyTotal = TEXAS_SG_RATES.total_daily_rate * days;

      monthly[monthKey] = {
        days: days,
        base_pay: round2(basePay),
        special_pay: round2(specialPay),
        allowances: round2(allowances),
        total: round2(monthlyTotal),
        bah: 0,
        bas: 0,
        per_diem: 0,
        minimum_income_adjustment: 0,
        hazard_pay: 0,
        hardship_pay: 0,
        danger_pay: 0,
      };

      current = firstOfNextMonth(current);
    }

    var totalDays = daysInclusive(startDate, endDate);
    var grand = Object.keys(monthly).reduce(function (sum, m) { return sum + monthly[m].total; }, 0);

    return {
      daily_base_rate: TEXAS_SG_RATES.daily_base_rate,
      daily_special_rate: TEXAS_SG_RATES.special_pay,
      daily_allowance_rate: TEXAS_SG_RATES.daily_allowance,
      monthly_breakdown: monthly,
      total_days: totalDays,
      grand_total: round2(grand),
    };
  }

  function calculateTotalPay(input) {
    var serviceCategory = input.service_category;
    var grade = input.grade;
    var years = Number(input.years_of_service || 0);
    var startDate = typeof input.start_date === "string" ? parseYmdToUtcDate(input.start_date) : input.start_date;
    var endDate = typeof input.end_date === "string" ? parseYmdToUtcDate(input.end_date) : input.end_date;
    var hasDependents = Boolean(input.has_dependents);
    var hazardousDuty = Boolean(input.hazardous_duty);
    var hardshipDuty = Boolean(input.hardship_duty);
    var atBorder = Boolean(input.at_border);
    var presentThisMonth = Boolean(input.present_this_month);

    if (serviceCategory === "Texas State Guard") {
      return calculateTexasSgPay(startDate, endDate);
    }

    var dailyBase = getBasePayRate(grade, years);
    var dailyBah = round2(getBahRate(grade, hasDependents));
    var dailyBas = round2(getBasRate(grade));
    var dailyAdjustment = calculateMinimumIncomeAdjustment(dailyBase, dailyBah, dailyBas);

    var monthly = {};
    var current = new Date(startDate.getTime());

    while (current.getTime() <= endDate.getTime()) {
      var monthKey = toMonthKey(current);
      var monthStart = maxDate(startDate, firstOfMonth(current));
      var monthEnd = minDate(endDate, addDays(firstOfNextMonth(current), -1));
      var days = daysInclusive(monthStart, monthEnd);

      var basePay = dailyBase * days;
      var bah = dailyBah * days;
      var bas = dailyBas * days;
      var perDiem = PER_DIEM_RATE * days;
      var adjustment = dailyAdjustment * days;
      var hazardPay = getHazardousDutyPay(hazardousDuty, presentThisMonth);
      var hardshipPay = getHardshipDutyPay(hardshipDuty ? presentThisMonth : false);
      var dangerPay = getImminentDangerPay(presentThisMonth, atBorder);
      var total = basePay + bah + bas + perDiem + adjustment + hazardPay + hardshipPay + dangerPay;

      monthly[monthKey] = {
        days: days,
        base_pay: round2(basePay),
        bah: round2(bah),
        bas: round2(bas),
        per_diem: round2(perDiem),
        minimum_income_adjustment: round2(adjustment),
        hazard_pay: round2(hazardPay),
        hardship_pay: round2(hardshipPay),
        danger_pay: round2(dangerPay),
        total: round2(total),
      };

      current = firstOfNextMonth(current);
    }

    var totalDays = daysInclusive(startDate, endDate);
    var grand = Object.keys(monthly).reduce(function (sum, m) { return sum + monthly[m].total; }, 0);

    return {
      daily_base_rate: dailyBase,
      daily_bah_rate: dailyBah,
      daily_bas_rate: dailyBas,
      daily_per_diem_rate: PER_DIEM_RATE,
      daily_adjustment_rate: dailyAdjustment,
      monthly_breakdown: monthly,
      total_days: totalDays,
      grand_total: round2(grand),
    };
  }

  function getAvailableGrades() {
    var enlisted = ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9"];
    var warrant = ["W-1", "W-2", "W-3", "W-4", "W-5"];
    var officer = ["O-1", "O1E", "O-2", "O2E", "O-3", "O3E", "O-4", "O-5", "O-6"];
    return enlisted.concat(warrant).concat(officer);
  }

  return {
    calculateTotalPay: calculateTotalPay,
    formatCurrency: formatCurrency,
    getAvailableGrades: getAvailableGrades,
  };
});
