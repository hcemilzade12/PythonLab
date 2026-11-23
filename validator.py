import math
import re
from datetime import datetime

FIELD_COUNT = 6
ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
IATA_RE = re.compile(r"[A-Z]{3}")
DT_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DT_FORMAT = "%Y-%m-%d %H:%M"


def load_airports(path: str) -> set[str]:
    codes = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            codes.add(line)
    return codes


def parse_dt(value: str) -> datetime | None:
    # Строгий формат: регэксп отсекает 2025-1-5 9:3, strptime - несуществующие даты
    if not DT_RE.fullmatch(value):
        return None
    try:
        return datetime.strptime(value, DT_FORMAT)
    except ValueError:
        return None


def is_valid_dt(value) -> bool:
    return isinstance(value, str) and parse_dt(value) is not None


def _airport_ok(code: str, airports: set[str]) -> bool:
    return bool(IATA_RE.fullmatch(code)) and code in airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    if len(fields) != FIELD_COUNT:
        return "WRONG_FIELD_COUNT"
    f = [x.strip() for x in fields]
    if any(x == "" for x in f):
        return "MISSING_FIELD"
    flight_id, origin, dest, dep, arr, price = f
    if not ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"
    if not _airport_ok(origin, airports):
        return "INVALID_ORIGIN"
    if not _airport_ok(dest, airports):
        return "INVALID_DESTINATION"
    if origin == dest:
        return "SAME_ORIGIN_DESTINATION"
    dep_dt = parse_dt(dep)
    if dep_dt is None:
        return "INVALID_DEPARTURE"
    arr_dt = parse_dt(arr)
    if arr_dt is None:
        return "INVALID_ARRIVAL"
    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"
    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(value):
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"
    return None


def to_record(fields: list[str]) -> dict:
    f = [x.strip() for x in fields]
    return {
        "flight_id": f[0],
        "origin": f[1],
        "destination": f[2],
        "departure_datetime": f[3],
        "arrival_datetime": f[4],
        "price": float(f[5]),
    }