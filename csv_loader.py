import csv
import os

from validator import to_record, validate_row


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()  # (flight_id, departure) по всем файлам

    for path in paths:
        name = os.path.basename(path)
        # newline=None: \n, \r\n и \r приводятся к \n
        with open(path, encoding="utf-8-sig", newline=None) as f:
            for line_no, line in enumerate(f, start=1):
                if line_no == 1:
                    continue
                text = line.rstrip("\r\n")
                if not text.strip() or text.lstrip().startswith("#"):
                    continue
                try:
                    fields = next(csv.reader([text]))
                except csv.Error:
                    fields = [text]
                code = validate_row(fields, airports)
                if code is None:
                    rec = to_record(fields)
                    key = (rec["flight_id"], rec["departure_datetime"])
                    if key in seen:
                        code = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(key)
                        records.append(rec)
                if code is not None:
                    errors.append(f"{name}:{line_no}: {code} | {text.strip()}")
    return records, errors