"""
Leave Agent: Handles leave balance inquiries, request submission,
and HR database updates.
"""
import logging
from typing import Dict, Any, Optional
from datetime import date

logger = logging.getLogger(__name__)

from backend.tools.leave_tool import leave_tool
from backend.database.mysql import get_sql_db


class LeaveAgent:
    """
    Processes leave-related requests: balance checks, submissions, approvals.
    """

    def handle_request(
        self,
        action: str,
        employee_id: str,
        leave_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route leave actions to the appropriate handler.
        Actions: check_balance | submit | approve | reject | list | summary
        """
        action = action.lower().strip()
        logger.info(f"Leave action: {action} for employee {employee_id}")

        if action in ("check_balance", "balance", "check"):
            return self.check_balance(employee_id, leave_type)
        elif action in ("submit", "request", "apply"):
            return self.submit_request(employee_id, leave_type, start_date, end_date, reason)
        elif action in ("approve",):
            return self.approve_request(request_id, employee_id)
        elif action in ("reject",):
            return self.reject_request(request_id)
        elif action in ("list", "history"):
            return self.list_requests(employee_id)
        elif action in ("summary",):
            return self.get_summary(employee_id)
        else:
            return {
                "status": "error",
                "response": (
                    "❓ Unknown leave action. Available actions:\n"
                    "• `check_balance` – Check your leave balance\n"
                    "• `submit` – Submit a leave request\n"
                    "• `list` – View your leave history\n"
                    "• `summary` – Full leave summary"
                ),
            }

    def check_balance(
        self,
        employee_id: str,
        leave_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check employee leave balance."""
        leave_balance = self._get_leave_balance(employee_id)

        if leave_type:
            lt = leave_type.lower()
            available = leave_balance.get(lt, 0)
            return {
                "status": "success",
                "leave_type": lt,
                "days_available": available,
                "response": f"📅 You have **{available} days** of {lt} leave remaining.",
            }

        summary = leave_tool.get_leave_summary(leave_balance)
        return {
            "status": "success",
            "leave_balance": leave_balance,
            "response": summary,
        }

    def submit_request(
        self,
        employee_id: str,
        leave_type: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a leave request."""
        if not all([leave_type, start_date, end_date]):
            return {
                "status": "error",
                "response": (
                    "⚠️ Please provide:\n"
                    "• Leave type (annual, sick, emergency)\n"
                    "• Start date\n"
                    "• End date"
                ),
            }

        # Calculate days
        assert start_date and end_date
        days = leave_tool.calculate_leave_days(start_date, end_date)

        # Check balance
        leave_balance = self._get_leave_balance(employee_id)
        balance_check = leave_tool.check_balance(
            employee_id, leave_type, leave_balance, days
        )

        if not balance_check["can_approve"]:
            return {
                "status": "insufficient_balance",
                "days_requested": days,
                "days_available": balance_check["days_available"],
                "response": balance_check["message"],
            }

        # Create request
        request = leave_tool.create_request(
            employee_id, leave_type, start_date, end_date, reason
        )

        # Store in DB
        try:
            db = get_sql_db()
            request_id = db.insert_leave_request(request)
            request["id"] = request_id

            # Deduct balance (auto-approved for demo; in prod would be pending)
            new_balance = leave_tool.update_balance(leave_balance, leave_type, days)
            db.update_leave_status(request_id, "approved")
            self._update_employee_balance(employee_id, new_balance)
        except Exception as e:
            logger.error(f"DB error on leave submit: {e}")

        return {
            "status": "submitted",
            "request_id": request.get("id"),
            "leave_type": leave_type,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "days_requested": days,
            "response": (
                f"✅ **Leave Request Submitted**\n\n"
                f"• Type: {leave_type.title()} Leave\n"
                f"• Dates: {start_date} to {end_date}\n"
                f"• Duration: **{days} working days**\n"
                f"• Remaining balance: {balance_check['days_after_approval']} days\n\n"
                f"Your request has been submitted and is pending manager approval."
            ),
        }

    def approve_request(
        self,
        request_id: Optional[str],
        approved_by: str = "HR Manager",
    ) -> Dict[str, Any]:
        if not request_id:
            return {"status": "error", "response": "Request ID required"}
        try:
            db = get_sql_db()
            db.update_leave_status(request_id, "approved", approved_by)
            return {
                "status": "approved",
                "request_id": request_id,
                "response": f"✅ Leave request `{request_id}` has been **approved** by {approved_by}.",
            }
        except Exception as e:
            return {"status": "error", "response": str(e)}

    def reject_request(self, request_id: Optional[str]) -> Dict[str, Any]:
        if not request_id:
            return {"status": "error", "response": "Request ID required"}
        try:
            db = get_sql_db()
            db.update_leave_status(request_id, "rejected")
            return {
                "status": "rejected",
                "request_id": request_id,
                "response": f"❌ Leave request `{request_id}` has been **rejected**.",
            }
        except Exception as e:
            return {"status": "error", "response": str(e)}

    def list_requests(self, employee_id: str) -> Dict[str, Any]:
        try:
            db = get_sql_db()
            requests = db.get_leave_requests(employee_id)
            if not requests:
                return {
                    "status": "success",
                    "requests": [],
                    "response": "📋 No leave requests found.",
                }
            lines = ["📋 **Your Leave Requests:**\n"]
            for req in requests[-10:]:  # Last 10
                lines.append(
                    f"• [{req['status'].upper()}] {req['leave_type'].title()} | "
                    f"{req['start_date']} → {req['end_date']} ({req['days_requested']} days)"
                )
            return {
                "status": "success",
                "requests": requests,
                "response": "\n".join(lines),
            }
        except Exception as e:
            return {"status": "error", "response": str(e)}

    def get_summary(self, employee_id: str) -> Dict[str, Any]:
        balance = self._get_leave_balance(employee_id)
        balance_summary = leave_tool.get_leave_summary(balance)
        return {
            "status": "success",
            "leave_balance": balance,
            "response": balance_summary,
        }

    def _get_leave_balance(self, employee_id: str) -> Dict[str, int]:
        try:
            db = get_sql_db()
            emp = db.get_employee(employee_id)
            if emp and emp.get("leave_balance"):
                balance = emp["leave_balance"]
                if isinstance(balance, str):
                    import json
                    balance = json.loads(balance)
                return balance
        except Exception:
            pass
        return {"annual": 20, "sick": 10, "emergency": 3}

    def _update_employee_balance(self, employee_id: str, new_balance: Dict[str, int]) -> None:
        try:
            import json
            db = get_sql_db()
            db._conn.execute(
                "UPDATE employees SET leave_balance = ? WHERE id = ?",
                (json.dumps(new_balance), employee_id)
            )
            db._conn.commit()
        except Exception as e:
            logger.error(f"Failed to update leave balance: {e}")


leave_agent = LeaveAgent()
