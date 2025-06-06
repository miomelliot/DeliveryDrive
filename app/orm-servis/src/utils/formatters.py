# src/utils/formatters.py
from datetime import time


def format_time_range(start: time, end: time) -> str:
    return f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"
