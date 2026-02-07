"""
RSS schedule helpers.
"""
from __future__ import annotations

from datetime import timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.utils import timezone

from .speaker_config import normalize_speaker_config


def _get_zoneinfo(timezone_name: str) -> ZoneInfo:
    value = (timezone_name or "").strip() or "UTC"
    try:
        return ZoneInfo(value)
    except Exception:
        return ZoneInfo("UTC")


def normalize_week_days(raw_week_days) -> list[int]:
    result = []
    if isinstance(raw_week_days, (list, tuple)):
        for item in raw_week_days:
            try:
                day = int(item)
            except (TypeError, ValueError):
                continue
            if 0 <= day <= 6 and day not in result:
                result.append(day)
    result.sort()
    return result


def compute_next_run_at(schedule, from_dt=None):
    """
    Compute next run datetime in UTC for a schedule.
    """
    now_utc = from_dt or timezone.now()
    tz = _get_zoneinfo(getattr(schedule, "timezone_name", "UTC"))
    local_now = now_utc.astimezone(tz)
    run_time = getattr(schedule, "run_time", None)
    if not run_time:
        run_time = local_now.timetz().replace(second=0, microsecond=0)

    def build_local(day_offset: int):
        target = local_now + timedelta(days=day_offset)
        return target.replace(
            hour=run_time.hour,
            minute=run_time.minute,
            second=0,
            microsecond=0,
        )

    frequency = getattr(schedule, "frequency", "daily")
    if frequency == "weekly":
        week_days = normalize_week_days(getattr(schedule, "week_days", []))
        if not week_days:
            week_days = [local_now.weekday()]

        for offset in range(0, 8):
            candidate = build_local(offset)
            if candidate.weekday() in week_days and candidate > local_now:
                return candidate.astimezone(dt_timezone.utc)

        return build_local(7).astimezone(dt_timezone.utc)

    candidate = build_local(0)
    if candidate <= local_now:
        candidate = build_local(1)
    return candidate.astimezone(dt_timezone.utc)


def build_speaker_config_from_schedule(schedule):
    return normalize_speaker_config(
        {
            "host_name": getattr(schedule, "host_name", ""),
            "guest_name": getattr(schedule, "guest_name", ""),
            "host_voice_id": getattr(schedule, "host_voice_id", ""),
            "guest_voice_id": getattr(schedule, "guest_voice_id", ""),
        }
    )
