import math

from validator import is_valid_dt

RECORD_KEYS = ("flight_id", "origin", "destination",
               "departure_datetime", "arrival_datetime", "price")
STR_KEYS = ("flight_id", "origin", "destination")
DT_KEYS = ("departure_datetime", "arrival_datetime")
NUM_KEYS = ("price", "min_price")
ALLOWED = set(STR_KEYS) | set(DT_KEYS) | set(NUM_KEYS) | {"sort_by", "order", "limit"}


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _valid(query) -> bool:
    if not isinstance(query, dict):
        return False
    for key, val in query.items():
        if key not in ALLOWED:
            return False
        if key in STR_KEYS and not isinstance(val, str):
            return False
        if key in DT_KEYS and not is_valid_dt(val):
            return False
        if key in NUM_KEYS and not _is_number(val):
            return False
        if key == "sort_by" and (not isinstance(val, str) or val not in RECORD_KEYS):
            return False
        if key == "order" and (not isinstance(val, str) or val not in ("asc", "desc")):
            return False
        if key == "limit" and (not isinstance(val, int) or isinstance(val, bool) or val < 0):
            return False
    if "order" in query and "sort_by" not in query:
        return False
    return True


def _matches(rec: dict, q: dict) -> bool:
    for key in STR_KEYS:
        if key in q and rec[key] != q[key]:
            return False
    if "departure_datetime" in q and rec["departure_datetime"] < q["departure_datetime"]:
        return False
    if "arrival_datetime" in q and rec["arrival_datetime"] > q["arrival_datetime"]:
        return False
    if "price" in q and not rec["price"] <= q["price"]:
        return False
    if "min_price" in q and not rec["price"] >= q["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    if not _valid(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}
    result = [r for r in db if _matches(r, query)]
    if "sort_by" in query:
        # sorted стабилен, reverse=True тоже сохраняет порядок равных элементов
        result = sorted(result, key=lambda r: r[query["sort_by"]],
                        reverse=query.get("order", "asc") == "desc")
    if "limit" in query:
        result = result[:query["limit"]]
    return {"query": query, "matches": result}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    if isinstance(queries, dict):
        queries = [queries]
    return [run_query(db, q) for q in queries]