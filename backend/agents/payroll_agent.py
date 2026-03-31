"""
Payroll Agent: Answers payroll questions, explains payslips,
and calculates salary breakdowns.
"""
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

from backend.tools.payroll_tool import payroll_tool
from backend.database.mysql import get_sql_db


class PayrollAgent:
    """
    Handles employee payroll queries using the payroll tool and database.
    """

    def answer_question(
        self,
        question: str,
        employee_id: Optional[str] = None,
        employee_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route a payroll question to the appropriate handler.
        """
        question_lower = question.lower()
        logger.info(f"Payroll question: {question[:80]}")

        # ── Intent detection ────────────────────────────────────────────────
        if any(kw in question_lower for kw in ["net salary", "take home", "net pay"]):
            return self._handle_net_salary_query(question, employee_id)

        elif any(kw in question_lower for kw in ["payslip", "pay slip", "breakdown", "deduction"]):
            return self._handle_payslip_query(employee_id)

        elif any(kw in question_lower for kw in ["tax", "income tax", "withholding"]):
            return self._handle_tax_query(question)

        elif any(kw in question_lower for kw in ["bonus", "raise", "increment", "salary increase"]):
            return self._handle_bonus_query(question, employee_id)

        elif any(kw in question_lower for kw in ["401k", "retirement", "pension"]):
            return self._handle_benefits_query(question)

        else:
            return self._handle_general_query(question, employee_id)

    def _handle_net_salary_query(
        self,
        question: str,
        employee_id: Optional[str],
    ) -> Dict[str, Any]:
        """Calculate or look up net salary."""
        # Try to extract salary from question
        salary_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', question)
        gross = None
        if salary_match:
            gross = float(salary_match.group(1).replace(",", ""))

        if gross is None and employee_id:
            # Look up from DB
            try:
                db = get_sql_db()
                emp = db.get_employee(employee_id)
                if emp:
                    gross = emp.get("base_salary", 5000)
            except Exception:
                gross = 5000

        if gross is None:
            gross = 5000  # Default example

        breakdown = payroll_tool.calculate_net_salary(gross)

        return {
            "type": "net_salary",
            "gross_salary": gross,
            "calculation": breakdown,
            "response": (
                f"💰 **Net Salary Calculation**\n\n"
                f"Gross Monthly: **${gross:,.2f}**\n"
                f"Income Tax: -${breakdown['income_tax']:,.2f}\n"
                f"Social Security: -${breakdown['social_security']:,.2f}\n"
                f"Medicare: -${breakdown['medicare']:,.2f}\n"
                f"**Net Pay: ${breakdown['net_salary']:,.2f}**\n\n"
                f"Effective tax rate: {breakdown['effective_tax_rate']}%"
            ),
        }

    def _handle_payslip_query(self, employee_id: Optional[str]) -> Dict[str, Any]:
        """Retrieve and explain the latest payslip."""
        records = []
        if employee_id:
            try:
                db = get_sql_db()
                records = db.get_payroll_records(employee_id)
            except Exception:
                pass

        if records:
            latest = records[0]
            explanation = payroll_tool.explain_payslip(latest)
            return {
                "type": "payslip",
                "payroll_record": latest,
                "response": explanation,
            }
        else:
            # Provide example explanation
            sample = {
                "employee_name": "You",
                "period_month": 3,
                "period_year": 2026,
                "base_salary": 5000,
                "bonuses": 500,
                "deductions": 200,
                "tax_amount": 650,
                "social_security": 310,
                "net_salary": 4340,
            }
            return {
                "type": "payslip_example",
                "response": payroll_tool.explain_payslip(sample),
            }

    def _handle_tax_query(self, question: str) -> Dict[str, Any]:
        salary_match = re.search(r'\$?([\d,]+)', question)
        salary = float(salary_match.group(1).replace(",", "")) if salary_match else 60000

        breakdown = payroll_tool.calculate_net_salary(salary / 12)
        annual_tax = breakdown["income_tax"] * 12

        return {
            "type": "tax_info",
            "annual_salary": salary,
            "annual_tax": annual_tax,
            "effective_rate": breakdown["effective_tax_rate"],
            "response": (
                f"🧾 **Tax Information**\n\n"
                f"For an annual salary of **${salary:,.0f}**:\n"
                f"• Monthly income tax: **${breakdown['income_tax']:,.2f}**\n"
                f"• Annual tax: **${annual_tax:,.2f}**\n"
                f"• Effective tax rate: **{breakdown['effective_tax_rate']}%**\n\n"
                f"*Note: Actual taxes depend on filing status, deductions, and state taxes.*"
            ),
        }

    def _handle_bonus_query(self, question: str, employee_id: Optional[str]) -> Dict[str, Any]:
        bonus_match = re.search(r'\$?([\d,]+)', question)
        bonus = float(bonus_match.group(1).replace(",", "")) if bonus_match else 1000

        base = 5000
        if employee_id:
            try:
                db = get_sql_db()
                emp = db.get_employee(employee_id)
                if emp:
                    base = emp.get("base_salary", 5000)
            except Exception:
                pass

        without_bonus = payroll_tool.calculate_net_salary(base)
        with_bonus = payroll_tool.calculate_net_salary(base, bonus)
        net_bonus = with_bonus["net_salary"] - without_bonus["net_salary"]

        return {
            "type": "bonus_impact",
            "gross_bonus": bonus,
            "net_bonus": round(net_bonus, 2),
            "response": (
                f"🎁 **Bonus Impact Analysis**\n\n"
                f"Gross bonus: ${bonus:,.2f}\n"
                f"After-tax bonus: **${net_bonus:,.2f}**\n"
                f"Effective take-home rate: {round((net_bonus/bonus)*100, 1)}%\n\n"
                f"*Bonuses are taxed as ordinary income in the month received.*"
            ),
        }

    def _handle_benefits_query(self, question: str) -> Dict[str, Any]:
        return {
            "type": "benefits_info",
            "response": (
                "🏦 **Retirement & Benefits Information**\n\n"
                "• **401(k)**: Contribute up to $22,500/year (2024). Pre-tax contributions reduce taxable income.\n"
                "• **Employer Match**: Company matches up to 4% of your salary.\n"
                "• **Roth 401(k)**: After-tax contributions, tax-free withdrawals in retirement.\n"
                "• **HSA**: If enrolled in HDHP, contribute up to $3,850/year pre-tax.\n\n"
                "Contact HR to update your contribution rates or investment allocations."
            ),
        }

    def _handle_general_query(
        self,
        question: str,
        employee_id: Optional[str],
    ) -> Dict[str, Any]:
        return {
            "type": "general",
            "response": (
                "💼 **Payroll Information**\n\n"
                "I can help you with:\n"
                "• **Net salary calculation** – Ask: 'What is my net salary?'\n"
                "• **Payslip explanation** – Ask: 'Explain my payslip'\n"
                "• **Tax breakdown** – Ask: 'How much tax on $80,000?'\n"
                "• **Bonus impact** – Ask: 'Net impact of a $2,000 bonus?'\n"
                "• **Benefits** – Ask: 'How does my 401k work?'\n\n"
                "Please be more specific about what payroll information you need."
            ),
        }


payroll_agent = PayrollAgent()
