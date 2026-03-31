"""
Payroll Tool: Calculate payroll, explain payslips, estimate deductions.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PayrollTool:
    """Handles payroll calculations and queries."""

    # Tax brackets (simplified US-style for demo)
    TAX_BRACKETS = [
        (10275, 0.10),
        (41775, 0.12),
        (89075, 0.22),
        (170050, 0.24),
        (215950, 0.32),
        (539900, 0.35),
        (float("inf"), 0.37),
    ]

    SOCIAL_SECURITY_RATE = 0.062  # 6.2%
    MEDICARE_RATE = 0.0145        # 1.45%
    SS_WAGE_BASE = 147000         # 2022 wage base

    def calculate_net_salary(
        self,
        gross_salary: float,
        bonuses: float = 0.0,
        deductions: float = 0.0,
        country: str = "US",
    ) -> Dict[str, float]:
        """
        Calculate net salary from gross.

        Args:
            gross_salary: Monthly gross salary
            bonuses: Additional bonuses
            deductions: Pre-tax deductions (401k, health insurance, etc.)
            country: Country code for tax rules

        Returns:
            Breakdown of salary components
        """
        annual_gross = (gross_salary + bonuses) * 12
        taxable_income = annual_gross - (deductions * 12)

        # Income tax
        tax = self._calc_income_tax(taxable_income)
        monthly_tax = round(tax / 12, 2)

        # Social Security (up to wage base)
        ss = min(annual_gross, self.SS_WAGE_BASE) * self.SOCIAL_SECURITY_RATE
        monthly_ss = round(ss / 12, 2)

        # Medicare
        medicare = annual_gross * self.MEDICARE_RATE
        monthly_medicare = round(medicare / 12, 2)

        gross = gross_salary + bonuses
        total_deductions = deductions + monthly_tax + monthly_ss + monthly_medicare
        net = round(gross - total_deductions, 2)

        return {
            "gross_salary": gross,
            "bonuses": bonuses,
            "pre_tax_deductions": deductions,
            "income_tax": monthly_tax,
            "social_security": monthly_ss,
            "medicare": monthly_medicare,
            "total_deductions": round(total_deductions, 2),
            "net_salary": max(0, net),
            "effective_tax_rate": round((monthly_tax / gross) * 100, 2) if gross > 0 else 0,
        }

    def _calc_income_tax(self, annual_income: float) -> float:
        """Calculate annual income tax using progressive brackets."""
        tax = 0.0
        prev_limit = 0
        for limit, rate in self.TAX_BRACKETS:
            if annual_income <= prev_limit:
                break
            taxable_in_bracket = min(annual_income, limit) - prev_limit
            tax += taxable_in_bracket * rate
            prev_limit = limit
        return round(tax, 2)

    def explain_payslip(self, payroll_record: Dict[str, Any]) -> str:
        """Generate a human-readable payslip explanation."""
        name = payroll_record.get("employee_name", "Employee")
        month = payroll_record.get("period_month", "")
        year = payroll_record.get("period_year", "")
        gross = payroll_record.get("base_salary", 0)
        bonuses = payroll_record.get("bonuses", 0)
        deductions = payroll_record.get("deductions", 0)
        tax = payroll_record.get("tax_amount", 0)
        ss = payroll_record.get("social_security", 0)
        net = payroll_record.get("net_salary", 0)

        breakdown = self.calculate_net_salary(gross, bonuses, deductions)

        return f"""
📄 **Payslip Explanation for {name}**
📅 Period: {month}/{year}

**Earnings:**
• Base Salary: ${gross:,.2f}
• Bonuses: ${bonuses:,.2f}
• **Gross Total: ${gross + bonuses:,.2f}**

**Deductions:**
• Pre-tax deductions: ${deductions:,.2f}
• Income Tax ({breakdown['effective_tax_rate']}%): ${tax:,.2f}
• Social Security (6.2%): ${ss:,.2f}
• Medicare (1.45%): ${breakdown['medicare']:,.2f}
• **Total Deductions: ${deductions + tax + ss:,.2f}**

**Net Pay: ${net:,.2f}**

💡 Your effective tax rate is {breakdown['effective_tax_rate']}%.
        """.strip()

    def estimate_deductions(
        self,
        annual_salary: float,
        has_401k: bool = False,
        contribution_401k: float = 0,
        has_health_insurance: bool = False,
        health_deduction: float = 0,
    ) -> Dict[str, Any]:
        """Estimate annual deductions for an employee."""
        deductions: Dict[str, float] = {}

        if has_401k:
            deductions["401k"] = min(contribution_401k, 20500)  # 2022 limit

        if has_health_insurance:
            deductions["health_insurance"] = health_deduction * 12

        pre_tax = sum(deductions.values())
        result = self.calculate_net_salary(
            annual_salary / 12, 0, pre_tax / 12
        )
        return {
            "annual_salary": annual_salary,
            "deductions_breakdown": deductions,
            "estimated_monthly_net": result["net_salary"],
            "estimated_annual_net": result["net_salary"] * 12,
            "total_annual_tax": result["income_tax"] * 12,
        }


payroll_tool = PayrollTool()
