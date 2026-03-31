"""
Leave Management Tool: Calculate leave balances and manage requests.
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


class LeaveTool:
    """Handles leave balance calculation and request management."""

    LEAVE_ENTITLEMENTS = {
        "annual": 20,
        "sick": 10,
        "emergency": 3,
        "maternity": 90,
        "paternity": 14,
        "unpaid": 30,
    }

    def calculate_leave_days(self, start_date: date, end_date: date) -> int:
        """Calculate working days between two dates (Mon–Fri)."""
        if end_date < start_date:
            return 0
        count = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Monday=0, Friday=4
                count += 1
            current += timedelta(days=1)
        return count

    def check_balance(
        self,
        employee_id: str,
        leave_type: str,
        leave_balance: Dict[str, int],
        days_requested: int,
    ) -> Dict[str, Any]:
        """Check if the employee has enough leave balance."""
        available = leave_balance.get(leave_type, 0)
        entitlement = self.LEAVE_ENTITLEMENTS.get(leave_type, 0)

        return {
            "employee_id": employee_id,
            "leave_type": leave_type,
            "days_requested": days_requested,
            "days_available": available,
            "annual_entitlement": entitlement,
            "can_approve": available >= days_requested,
            "days_after_approval": available - days_requested if available >= days_requested else None,
            "message": (
                f"✅ Request approved. You will have {available - days_requested} days remaining."
                if available >= days_requested
                else f"❌ Insufficient balance. Requested {days_requested} days but only {available} available."
            ),
        }

    def create_request(
        self,
        employee_id: str,
        leave_type: str,
        start_date: date,
        end_date: date,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new leave request document."""
        days = self.calculate_leave_days(start_date, end_date)
        return {
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "leave_type": leave_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days_requested": days,
            "reason": reason,
            "status": "pending",
            "submitted_at": datetime.utcnow().isoformat(),
        }

    def update_balance(
        self,
        leave_balance: Dict[str, int],
        leave_type: str,
        days_approved: int,
    ) -> Dict[str, int]:
        """Deduct approved leave days from balance."""
        updated = dict(leave_balance)
        current = updated.get(leave_type, 0)
        updated[leave_type] = max(0, current - days_approved)
        return updated

    def get_leave_summary(self, leave_balance: Dict[str, int]) -> str:
        """Generate a human-readable leave balance summary."""
        lines = ["📊 **Your Leave Balance:**\n"]
        for leave_type, days in leave_balance.items():
            entitlement = self.LEAVE_ENTITLEMENTS.get(leave_type, 0)
            taken = entitlement - days
            lines.append(f"• **{leave_type.title()}**: {days}/{entitlement} days remaining ({taken} used)")
        return "\n".join(lines)


leave_tool = LeaveTool()
