import argparse
import json
import logging
import os
import sys
import time

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB038"
FIRST_NAME = "Huseyn"
LAST_NAME = "Jamilzade"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="flight_parser.py",
                                description="Flight schedule parser and query tool")
    p.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    p.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    p.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    p.add_argument("-a", metavar="FILE", help="airport list file (required with -i/-d)")
    p.add_argument("-o", metavar="FILE", help="output JSON database path (default: db.json)")
    p.add_argument("-q", metavar="FILE", help="JSON file with queries")
    p.add_argument("-r", metavar="FOLDER", help="folder for the response file")
    return p


def _write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_log(log_path: str, errors: list[str]) -> None:
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    try:
        for msg in errors:
            logger.warning(msg)
    finally:
        logger.removeHandler(handler)
        handler.close()


def _collect_csv(args) -> list[str]:
    if args.i:
        if not os.path.isfile(args.i):
            raise OSError(f"file not found: {args.i}")
        return [args.i]
    if not os.path.isdir(args.d):
        raise OSError(f"folder not found: {args.d}")
    names = sorted(n for n in os.listdir(args.d)
                   if n.endswith(".csv") and os.path.isfile(os.path.join(args.d, n)))
    if not names:
        raise OSError(f"no .csv files in folder: {args.d}")
    return [os.path.join(args.d, n) for n in names]


def _run(args, parser) -> int:
    sources = [x for x in (args.i, args.d, args.j) if x is not None]
    if len(sources) == 0:
        parser.error("one of -i, -d, -j is required")
    if len(sources) > 1:
        parser.error("only one of -i, -d, -j is allowed")
    if args.j is None and args.a is None:
        parser.error("-a is required with -i and -d")
    if args.j is not None and args.o is not None:
        parser.error("-o cannot be used with -j")

    try:
        if args.j is not None:
            with open(args.j, encoding="utf-8") as f:
                db = json.load(f)
            if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
                raise ValueError("database must be a JSON array of objects")
        else:
            airports = load_airports(args.a)
            db, errors = parse_files(_collect_csv(args), airports)
            out = args.o or "db.json"
            _write_json(out, db)
            log_path = os.path.join(os.path.dirname(os.path.abspath(out)), "errors.log")
            _write_log(log_path, errors)

        if args.q is not None:
            with open(args.q, encoding="utf-8") as f:
                queries = json.load(f)
            if not isinstance(queries, (dict, list)):
                raise ValueError("query file must contain an object or an array")
            response = run_queries(db, queries)
            name = "response_{}_{}_{}_{}.json".format(
                STUDENT_ID, FIRST_NAME, LAST_NAME, time.strftime("%Y%m%d_%H%M"))
            _write_json(os.path.join(args.r or ".", name), response)
    except (OSError, ValueError, RecursionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        return _run(args, parser)
    except SystemExit as e:
        # argparse завершает через SystemExit - превращаем в код возврата
        return e.code if isinstance(e.code, int) else 2


if __name__ == "__main__":
    sys.exit(main())