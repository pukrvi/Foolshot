from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .schemas import Calendar, Hours

IST = ZoneInfo("Asia/Kolkata")


def hours_for(calendar: Calendar, day: date) -> Hours | None:
    if day not in calendar.days:
        raise ValueError(f"calendar missing date {day}")
    return calendar.days[day]


def phase(at: datetime, day: date, hours: Hours | None) -> str:
    if at.utcoffset() is None:
        raise ValueError("timestamp requires a timezone")
    if hours is None:
        return "holiday"
    start = datetime.combine(day, hours.open, IST)
    end = datetime.combine(day, hours.close, IST)
    if not start <= at < end:
        return "closed"
    if at < start + timedelta(minutes=30):
        return "warmup"
    if at >= end - timedelta(minutes=60):
        return "observe_only"
    return "evaluation"
