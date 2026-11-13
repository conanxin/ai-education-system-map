#!/usr/bin/env python3
"""Inspect and act on docs/data/review-queue.json (stdlib only).

  python3 scripts/review_queue.py list [--all]
  python3 scripts/review_queue.py restore <index-or-url-fragment> [...]
  python3 scripts/review_queue.py dismiss <index-or-url-fragment> [...]

`restore` moves an entry into papers.json (tagged "manual-review" so the
relevance gate keeps it) and rebuilds dashboard-summary.json. `dismiss`
keeps the entry in the queue with status "dismissed" so the weekly watcher
never queues it again. Indexes are the ones printed by `list --all`.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "weekly_ai_education_watch", Path(__file__).with_name("weekly_ai_education_watch.py"))
watch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(watch)

OPEN_STATUSES = ("rejected_by_filter", "quarantined_from_papers")


def _select(items: list[dict], selector: str) -> list[int]:
    if selector.isdigit():
        index = int(selector)
        return [index] if 0 <= index < len(items) else []
    needle = selector.lower()
    return [i for i, x in enumerate(items)
            if needle in str(x.get("url", "")).lower()
            or needle in str(x.get("title", "")).lower()]


def cmd_list(queue: dict, show_all: bool) -> int:
    shown = 0
    for i, x in enumerate(queue["items"]):
        if not show_all and x.get("status") not in OPEN_STATUSES:
            continue
        shown += 1
        print(f"[{i:3}] {x.get('status', ''):24} {x.get('reason', ''):22} "
              f"{str(x.get('title', ''))[:90]}\n      {x.get('url', '')}")
    print(f"{shown} shown / {len(queue['items'])} total")
    return 0


def cmd_restore(data_dir: Path, queue: dict, selectors: list[str]) -> int:
    papers_path = data_dir / "papers.json"
    papers = watch.load_json(papers_path)
    keys = {watch.paper_key(p.get("url", "")) for p in papers}
    picked = sorted({i for s in selectors for i in _select(queue["items"], s)})
    if not picked:
        print("no matching queue entries", file=sys.stderr)
        return 1
    restored = 0
    for i in picked:
        entry = queue["items"][i]
        key = watch.paper_key(entry.get("url", ""))
        if entry.get("status") == "restored" or key in keys:
            print(f"skip (already a paper): {entry.get('title', '')[:80]}")
            entry["status"] = "restored"
            continue
        now = watch.now_iso()
        record = dict(entry.get("record") or {
            "id": entry["url"], "title": entry["title"], "url": entry["url"],
            "institution": "", "summary": "", "tags": [],
            "source_id": entry.get("source_id", ""),
            "year": watch._guess_year(entry["url"]), "first_seen": now,
        })
        record["key"] = key
        record["record_type"] = "scholarly_paper"
        record["tags"] = [*record.get("tags", []), "manual-review"]
        record["last_seen"] = now
        papers.append(record)
        keys.add(key)
        entry["status"] = "restored"
        entry["resolved_at"] = now
        restored += 1
        print(f"restored: {record['title'][:80]}")
    queue["updated_at"] = watch.now_iso()
    watch.save_json(papers_path, papers)
    watch.save_json(data_dir / "review-queue.json", queue)
    if restored:
        ok, _, error = watch.rebuild_dashboard_summary(data_dir.parent.parent, data_dir)
        print("dashboard summary rebuilt" if ok else f"summary rebuild failed: {error}")
    return 0


def cmd_dismiss(data_dir: Path, queue: dict, selectors: list[str]) -> int:
    picked = sorted({i for s in selectors for i in _select(queue["items"], s)})
    if not picked:
        print("no matching queue entries", file=sys.stderr)
        return 1
    changed = False
    for i in picked:
        entry = queue["items"][i]
        if entry.get("status") in OPEN_STATUSES:
            entry["status"] = "dismissed"
            entry["resolved_at"] = watch.now_iso()
            print(f"dismissed: {entry.get('title', '')[:80]}")
            changed = True
    if changed:
        queue["updated_at"] = watch.now_iso()
        watch.save_json(data_dir / "review-queue.json", queue)
        ok, _, error = watch.rebuild_dashboard_summary(data_dir.parent.parent, data_dir)
        if not ok:
            print(f"summary rebuild failed: {error}", file=sys.stderr)
            return 1
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", type=Path, default=ROOT / "docs" / "data")
    sub = ap.add_subparsers(dest="command", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--all", action="store_true", help="include restored/dismissed entries")
    for name in ("restore", "dismiss"):
        sp = sub.add_parser(name)
        sp.add_argument("selectors", nargs="+")
    args = ap.parse_args(argv)
    queue = watch.load_json(args.data_dir / "review-queue.json")
    if not isinstance(queue, dict) or not isinstance(queue.get("items"), list):
        print("review-queue.json is missing or malformed", file=sys.stderr)
        return 1
    if args.command == "list":
        return cmd_list(queue, args.all)
    if args.command == "restore":
        return cmd_restore(args.data_dir, queue, args.selectors)
    return cmd_dismiss(args.data_dir, queue, args.selectors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
