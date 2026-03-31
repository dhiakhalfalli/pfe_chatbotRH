"""
Calendar Tool: Schedule and manage interview appointments.
Uses an in-memory store (integrates with Google Calendar or Outlook in prod).
"""
import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CalendarTool:
    """Manages interview scheduling and calendar events."""

    def __init__(self):
        # In-memory event store (replace with DB or external calendar API)
        self._events: Dict[str, Dict[str, Any]] = {}

    def schedule_interview(
        self,
        candidate_id: str,
        candidate_name: str,
        interviewer: str,
        scheduled_at: datetime,
        duration_minutes: int = 60,
        format_type: str = "video",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Schedule a new interview event."""
        event_id = str(uuid.uuid4())
        end_time = scheduled_at + timedelta(minutes=duration_minutes)

        event = {
            "id": event_id,
            "type": "interview",
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "interviewer": interviewer,
            "start_time": scheduled_at.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "format": format_type,
            "notes": notes,
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat(),
        }

        self._events[event_id] = event
        logger.info(f"Interview scheduled: {event_id} for {candidate_name} on {scheduled_at}")
        return event

    def get_available_slots(
        self,
        interviewer: str,
        date: datetime,
        slot_duration_minutes: int = 60,
    ) -> List[Dict[str, Any]]:
        """Get available interview slots for a given day."""
        # Business hours: 9 AM to 5 PM
        slots = []
        start_hour = 9
        end_hour = 17

        # Get existing events for this interviewer on this date
        booked_times = set()
        for event in self._events.values():
            if event["interviewer"] == interviewer:
                event_start = datetime.fromisoformat(event["start_time"])
                if event_start.date() == date.date():
                    booked_times.add(event_start.hour)

        current = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)

        while current + timedelta(minutes=slot_duration_minutes) <= end:
            if current.hour not in booked_times:
                slots.append({
                    "start": current.isoformat(),
                    "end": (current + timedelta(minutes=slot_duration_minutes)).isoformat(),
                    "available": True,
                })
            current += timedelta(minutes=slot_duration_minutes)

        return slots

    def cancel_interview(self, event_id: str) -> bool:
        """Cancel an interview event."""
        if event_id in self._events:
            self._events[event_id]["status"] = "cancelled"
            logger.info(f"Interview cancelled: {event_id}")
            return True
        return False

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self._events.get(event_id)

    def list_events(
        self,
        interviewer: Optional[str] = None,
        candidate_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        events = list(self._events.values())
        if interviewer:
            events = [e for e in events if e["interviewer"] == interviewer]
        if candidate_id:
            events = [e for e in events if e["candidate_id"] == candidate_id]
        return sorted(events, key=lambda x: x["start_time"])


calendar_tool = CalendarTool()
