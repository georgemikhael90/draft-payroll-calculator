import os
import base64
from datetime import date

import streamlit as st

from local_engine import (
    PayrollInput,
    ServiceCategory,
    run_payroll_calculation,
    format_currency,
    get_available_grades,
)


st.set_page_config(
    page_title="SAD Pay Calculator",
    page_icon="??",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme" not in st.session_state:
    st.session_state.theme = "light"

if st.sidebar.checkbox("Toggle Dark Mode", value=st.session_state.theme == "dark"):
    st.session_state.theme = "dark"
else:
    st.session_state.theme = "light"

st.markdown(
    """
    <style>
    .main { padding: 2rem; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 1.5rem; }
    .logo-container img { max-width: 280px; height: auto; }
    .stAlert { margin-top: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def img_to_b64(path: str):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


logo_path = os.path.join("attached_assets", "NEW LOGO SMALL.png")
if os.path.exists(logo_path):
    logo_b64 = img_to_b64(logo_path)
    if logo_b64:
        st.markdown(
            f"""
            <div class="logo-container">
                <img src="data:image/png;base64,{logo_b64}" alt="SAD Pay Calculator Logo"/>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.title("SAD Pay Calculator")
st.markdown(
    "Calculate State Active Duty pay using the same rates and formulas as your Replit payroll tracker."
)

calculator_tab, compare_tab = st.tabs(["Pay Calculator", "Pay Comparison"])

with calculator_tab:
    st.subheader("Service Member Information")
    c1, c2 = st.columns(2)
    with c1:
        sm_name = st.text_input("Service Member Name")
        sm_dodid = st.text_input("DOD ID")
    with c2:
        sm_task_force = st.text_input("Task Force")
        sm_company = st.text_input("Company")

    st.subheader("Pay Inputs")
    c1, c2 = st.columns(2)

    with c1:
        service_category_text = st.selectbox(
            "Service Category", [c.value for c in ServiceCategory]
        )
        is_texas_sg = service_category_text == ServiceCategory.TEXAS_SG.value

        military_grade = st.selectbox(
            "Military Grade", get_available_grades(), disabled=is_texas_sg
        )
        years_of_service = st.number_input(
            "Years of Service", min_value=0, max_value=40, value=0, step=1, disabled=is_texas_sg
        )

    with c2:
        start_date = st.date_input("Start Date", value=date.today())
        end_date = st.date_input("End Date", value=date.today())
        has_dependents = st.checkbox("With Dependents", disabled=is_texas_sg)

    hazardous_duty = False
    hardship_duty = False
    at_border = False
    present_this_month = False

    if not is_texas_sg:
        st.subheader("Special Duty Pay")
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            hazardous_duty = st.checkbox("Completed 365 Days of Hazardous Duty")
        with d2:
            hardship_duty = st.checkbox("Eligible for Hardship Duty Pay")
        with d3:
            at_border = st.checkbox("Located at Border")
        with d4:
            present_this_month = st.checkbox(
                "Present for Duty This Month",
                disabled=not (hazardous_duty or hardship_duty or at_border),
            )

    if end_date < start_date:
        st.error("End date must be after start date")
    else:
        payload = PayrollInput(
            service_category=ServiceCategory(service_category_text),
            grade=military_grade,
            years_of_service=int(years_of_service),
            start_date=start_date,
            end_date=end_date,
            has_dependents=has_dependents,
            hazardous_duty=hazardous_duty,
            hardship_duty=hardship_duty,
            at_border=at_border,
            present_this_month=present_this_month,
        )

        pay_info = run_payroll_calculation(payload)

        st.header("Pay Calculation")

        if payload.service_category == ServiceCategory.TEXAS_SG:
            m1, m2, m3 = st.columns(3)
            m1.metric("Daily Base Pay Rate", format_currency(pay_info["daily_base_rate"]))
            m2.metric("Daily Special Pay", format_currency(pay_info["daily_special_rate"]))
            m3.metric("Daily Allowance", format_currency(pay_info["daily_allowance_rate"]))
        else:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Daily Base Pay Rate", format_currency(pay_info["daily_base_rate"]))
            m2.metric("Daily BAH Rate", format_currency(pay_info["daily_bah_rate"]))
            m3.metric("Daily BAS Rate", format_currency(pay_info["daily_bas_rate"]))
            m4.metric("Daily Per Diem Rate", format_currency(pay_info["daily_per_diem_rate"]))
            if pay_info["daily_adjustment_rate"] > 0:
                m5.metric("Min Income Adjustment", format_currency(pay_info["daily_adjustment_rate"]))

        st.subheader("Monthly Breakdown")
        for month, details in pay_info["monthly_breakdown"].items():
            with st.expander(f"{month} ({details['days']} days)"):
                if payload.service_category == ServiceCategory.TEXAS_SG:
                    b1, b2, b3, b4 = st.columns(4)
                    b1.metric("Base Pay", format_currency(details["base_pay"]))
                    b2.metric("Special Pay", format_currency(details["special_pay"]))
                    b3.metric("Allowances", format_currency(details["allowances"]))
                    b4.metric("Monthly Total", format_currency(details["total"]))
                else:
                    b1, b2, b3, b4, b5, b6, b7, b8 = st.columns(8)
                    b1.metric("Base Pay", format_currency(details["base_pay"]))
                    b2.metric("BAH", format_currency(details["bah"]))
                    b3.metric("BAS", format_currency(details["bas"]))
                    b4.metric("Per Diem", format_currency(details["per_diem"]))
                    b5.metric("Min Adj", format_currency(details.get("minimum_income_adjustment", 0)))
                    b6.metric("Hazard", format_currency(details["hazard_pay"]))
                    b7.metric("Hardship", format_currency(details["hardship_pay"]))
                    b8.metric("Danger", format_currency(details["danger_pay"]))
                    st.metric("Monthly Total", format_currency(details["total"]))

        st.header("Total Compensation")
        st.metric(
            f"Total Pay for {pay_info['total_days']} days",
            format_currency(pay_info["grand_total"]),
        )

        st.caption(
            f"Service Member: {sm_name or 'N/A'} | DOD ID: {sm_dodid or 'N/A'} | "
            f"Task Force: {sm_task_force or 'N/A'} | Company: {sm_company or 'N/A'}"
        )

with compare_tab:
    st.subheader("Pay Comparison (Original vs Correct)")
    st.markdown("Use this to compare two calculations and see under/overpayment.")

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("**Original Setup**")
        o_cat = st.selectbox("Service Category (Original)", [c.value for c in ServiceCategory], key="o_cat")
        o_grade = st.selectbox("Grade (Original)", get_available_grades(), key="o_grade")
        o_years = st.number_input("Years (Original)", 0, 40, 0, key="o_years")
        o_start = st.date_input("Start Date (Original)", date.today(), key="o_start")
        o_end = st.date_input("End Date (Original)", date.today(), key="o_end")
        o_dep = st.checkbox("With Dependents (Original)", key="o_dep")

    with cc2:
        st.markdown("**Correct Setup**")
        c_cat = st.selectbox("Service Category (Correct)", [c.value for c in ServiceCategory], key="c_cat")
        c_grade = st.selectbox("Grade (Correct)", get_available_grades(), key="c_grade")
        c_years = st.number_input("Years (Correct)", 0, 40, 0, key="c_years")
        c_start = st.date_input("Start Date (Correct)", date.today(), key="c_start")
        c_end = st.date_input("End Date (Correct)", date.today(), key="c_end")
        c_dep = st.checkbox("With Dependents (Correct)", key="c_dep")

    if st.button("Compare Totals"):
        if o_end < o_start or c_end < c_start:
            st.error("Each end date must be after its start date.")
        else:
            original = run_payroll_calculation(
                PayrollInput(ServiceCategory(o_cat), o_grade, int(o_years), o_start, o_end, o_dep)
            )
            correct = run_payroll_calculation(
                PayrollInput(ServiceCategory(c_cat), c_grade, int(c_years), c_start, c_end, c_dep)
            )
            diff = correct["grand_total"] - original["grand_total"]

            c1, c2, c3 = st.columns(3)
            c1.metric("Original Total", format_currency(original["grand_total"]))
            c2.metric("Correct Total", format_currency(correct["grand_total"]))
            c3.metric("Difference", format_currency(diff))

            if diff > 0:
                st.warning("Underpayment detected in original setup.")
            elif diff < 0:
                st.error("Overpayment detected in original setup.")
            else:
                st.success("No difference between original and correct totals.")
