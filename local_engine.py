from dataclasses import dataclass
from datetime import date
from typing import Dict, Any

from utils import ServiceCategory, calculate_total_pay, format_currency, get_available_grades


@dataclass
class PayrollInput:
    service_category: ServiceCategory
    grade: str
    years_of_service: int
    start_date: date
    end_date: date
    has_dependents: bool = False
    hazardous_duty: bool = False
    hardship_duty: bool = False
    at_border: bool = False
    present_this_month: bool = False


def run_payroll_calculation(payload: PayrollInput) -> Dict[str, Any]:
    return calculate_total_pay(
        payload.service_category,
        payload.grade,
        payload.years_of_service,
        payload.start_date,
        payload.end_date,
        payload.has_dependents,
        payload.hazardous_duty,
        payload.hardship_duty,
        payload.at_border,
        payload.present_this_month,
    )


__all__ = [
    "PayrollInput",
    "ServiceCategory",
    "run_payroll_calculation",
    "format_currency",
    "get_available_grades",
]
