#!/usr/bin/env python3
"""
failure_log_viewer.py
─────────────────────
CLI dashboard for AnimAI Studio failure log analysis.

Usage
─────
  python failure_log_viewer.py              # show summary + last 10 failures
  python failure_log_viewer.py --all        # show all failures
  python failure_log_viewer.py --tags       # tag frequency table
  python failure_log_viewer.py --types      # failure type breakdown
  python failure_log_viewer.py --id <id>    # inspect a specific bundle (code + error)
  python failure_log_viewer.py --filter bookmark_error   # filter by failure_type
  python failure_log_viewer.py --export failures.json    # export index to JSON
  python failure_log_viewer.py --log-now   # manually log the current last_failed_* pair

Examples
────────
  python failure_log_viewer.py --tags
  python failure_log_viewer.py --filter bookmark_error
  python failure_log_viewer.py --id 20260331_164500_bookmark_error
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Make sure we can import from the project root
sys.path.insert(0, os.path.dirname(__file__))

from agent.failure_logger import (
    load_index,
    load_bundle,
    tag_summary,
    failure_type_summary,
    log_failure,
    FAILURE_LOG_DIR,
)

# ── ANSI colours ──────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

def c(text, color): return f"{color}{text}{RESET}"


# ── Formatters ────────────────────────────────────────────────────────────────

def _fmt_entry(entry: dict, idx: int) -> str:
    ft   = entry.get("failure_type", "?")
    ts   = entry.get("timestamp", "?")[:19].replace("T", " ")
    qry  = (entry.get("query") or "(no query)")[:60]
    tags = ", ".join(entry.get("tags", []))
    att  = entry.get("attempt", "?")
    cln  = entry.get("code_lines", "?")

    color = RED if "error" in ft else YELLOW if ft == "timeout" else CYAN
    return (
        f"  {c(str(idx).rjust(4), DIM)}  {c(ts, DIM)}  "
        f"{c(ft.ljust(20), color)}  "
        f"attempt={att}  lines={cln}\n"
        f"         query: {c(qry, BOLD)}\n"
        f"         tags:  {c(tags or '(none)', DIM)}\n"
        f"         id:    {c(entry.get('id', '?'), DIM)}"
    )


def _table(data: dict, header: str, col1: str = "KEY", col2: str = "COUNT") -> str:
    if not data:
        return f"  (no data)"
    col_w = max(len(k) for k in data) + 2
    lines = [f"  {c(col1.ljust(col_w), BOLD)}  {c(col2, BOLD)}"]
    for k, v in data.items():
        bar = "█" * min(v, 40)
        lines.append(f"  {k.ljust(col_w)}  {c(str(v).rjust(4), YELLOW)}  {c(bar, GREEN)}")
    return "\n".join(lines)


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_summary(entries: list[dict], n: int = 10):
    total = len(entries)
    print(f"\n{c('AnimAI Failure Log Summary', BOLD)}  ({c(str(total), YELLOW)} total failures)")
    print(f"  Storage: {os.path.abspath(FAILURE_LOG_DIR)}\n")

    if not entries:
        print(c("  No failures logged yet.", GREEN))
        return

    shown = entries[:n]
    print(c(f"  Latest {len(shown)} failures:", CYAN))
    for i, e in enumerate(shown, 1):
        print(_fmt_entry(e, i))
        print()

    if total > n:
        print(c(f"  ... and {total - n} more. Use --all to see everything.", DIM))


def cmd_tags():
    ts = tag_summary()
    print(f"\n{c('Tag Frequency', BOLD)}\n")
    print(_table(ts, header="Tag Frequency", col1="TAG", col2="COUNT"))
    print()


def cmd_types():
    ft = failure_type_summary()
    print(f"\n{c('Failure Type Breakdown', BOLD)}\n")
    print(_table(ft, header="Failure Types", col1="TYPE", col2="COUNT"))
    print()


def cmd_inspect(bundle_id: str):
    b = load_bundle(bundle_id)
    if not b:
        print(c(f"\n  Bundle '{bundle_id}' not found in {FAILURE_LOG_DIR}", RED))
        return

    print(f"\n{c('Bundle: ' + bundle_id, BOLD)}")
    print(f"  timestamp:    {b.get('timestamp')}")
    print(f"  failure_type: {c(b.get('failure_type', '?'), YELLOW)}")
    print(f"  query:        {b.get('query') or '(none)'}")
    print(f"  attempt:      {b.get('attempt')}")
    print(f"  tags:         {', '.join(b.get('tags', []))}")
    print(f"  code_lines:   {b.get('code_lines')}")

    print(f"\n{c('─── ERROR ───', RED)}")
    err = (b.get("error") or "").strip()
    # Show only first 60 lines of error to keep terminal sane
    for line in err.splitlines()[:60]:
        print(f"  {line}")
    if len(err.splitlines()) > 60:
        print(c(f"  ... ({len(err.splitlines()) - 60} more lines truncated)", DIM))

    print(f"\n{c('─── CODE (first 50 lines) ───', CYAN)}")
    code = (b.get("code") or "").strip()
    for i, line in enumerate(code.splitlines()[:50], 1):
        print(f"  {c(str(i).rjust(4), DIM)}  {line}")
    if len(code.splitlines()) > 50:
        print(c(f"  ... ({len(code.splitlines()) - 50} more lines). Full code in bundle JSON.", DIM))
    print()


def cmd_filter(failure_type: str, entries: list[dict]):
    filtered = [e for e in entries if e.get("failure_type") == failure_type]
    print(f"\n{c(f'Failures of type: {failure_type}', BOLD)}  ({len(filtered)} found)\n")
    if not filtered:
        print(c("  None found.", GREEN))
        return
    for i, e in enumerate(filtered, 1):
        print(_fmt_entry(e, i))
        print()


def cmd_export(path: str, entries: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(c(f"\n  Exported {len(entries)} entries → {os.path.abspath(path)}", GREEN))


def cmd_log_now():
    """Manually import the current last_failed_* pair into the log."""
    scene_path = os.path.join("outputs", "last_failed_scene.py")
    log_path   = os.path.join("outputs", "last_failed_log.txt")

    if not os.path.exists(scene_path):
        print(c(f"\n  {scene_path} does not exist.", RED))
        return
    if not os.path.exists(log_path):
        print(c(f"\n  {log_path} does not exist.", RED))
        return

    with open(scene_path, encoding="utf-8") as f:
        code = f.read()
    with open(log_path, encoding="utf-8") as f:
        error = f.read()

    err_lower = error.lower()
    if "word boundaries are required" in err_lower:
        ft = "bookmark_error"
    elif "no video file was generated" in err_lower:
        ft = "no_video"
    elif "syntaxerror" in err_lower:
        ft = "syntax_error"
    elif "attributeerror" in err_lower:
        ft = "attribute_error"
    elif "nameerror" in err_lower:
        ft = "name_error"
    elif "typeerror" in err_lower:
        ft = "type_error"
    else:
        ft = "runtime_error"

    bundle_path = log_failure(error=error, code=code, failure_type=ft)
    print(c(f"\n  ✅ Logged current failure → {bundle_path}", GREEN))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AnimAI Studio failure log viewer and analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--all",      action="store_true",  help="Show all failures (not just last 10)")
    parser.add_argument("--tags",     action="store_true",  help="Show tag frequency table")
    parser.add_argument("--types",    action="store_true",  help="Show failure type breakdown")
    parser.add_argument("--id",       metavar="BUNDLE_ID",  help="Inspect a specific bundle by ID")
    parser.add_argument("--filter",   metavar="TYPE",       help="Filter failures by failure_type")
    parser.add_argument("--export",   metavar="FILE",       help="Export index to a JSON file")
    parser.add_argument("--log-now",  action="store_true",  help="Import last_failed_* files into the log")
    args = parser.parse_args()

    entries = load_index()

    if args.log_now:
        cmd_log_now()
        return

    if args.id:
        cmd_inspect(args.id)
        return

    if args.tags:
        cmd_tags()
        return

    if args.types:
        cmd_types()
        return

    if args.filter:
        cmd_filter(args.filter, entries)
        return

    if args.export:
        cmd_export(args.export, entries)
        return

    # Default: summary
    n = len(entries) if args.all else 10
    cmd_summary(entries, n=n)


if __name__ == "__main__":
    main()
