import streamlit as st
from datetime import datetime, date
from utils import (
    calculate_total_pay,
    format_currency,
    get_available_grades,
    ServiceCategory
)
from report_generators import generate_pdf_report, generate_excel_report
import base64
from PIL import Image
import os

def get_download_link(file_path, link_text):
    """Generate a download link for a file"""
    with open(file_path, "rb") as f:
        bytes = f.read()
        b64 = base64.b64encode(bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_path}">{link_text}</a>'
        return href

def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")
        return None

# Set page title and initial theme
st.set_page_config(
    page_title="SAD Pay Calculator",
    page_icon="🪖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize theme in session state if not present
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# Add theme toggle in sidebar
if st.sidebar.checkbox('Toggle Dark Mode', value=st.session_state.theme == 'dark'):
    st.session_state.theme = 'dark'
else:
    st.session_state.theme = 'light'

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .logo-container img {
        max-width: 300px;
        height: auto;
    }
    .signature-container {
        display: flex;
        justify-content: flex-end;
        padding: 20px 0;
        font-family: 'Times New Roman', Times, serif;
        font-size: 24px;
        color: #007BFF;
    }
    </style>
""", unsafe_allow_html=True)

# Display logo
try:
    logo_path = 'attached_assets/NEW LOGO SMALL.png'
    if os.path.exists(logo_path):
        logo_base64 = get_img_as_base64(logo_path)
        if logo_base64:
            st.markdown(
                f"""
                <div class="logo-container">
                    <img src="data:image/png;base64,{logo_base64}" alt="SAD Pay Calculator Logo">
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("Logo image not found, but application will continue to function.")
except Exception as e:
    st.error(f"Error displaying logo: {str(e)}")

# Create tabs
calculator_tab, correction_tab = st.tabs(["Pay Calculator", "Pay Correction"])

with calculator_tab:
    # Original calculator content
    st.title("SAD Pay Calculator")
    st.markdown("Calculate State Active Duty pay, allowances, and special duty pay based on service category, grade, time in service, and dependent status.")

    # Service Member Information
    st.subheader("Service Member Information")
    col1, col2 = st.columns(2)

    with col1:
        sm_name = st.text_input("Service Member Name", key="sm_name", help="Enter the service member's full name")
        sm_dodid = st.text_input("DOD ID", key="sm_dodid", help="Enter the service member's DOD ID number")

    with col2:
        sm_task_force = st.text_input("Task Force", key="sm_task_force", help="Enter the service member's Task Force")
        sm_company = st.text_input("Company", key="sm_company", help="Enter the service member's Company")

    # Input section
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            service_category = st.selectbox(
                "Service Category",
                [cat.value for cat in ServiceCategory],
                help="Select your service category"
            )

            military_grade = st.selectbox(
                "Military Grade",
                get_available_grades(),
                help="Select your military grade/rank",
                disabled=service_category == ServiceCategory.TEXAS_SG.value
            )

            years_of_service = st.number_input(
                "Years of Service",
                min_value=0,
                max_value=40,
                value=0,
                step=1,
                help="Enter your completed years of service",
                disabled=service_category == ServiceCategory.TEXAS_SG.value
            )

        with col2:
            start_date = st.date_input(
                "Start Date",
                value=date.today(),
                help="Select the start date for pay calculation"
            )

            end_date = st.date_input(
                "End Date",
                value=date.today(),
                help="Select the end date for pay calculation"
            )

            has_dependents = st.checkbox(
                "With Dependents",
                help="Check if you have qualifying dependents for BAH calculation",
                disabled=service_category == ServiceCategory.TEXAS_SG.value
            )

            hazardous_duty = False
            hardship_duty = False
            at_border = False
            present_this_month = False

            # Special Duty Pay section (only for Army NG and Air NG)
            if service_category != ServiceCategory.TEXAS_SG.value:
                st.subheader("🚨 Special Duty Pay")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    hazardous_duty = st.checkbox(
                        "Completed 365 Days of Hazardous Duty",
                        help="Check if you have completed 365 days of hazardous duty"
                    )

                with col2:
                    hardship_duty = st.checkbox(
                        "Eligible for Hardship Duty Pay",
                        help="Check if you are eligible for Hardship Duty Pay"
                    )

                with col3:
                    at_border = st.checkbox(
                        "Located at Border",
                        help="Check if you are located at the Border for Imminent Danger Pay"
                    )

                with col4:
                    present_this_month = st.checkbox(
                        "Present for Duty This Month",
                        help="Check if you have been present for at least one day this month",
                        disabled=not (hazardous_duty or hardship_duty or at_border)
                    )

    # Calculate days between dates
    if start_date and end_date:
        if end_date < start_date:
            st.error("End date must be after start date")
        else:
            service_cat = ServiceCategory(service_category)
            pay_info = calculate_total_pay(
                service_cat,
                military_grade,
                years_of_service,
                start_date,
                end_date,
                has_dependents,
                hazardous_duty,
                hardship_duty,
                at_border,
                present_this_month
            )

            # Display results
            st.header("📊 Pay Calculation")

            if service_cat == ServiceCategory.TEXAS_SG:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Daily Base Pay Rate", format_currency(pay_info['daily_base_rate']))
                with col2:
                    st.metric("Daily Special Pay", format_currency(pay_info['daily_special_rate']))
                with col3:
                    st.metric("Daily Allowance", format_currency(pay_info['daily_allowance_rate']))
            else:
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Daily Base Pay Rate", format_currency(pay_info['daily_base_rate']))
                with col2:
                    st.metric("Daily BAH Rate", format_currency(pay_info['daily_bah_rate']))
                with col3:
                    st.metric("Daily BAS Rate", format_currency(pay_info['daily_bas_rate']))
                with col4:
                    st.metric("Daily Per Diem Rate", format_currency(pay_info['daily_per_diem_rate']))
                with col5:
                    if pay_info['daily_adjustment_rate'] > 0:
                        st.metric("Min Income Adjustment", format_currency(pay_info['daily_adjustment_rate']))

            # Display monthly breakdown
            st.subheader("📅 Monthly Breakdown")

            for month, details in pay_info['monthly_breakdown'].items():
                with st.expander(f"{month} ({details['days']} days)"):
                    if service_cat == ServiceCategory.TEXAS_SG:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Base Pay", format_currency(details['base_pay']))
                        with col2:
                            st.metric("Special Pay", format_currency(details['special_pay']))
                        with col3:
                            st.metric("Allowances", format_currency(details['allowances']))
                        with col4:
                            st.metric("Monthly Total", format_currency(details['total']))
                    else:
                        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
                        with col1:
                            st.metric("Base Pay", format_currency(details['base_pay']))
                        with col2:
                            st.metric("BAH", format_currency(details['bah']))
                        with col3:
                            st.metric("BAS", format_currency(details['bas']))
                        with col4:
                            st.metric("Per Diem", format_currency(details['per_diem']))
                        with col5:
                            if details.get('minimum_income_adjustment', 0) > 0:
                                st.metric("Min Income Adj", format_currency(details['minimum_income_adjustment']))
                        with col6:
                            st.metric("Hazard Pay", format_currency(details['hazard_pay']))
                        with col7:
                            st.metric("Hardship Pay", format_currency(details['hardship_pay']))
                        with col8:
                            st.metric("Danger Pay", format_currency(details['danger_pay']))
                        with col9:
                            st.metric("Monthly Total", format_currency(details['total']))

            # Display grand total
            st.header("💰 Total Compensation")
            st.metric(
                f"Total Pay for {pay_info['total_days']} days",
                format_currency(pay_info['grand_total'])
            )

            # Detailed breakdown
            st.subheader("💡 Pay Details")
            if service_cat == ServiceCategory.TEXAS_SG:
                st.markdown(f"""
                - **Service Category**: {service_category}
                - **Date Range**: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({pay_info['total_days']} days)

                #### Fixed Daily Rates:
                - Base Pay Rate: {format_currency(pay_info['daily_base_rate'])}
                - Special Pay: {format_currency(pay_info['daily_special_rate'])}
                - Daily Allowance: {format_currency(pay_info['daily_allowance_rate'])}
                """)
            else:
                st.markdown(f"""
                - **Service Category**: {service_category}
                - **Grade**: {military_grade}
                - **Years of Service**: {years_of_service}
                - **Date Range**: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({pay_info['total_days']} days)
                - **Dependent Status**: {'With Dependents' if has_dependents else 'Without Dependents'}
                - **Daily Rates**:
                  - Base Pay: {format_currency(pay_info['daily_base_rate'])}
                  - BAH: {format_currency(pay_info['daily_bah_rate'])}
                  - BAS: {format_currency(pay_info['daily_bas_rate'])}
                  - Per Diem: {format_currency(pay_info['daily_per_diem_rate'])}
                  {f"- Min Income Adjustment: {format_currency(pay_info['daily_adjustment_rate'])}" if pay_info['daily_adjustment_rate'] > 0 else ""}
                - **Special Duty Status**:
                  - Hazardous Duty: {'Yes' if hazardous_duty and present_this_month else 'No'}
                  - Hardship Duty: {'Yes' if hardship_duty and present_this_month else 'No'}
                  - Imminent Danger: {'Yes' if at_border and present_this_month else 'No'}
                """)

            # Add report generation buttons
            st.subheader("📄 Generate Reports")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Generate PDF Report"):
                    try:
                        pdf_file = generate_pdf_report(
                            pay_info, service_cat, military_grade, years_of_service,
                            start_date, end_date, has_dependents,
                            hazardous_duty, hardship_duty, at_border,
                            sm_name, sm_dodid, sm_task_force, sm_company
                        )
                        st.markdown(
                            get_download_link(pdf_file, "📥 Download PDF Report"),
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF report: {str(e)}")

            with col2:
                if st.button("Generate Excel Report"):
                    try:
                        excel_file = generate_excel_report(
                            pay_info, service_cat, military_grade, years_of_service,
                            start_date, end_date, has_dependents,
                            hazardous_duty, hardship_duty, at_border,
                            sm_name, sm_dodid, sm_task_force, sm_company
                        )
                        st.markdown(
                            get_download_link(excel_file, "📥 Download Excel Report"),
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        st.error(f"Error generating Excel report: {str(e)}")

with correction_tab:
    st.title("Pay Correction Calculator")
    st.markdown("Compare original pay details with correct calculations and determine any differences.")

    # Service Member Information
    st.subheader("Service Member Information")
    col1, col2 = st.columns(2)

    with col1:
        sm_name = st.text_input("Service Member Name", key="sm_name_corr", help="Enter the service member's full name")
        sm_dodid = st.text_input("DOD ID", key="sm_dodid_corr", help="Enter the service member's DOD ID number")

    with col2:
        sm_task_force = st.text_input("Task Force", key="sm_task_force_corr", help="Enter the service member's Task Force")
        sm_company = st.text_input("Company", key="sm_company_corr", help="Enter the service member's Company")

    # Original Pay Details
    st.subheader("Original Pay Details")
    col1, col2 = st.columns(2)

    with col1:
        original_service_category = st.selectbox(
            "Original Service Category",
            [cat.value for cat in ServiceCategory],
            key="orig_service_cat",
            help="Select your original service category"
        )

        original_grade = st.selectbox(
            "Original Military Grade",
            get_available_grades(),
            key="orig_grade",
            help="Select your original military grade/rank",
            disabled=original_service_category == ServiceCategory.TEXAS_SG.value
        )

        original_years = st.number_input(
            "Original Years of Service",
            min_value=0,
            max_value=40,
            value=0,
            step=1,
            key="orig_years",
            help="Enter your original years of service",
            disabled=original_service_category == ServiceCategory.TEXAS_SG.value
        )

    with col2:
        original_start_date = st.date_input(
            "Original Start Date",
            value=date.today(),
            key="orig_start_date",
            help="Select the original start date"
        )

        original_end_date = st.date_input(
            "Original End Date",
            value=date.today(),
            key="orig_end_date",
            help="Select the original end date"
        )

        original_dependents = st.checkbox(
            "Original With Dependents",
            key="orig_dependents",
            help="Check if you had qualifying dependents for BAH calculation",
            disabled=original_service_category == ServiceCategory.TEXAS_SG.value
        )

    # Special Duty Pay section for Original Pay
    if original_service_category != ServiceCategory.TEXAS_SG.value:
        st.subheader("🚨 Original Special Duty Pay")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            original_hazardous_duty = st.checkbox(
                "Originally Completed 365 Days of Hazardous Duty",
                key="orig_hazardous",
                help="Check if you had completed 365 days of hazardous duty"
            )

        with col2:
            original_hardship_duty = st.checkbox(
                "Originally Eligible for Hardship Duty Pay",
                key="orig_hardship",
                help="Check if you were eligible for Hardship Duty Pay"
            )

        with col3:
            original_at_border = st.checkbox(
                "Originally Located at Border",
                key="orig_border",
                help="Check if you were located at the Border for Imminent Danger Pay"
            )

        with col4:
            original_present_this_month = st.checkbox(
                "Originally Present for Duty This Month",
                key="orig_present",
                help="Check if you were present for at least one day this month",
                disabled=not (original_hazardous_duty or original_hardship_duty or original_at_border)
            )
    else:
        original_hazardous_duty = False
        original_hardship_duty = False
        original_at_border = False
        original_present_this_month = False


    # Correct Pay Details
    st.subheader("Correct Pay Details")
    col1, col2 = st.columns(2)

    with col1:
        correct_service_category = st.selectbox(
            "Correct Service Category",
            [cat.value for cat in ServiceCategory],
            key="correct_service_cat",
            help="Select the correct service category"
        )

        correct_grade = st.selectbox(
            "Correct Military Grade",
            get_available_grades(),
            key="correct_grade",
            help="Select the correct military grade/rank",
            disabled=correct_service_category == ServiceCategory.TEXAS_SG.value
        )

        correct_years = st.number_input(
            "Correct Years of Service",
            min_value=0,
            max_value=40,
            value=0,
            step=1,
            key="correct_years",
            help="Enter the correct years of service",
            disabled=correct_service_category == ServiceCategory.TEXAS_SG.value
        )

    with col2:
        correct_start_date = st.date_input(
            "Correct Start Date",
            value=date.today(),
            key="correct_start_date",
            help="Select the correct start date"
        )

        correct_end_date = st.date_input(
            "Correct End Date",
            value=date.today(),
            key="correct_end_date",
            help="Select the correct end date"
        )

        correct_dependents = st.checkbox(
            "Correct With Dependents",
            key="correct_dependents",
            help="Check if you correctly had qualifying dependents for BAH calculation",
            disabled=correct_service_category == ServiceCategory.TEXAS_SG.value
        )

    # Special Duty Pay section for Correct Pay
    if correct_service_category != ServiceCategory.TEXAS_SG.value:
        st.subheader("🚨 Correct Special Duty Pay")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            correct_hazardous_duty = st.checkbox(
                "Correctly Completed 365 Days of Hazardous Duty",
                key="correct_hazardous",
                help="Check if you had actually completed 365 days of hazardous duty"
            )

        with col2:
            correct_hardship_duty = st.checkbox(
                "Correctly Eligible for Hardship Duty Pay",
                key="correct_hardship",
                help="Check if you were actually eligible for Hardship Duty Pay"
            )

        with col3:
            correct_at_border = st.checkbox(
                "Correctly Located at Border",
                key="correct_border",
                help="Check if you were actually located at the Border for Imminent Danger Pay"
            )

        with col4:
            correct_present_this_month = st.checkbox(
                "Correctly Present for Duty This Month",
                key="correct_present",
                help="Check if you were actually present for at least one day this month",
                disabled=not (correct_hazardous_duty or correct_hardship_duty or correct_at_border)
            )
    else:
        correct_hazardous_duty = False
        correct_hardship_duty = False
        correct_at_border = False
        correct_present_this_month = False

    # Update the Calculate Difference button section
    if st.button("Calculate Difference"):
        try:
            # Calculate original pay
            original_pay = calculate_total_pay(
                ServiceCategory(original_service_category),
                original_grade,
                original_years,
                original_start_date,
                original_end_date,
                original_dependents,
                original_hazardous_duty,
                original_hardship_duty,
                original_at_border,
                original_present_this_month
            )

            # Calculate correct pay
            correct_pay = calculate_total_pay(
                ServiceCategory(correct_service_category),
                correct_grade,
                correct_years,
                correct_start_date,
                correct_end_date,
                correct_dependents,
                correct_hazardous_duty,
                correct_hardship_duty,
                correct_at_border,
                correct_present_this_month
            )

            # Store results in session state
            st.session_state.original_pay = original_pay
            st.session_state.correct_pay = correct_pay
            st.session_state.pay_difference = correct_pay['grand_total'] - original_pay['grand_total']

            # Display comparison results
            st.header("📊 Pay Comparison")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Original Total Pay", format_currency(original_pay['grand_total']))
            with col2:
                st.metric("Correct Total Pay", format_currency(correct_pay['grand_total']))
            with col3:
                st.metric(
                    "Difference (Gain/Loss)",
                    format_currency(abs(st.session_state.pay_difference)),
                    delta=format_currency(st.session_state.pay_difference)
                )

            # Display Special Duty Status
            st.subheader("🚨 Special Duty Status")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Original Special Duty Status:")
                st.write(f"✓ Hazardous Duty: {'Yes' if original_hazardous_duty else 'No'}")
                st.write(f"✓ Hardship Duty: {'Yes' if original_hardship_duty else 'No'}")
                st.write(f"✓ Located at Border: {'Yes' if original_at_border else 'No'}")
                st.write(f"✓ Present for Duty: {'Yes' if original_present_this_month else 'No'}")

            with col2:
                st.write("Correct Special Duty Status:")
                st.write(f"✓ Hazardous Duty: {'Yes' if correct_hazardous_duty else 'No'}")
                st.write(f"✓ Hardship Duty: {'Yes' if correct_hardship_duty else 'No'}")
                st.write(f"✓ Located at Border: {'Yes' if correct_at_border else 'No'}")
                st.write(f"✓ Present for Duty: {'Yes' if correct_present_this_month else 'No'}")

            # Monthly breakdown comparison
            st.subheader("📅 Monthly Breakdown Comparison")
            all_months = set(original_pay['monthly_breakdown'].keys()) | set(correct_pay['monthly_breakdown'].keys())

            for month in sorted(all_months):
                with st.expander(f"{month}"):
                    orig_month = original_pay['monthly_breakdown'].get(month, {
                        'days': 0, 'base_pay': 0, 'bah': 0, 'bas': 0,
                        'hazard_pay': 0, 'hardship_pay': 0, 'danger_pay': 0,
                        'special_pay': 0, 'allowances': 0, 'total': 0,
                        'per_diem': 0, 'minimum_income_adjustment': 0
                    })
                    corr_month = correct_pay['monthly_breakdown'].get(month, {
                        'days': 0, 'base_pay': 0, 'bah': 0, 'bas': 0,
                        'hazard_pay': 0, 'hardship_pay': 0, 'danger_pay': 0,
                        'special_pay': 0, 'allowances': 0, 'total': 0,
                        'per_diem': 0, 'minimum_income_adjustment': 0
                    })

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("Original Pay Details:")
                        st.write(f"Base Pay: {format_currency(orig_month['base_pay'])}")
                        if ServiceCategory(original_service_category) == ServiceCategory.TEXAS_SG:
                            st.write(f"Special Pay: {format_currency(orig_month.get('special_pay', 0))}")
                            st.write(f"Allowances: {format_currency(orig_month.get('allowances', 0))}")
                        else:
                            st.write(f"BAH: {format_currency(orig_month['bah'])}")
                            st.write(f"BAS: {format_currency(orig_month['bas'])}")
                            st.write(f"Per Diem: {format_currency(orig_month['per_diem'])}")
                            min_income_adj = orig_month.get('minimum_income_adjustment', 0)
                            if min_income_adj > 0:
                                st.write(f"Min Income Adj: {format_currency(min_income_adj)}")
                            if original_present_this_month:
                                if original_hazardous_duty:
                                    st.write(f"Hazard Pay: {format_currency(orig_month.get('hazard_pay', 0))}")
                                if original_hardship_duty:
                                    st.write(f"Hardship Pay: {format_currency(orig_month.get('hardship_pay', 0))}")
                                if original_at_border:
                                    st.write(f"Danger Pay: {format_currency(orig_month.get('danger_pay', 0))}")
                        st.write(f"Total: {format_currency(orig_month['total'])}")

                    with col2:
                        st.write("Correct Pay Details:")
                        st.write(f"Base Pay: {format_currency(corr_month['base_pay'])}")
                        if ServiceCategory(correct_service_category) == ServiceCategory.TEXAS_SG:
                            st.write(f"Special Pay: {format_currency(corr_month.get('special_pay', 0))}")
                            st.write(f"Allowances: {format_currency(corr_month.get('allowances', 0))}")
                        else:
                            st.write(f"BAH: {format_currency(corr_month['bah'])}")
                            st.write(f"BAS: {format_currency(corr_month['bas'])}")
                            st.write(f"Per Diem: {format_currency(corr_month['per_diem'])}")
                            min_income_adj = corr_month.get('minimum_income_adjustment', 0)
                            if min_income_adj > 0:
                                st.write(f"Min Income Adj: {format_currency(min_income_adj)}")
                            if correct_present_this_month:
                                if correct_hazardous_duty:
                                    st.write(f"Hazard Pay: {format_currency(corr_month.get('hazard_pay', 0))}")
                                if correct_hardship_duty:
                                    st.write(f"Hardship Pay: {format_currency(corr_month.get('hardship_pay', 0))}")
                                if correct_at_border:
                                    st.write(f"Danger Pay: {format_currency(corr_month.get('danger_pay', 0))}")
                        st.write(f"Total: {format_currency(corr_month['total'])}")

                    with col3:
                        st.write("Difference:")
                        base_diff = corr_month['base_pay'] - orig_month['base_pay']
                        st.write(f"Base Pay: {format_currency(base_diff)}")

                        if ServiceCategory(original_service_category) == ServiceCategory.TEXAS_SG:
                            special_diff = corr_month.get('special_pay', 0) - orig_month.get('special_pay', 0)
                            allowances_diff = corr_month.get('allowances', 0) - orig_month.get('allowances', 0)
                            st.write(f"Special Pay: {format_currency(special_diff)}")
                            st.write(f"Allowances: {format_currency(allowances_diff)}")
                        else:
                            bah_diff = corr_month['bah'] - orig_month['bah']
                            bas_diff = corr_month['bas'] - orig_month['bas']
                            per_diem_diff = corr_month['per_diem'] - orig_month['per_diem']
                            min_income_adj_diff = corr_month.get('minimum_income_adjustment', 0) - orig_month.get('minimum_income_adjustment', 0)

                            st.write(f"BAH: {format_currency(bah_diff)}")
                            st.write(f"BAS: {format_currency(bas_diff)}")
                            st.write(f"Per Diem: {format_currency(per_diem_diff)}")
                            if min_income_adj_diff != 0:
                                st.write(f"Min Income Adj: {format_currency(min_income_adj_diff)}")

                            if original_present_this_month or correct_present_this_month:
                                hazard_diff = corr_month.get('hazard_pay', 0) - orig_month.get('hazard_pay', 0)
                                hardship_diff = corr_month.get('hardship_pay', 0) - orig_month.get('hardship_pay', 0)
                                danger_diff = corr_month.get('danger_pay', 0) - orig_month.get('danger_pay', 0)

                                if original_hazardous_duty or correct_hazardous_duty:
                                    st.write(f"Hazard Pay: {format_currency(hazard_diff)}")
                                if original_hardship_duty or correct_hardship_duty:
                                    st.write(f"Hardship Pay: {format_currency(hardship_diff)}")
                                if original_at_border or correct_at_border:
                                    st.write(f"Danger Pay: {format_currency(danger_diff)}")

                        total_diff = corr_month['total'] - orig_month['total']
                        st.metric(
                            "Monthly Difference",
                            format_currency(abs(total_diff)),
                            delta=format_currency(total_diff)
                        )

            # Generate Reports section
            st.subheader("📄 Generate Reports")
            report_col1, report_col2 = st.columns(2)

            with report_col1:
                if st.button("Generate Correction PDF Report"):
                    try:
                        pdf_file = generate_pdf_report(
                            original_pay,
                            ServiceCategory(correct_service_category),
                            correct_grade,
                            correct_years,
                            correct_start_date,
                            correct_end_date,
                            correct_dependents,
correct_hazardous_duty,
                            correct_hardship_duty,
                            correct_at_border,
                            sm_name,
                            sm_dodid,
                            sm_task_force,
                            sm_company,
                            is_correction=True,
                            original_details={
                                'service_category': original_service_category,
                                'grade': original_grade,
                                'years': original_years,
                                'start_date': original_start_date,
                                'end_date': original_end_date,
                                'dependents': original_dependents,
                                'hazardous_duty': original_hazardous_duty,
                                'hardship_duty': original_hardship_duty,
                                'at_border': original_at_border,
                                'present_this_month': original_present_this_month
                            }
                        )
                        st.markdown(
                            get_download_link(pdf_file, "📥 Download Correction PDF Report"),
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF report: {str(e)}")

            with report_col2:
                if st.button("Generate Correction Excel Report"):
                    try:
                        excel_file = generate_excel_report(
                            original_pay,
                            ServiceCategory(correct_service_category),
                            correct_grade,
                            correct_years,
                            correct_start_date,
                            correct_end_date,
                            correct_dependents,
                            correct_hazardous_duty,
                            correct_hardship_duty,
                            correct_at_border,
                            sm_name,
                            sm_dodid,
                            sm_task_force,
                            sm_company,
                            is_correction=True,
                            original_details={
                                'service_category': original_service_category,
                                'grade': original_grade,
                                'years': original_years,
                                'start_date': original_start_date,
                                'end_date': original_end_date,
                                'dependents': original_dependents,
                                'hazardous_duty': original_hazardous_duty,
                                'hardship_duty': original_hardship_duty,
                                'at_border': original_at_border,
                                'present_this_month': original_present_this_month
                            }
                        )
                        st.markdown(
                            get_download_link(excel_file, "📥 Download Correction Excel Report"),
                            unsafe_allow_html=True
                        )
                    except Exception as e:
                        st.error(f"Error generating Excel report: {str(e)}")

        except Exception as e:
            st.error(f"Error calculating pay difference: {str(e)}")

    # Monthly breakdown comparison
    st.subheader("📅 Monthly Breakdown Comparison")

    # Display Special Duty Status
    col1, col2 = st.columns(2)
    with col1:
        st.write("Original Special Duty Status:")
        st.write(f"✓ Hazardous Duty: {'Yes' if original_hazardous_duty else 'No'}")
        st.write(f"✓ Hardship Duty: {'Yes' if original_hardship_duty else 'No'}")
        st.write(f"✓ Located at Border: {'Yes' if original_at_border else 'No'}")
        st.write(f"✓ Present for Duty: {'Yes' if original_present_this_month else 'No'}")

    with col2:
        st.write("Correct Special Duty Status:")
        st.write(f"✓ Hazardous Duty: {'Yes' if correct_hazardous_duty else 'No'}")
        st.write(f"✓ Hardship Duty: {'Yes' if correct_hardship_duty else 'No'}")
        st.write(f"✓ Located at Border: {'Yes' if correct_at_border else 'No'}")
        st.write(f"✓ Present for Duty: {'Yes' if correct_present_this_month else 'No'}")

    st.markdown("---")

    # Only proceed with detailed breakdown if we have pay data in session state
    if 'original_pay' in st.session_state and 'correct_pay' in st.session_state:
        original_pay = st.session_state.original_pay
        correct_pay = st.session_state.correct_pay
        
        all_months = set(original_pay['monthly_breakdown'].keys()) | set(correct_pay['monthly_breakdown'].keys())

        for month in sorted(all_months):
            with st.expander(f"{month}"):
                orig_month = original_pay['monthly_breakdown'].get(month, {
                    'days': 0, 'base_pay': 0, 'bah': 0, 'bas': 0,
                    'hazard_pay': 0, 'hardship_pay': 0, 'danger_pay': 0,
                    'special_pay': 0, 'allowances': 0, 'total': 0, 'per_diem': 0, 'minimum_income_adjustment':0
                })
                corr_month = correct_pay['monthly_breakdown'].get(month, {
                'days': 0, 'base_pay': 0, 'bah': 0, 'bas': 0,
                'hazard_pay': 0, 'hardship_pay': 0, 'danger_pay': 0,
                'special_pay': 0, 'allowances': 0, 'total': 0, 'per_diem': 0, 'minimum_income_adjustment':0
            })

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("Original Pay:")
                st.write(f"Base Pay: {format_currency(orig_month['base_pay'])}")
                if ServiceCategory(original_service_category) == ServiceCategory.TEXAS_SG:
                    st.write(f"Special Pay: {format_currency(orig_month.get('special_pay', 0))}")
                    st.write(f"Allowances: {format_currency(orig_month.get('allowances', 0))}")
                else:
                    st.write(f"BAH: {format_currency(orig_month['bah'])}")
                    st.write(f"BAS: {format_currency(orig_month['bas'])}")
                    st.write(f"Per Diem: {format_currency(orig_month['per_diem'])}")
                    if original_present_this_month:
                        if original_hazardous_duty:
                            st.write(f"Hazard Pay: {format_currency(orig_month.get('hazard_pay', 0))}")
                        if original_hardship_duty:
                            st.write(f"Hardship Pay: {format_currency(orig_month.get('hardship_pay', 0))}")
                        if original_at_border:
                            st.write(f"Danger Pay: {format_currency(orig_month.get('danger_pay', 0))}")
                    if orig_month.get('minimum_income_adjustment', 0)>0:
                        st.write(f"Min Income Adj: {format_currency(orig_month['minimum_income_adjustment'])}")
                st.write(f"Total: {format_currency(orig_month['total'])}")


            with col2:
                st.write("Correct Pay:")
                st.write(f"Base Pay: {format_currency(corr_month['base_pay'])}")
                if ServiceCategory(correct_service_category) == ServiceCategory.TEXAS_SG:
                    st.write(f"Special Pay: {format_currency(corr_month.get('special_pay', 0))}")
                    st.write(f"Allowances: {format_currency(corr_month.get('allowances', 0))}")
                else:
                    st.write(f"BAH: {format_currency(corr_month['bah'])}")
                    st.write(f"BAS: {format_currency(corr_month['bas'])}")
                    st.write(f"Per Diem: {format_currency(corr_month['per_diem'])}")
                    if correct_present_this_month:
                        if correct_hazardous_duty:
                            st.write(f"Hazard Pay: {format_currency(corr_month.get('hazard_pay', 0))}")
                        if correct_hardship_duty:
                            st.write(f"Hardship Pay: {format_currency(corr_month.get('hardship_pay', 0))}")
                        if correct_at_border:
                            st.write(f"Danger Pay: {format_currency(corr_month.get('danger_pay', 0))}")
                    if corr_month.get('minimum_income_adjustment', 0)>0:
                        st.write(f"Min Income Adj: {format_currency(corr_month['minimum_income_adjustment'])}")
                st.write(f"Total: {format_currency(corr_month['total'])}")

            with col3:
                st.write("Difference:")
                base_diff = corr_month['base_pay'] - orig_month['base_pay']
                st.write(f"Base Pay: {format_currency(base_diff)}")

                if ServiceCategory(original_service_category) == ServiceCategory.TEXAS_SG:
                    special_diff = corr_month.get('special_pay', 0) - orig_month.get('special_pay', 0)
                    allowances_diff = corr_month.get('allowances', 0) - orig_month.get('allowances', 0)
                    st.write(f"Special Pay: {format_currency(special_diff)}")
                    st.write(f"Allowances: {format_currency(allowances_diff)}")
                else:
                    bah_diff = corr_month['bah'] - orig_month['bah']
                    bas_diff = corr_month['bas'] - orig_month['bas']
                    per_diem_diff = corr_month['per_diem'] - orig_month['per_diem']
                    min_income_adj_diff = corr_month.get('minimum_income_adjustment', 0) - orig_month.get('minimum_income_adjustment', 0)

                    st.write(f"BAH: {format_currency(bah_diff)}")
                    st.write(f"BAS: {format_currency(bas_diff)}")
                    st.write(f"Per Diem: {format_currency(per_diem_diff)}")

                    if min_income_adj_diff != 0:
                        st.write(f"Min Income Adj: {format_currency(min_income_adj_diff)}")

                    if original_present_this_month or correct_present_this_month:
                        hazard_diff = corr_month.get('hazard_pay', 0) - orig_month.get('hazard_pay', 0)
                        hardship_diff = corr_month.get('hardship_pay', 0) - orig_month.get('hardship_pay', 0)
                        danger_diff = corr_month.get('danger_pay', 0) - orig_month.get('danger_pay', 0)

                        if original_hazardous_duty or correct_hazardous_duty:
                            st.write(f"Hazard Pay: {format_currency(hazard_diff)}")
                        if original_hardship_duty or correct_hardship_duty:
                            st.write(f"Hardship Pay: {format_currency(hardship_diff)}")
                        if original_at_border or correct_at_border:
                            st.write(f"Danger Pay: {format_currency(danger_diff)}")

                total_diff = corr_month['total'] - orig_month['total']
                st.metric(
                    "Monthly Difference",
                    format_currency(abs(total_diff)),
                    delta=format_currency(total_diff)
                )

    # Add report generation buttons for correction comparison
    st.subheader("📄 Generate Correction Reports")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate Correction PDF Report", key="btn_pdf_report") and 'original_pay' in st.session_state:
            try:
                original_pay = st.session_state.original_pay
                pdf_file = generate_pdf_report(
                    original_pay,
                    ServiceCategory(correct_service_category),
                    correct_grade,
                    correct_years,
                    correct_start_date,
                    correct_end_date,
                    correct_dependents,
                    correct_hazardous_duty,
                    correct_hardship_duty,
                    correct_at_border,
                    sm_name,
                    sm_dodid,
                    sm_task_force,
                    sm_company,
                    is_correction=True,
                    original_details={
                        'service_category': original_service_category,
                        'grade': original_grade,
                        'years': original_years,
                        'start_date': original_start_date,
                        'end_date': original_end_date,
                        'dependents': original_dependents,
                        'hazardous_duty': original_hazardous_duty,
                        'hardship_duty': original_hardship_duty,
                        'at_border': original_at_border,
                        'present_this_month': original_present_this_month
                    }
                )
                st.markdown(
                    get_download_link(pdf_file, "📥 Download Correction PDF Report"),
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"Error generating PDF report: {str(e)}")

    with col2:
        if st.button("Generate Correction Excel Report", key="btn_excel_report") and 'original_pay' in st.session_state:
            try:
                original_pay = st.session_state.original_pay
                excel_file = generate_excel_report(
                    original_pay,
                    ServiceCategory(correct_service_category),
                    correct_grade,
                    correct_years,
                    correct_start_date,
                    correct_end_date,
                    correct_dependents,
                    correct_hazardous_duty,
                    correct_hardship_duty,
                    correct_at_border,
                    sm_name,
                    sm_dodid,
                    sm_task_force,
                    sm_company,
                    is_correction=True,
                    original_details={
                        'service_category': original_service_category,
                        'grade': original_grade,
                        'years': original_years,
                        'start_date': original_start_date,
                        'end_date': original_end_date,
                        'dependents': original_dependents,
                        'hazardous_duty': original_hazardous_duty,
                        'hardship_duty': original_hardship_duty,
                        'at_border': original_at_border,
                        'present_this_month': original_present_this_month
                    }
                )
                st.markdown(
                    get_download_link(excel_file, "📥 Download Correction Excel Report"),
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.error(f"Error generating Excel report: {str(e)}")

# Footer with signature
st.markdown("---")
st.markdown(
    '<div class="signature-container">Created by 1LT George Mikhael</div>',
    unsafe_allow_html=True
)

st.markdown("🪖 SAD Pay Calculator | Made with Streamlit")