import re
from datetime import datetime, timedelta


def parse_time_expression(text):
    """
    Parse a natural language time expression.
    Returns (seconds_from_now, human_readable) or (None, None).

    Handles:
      - "in 5 minutes", "in 2 hours", "in 30 seconds"
      - "at 7:30 AM", "at 7:30pm", "at 7:30 PM"
      - "at 7 am", "at 3pm"
      - "for 7:30 AM", "for 11:21 PM"  ← alarm-friendly
      - "for 7 am"
    """
    text = text.lower().strip()

    # --- "in X minutes/hours/seconds" ---
    m = re.search(r"in\s+(\d+)\s*(second|sec|minute|min|hour|hr)s?", text)
    if m:
        value = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("sec"):
            secs = value
            human = f"{value} second{'s' if value != 1 else ''}"
        elif unit.startswith("min"):
            secs = value * 60
            human = f"{value} minute{'s' if value != 1 else ''}"
        else:
            secs = value * 3600
            human = f"{value} hour{'s' if value != 1 else ''}"
        return secs, human

    # --- "at|for H:MM am|pm" (with minutes, optional am/pm) ---
    m = re.search(r"(?:at|for)\s+(\d{1,2}):(\d{2})\s*(am|pm)?", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = m.group(3)

        # If am/pm is missing, infer: 0-7 = PM, 8-23 = AM (common convention)
        if ampm is None:
            if 1 <= hour <= 7:
                ampm = "pm"
            elif 8 <= hour <= 11:
                ampm = "am"
            elif hour == 12:
                ampm = "pm"

        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)

        secs = (target - now).total_seconds()
        return secs, target.strftime("%I:%M %p")

    # --- "at|for H am|pm" (no minutes) ---
    m = re.search(r"(?:at|for)\s+(\d{1,2})\s*(am|pm)", text)
    if m:
        hour = int(m.group(1))
        ampm = m.group(2)
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

        now = datetime.now()
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)

        secs = (target - now).total_seconds()
        return secs, target.strftime("%I:%M %p")

    # --- "at|for H" (no minutes, no am/pm — infer from current time) ---
    m = re.search(r"(?:at|for)\s+(\d{1,2})\b(?!:)", text)
    if m:
        hour = int(m.group(1))
        if 0 <= hour <= 23:
            now = datetime.now()
            target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)

            secs = (target - now).total_seconds()
            return secs, target.strftime("%I:%M %p")

    return None, None


def extract_message(text):
    """
    Extract the message from a reminder/alarm phrase.
    Example: "remind me in 5 minutes to check the oven" -> "check the oven"
    """
    text = text.strip()

    m = re.search(r"\bto\s+(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip(".!?")

    m = re.search(r"\bthat\s+(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip(".!?")

    m = re.search(r"\babout\s+(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip(".!?")

    return "reminder"
