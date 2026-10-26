#!/usr/bin/env python3
"""P42: verifiable, non-destructive classification of the legacy mixed papers list.

Preserve every legacy record's content, ID, and source in a typed collection.
Never silently classify unknown untagged records as publications.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

NONPAPER_TAGS = {
    "official-page": "official_page",
    "person-source": "person_profile",
    "conference-venue": "venue_or_journal",
}
SCHOLARLY_DOMAINS = {
    "oulurepo.oulu.fi", "bera-journals.onlinelibrary.wiley.com",
    "learning-analytics.info", "aclanthology.org",
    "genai-personalization.github.io", "arxiv.org", "www.arxiv.org",
}
EXPECTED_ARCHIVE_ID_PREFIXES = (
    "https://hai.stanford.edu/assets/files/hai-stanford-accelerator-for-learning-rfi-response",
    "https://hai.stanford.edu/news/data-centered-approach-education-ai",
)
ALLOWED_REFERENCE_KINDS = set(NONPAPER_TAGS.values()) | {"policy_document", "news_article"}


def record_kind(record: dict) -> str:
    tags = set(record.get("tags") or [])
    if record.get("record_type")=="scholarly_paper":
        # A future item has already passed the weekly type checker; allow
        # verified DOI/OpenAlex IDs during idempotent re-validation.
        url=urlsplit(str(record.get("url") or ""))
        host=url.hostname
        allowed=SCHOLARLY_DOMAINS | {
            "doi.org","www.doi.org","openalex.org","openreview.net"}
        if (url.scheme!="https" or host not in allowed or
                tags.intersection(NONPAPER_TAGS)):
            raise ValueError("P42 typed paper conflicts with trusted academic URL/tags")
        return "scholarly_paper"
    known = [kind for tag,kind in NONPAPER_TAGS.items() if tag in tags]
    if len(known)>1:
        raise ValueError("Conflicting non-paper tags: "+str(record.get("id")))
    if known:
        return known[0]
    url = str(record.get("url") or "").strip()
    if url.startswith(EXPECTED_ARCHIVE_ID_PREFIXES[0]):
        return "policy_document"
    if url == EXPECTED_ARCHIVE_ID_PREFIXES[1]:
        return "news_article"
    hostname=urlsplit(url).hostname
    if hostname in SCHOLARLY_DOMAINS:
        return "scholarly_paper"
    raise ValueError(f"Unreviewed ambiguous legacy record: {record.get('id')!r}")


def partition(records: list[dict]) -> tuple[list[dict],list[dict]]:
    seen=set()
    papers=[]
    references=[]
    for entry in records:
        if not isinstance(entry,dict) or not entry.get("id") or not entry.get("title"):
            raise ValueError("Malformed research entry")
        ident=str(entry["id"])
        if ident in seen:raise ValueError("Duplicate legacy ID "+ident)
        seen.add(ident)
        kind=record_kind(entry)
        obj=dict(entry)
        obj["record_type"]=kind
        (papers if kind=="scholarly_paper" else references).append(obj)
    assert len(papers)+len(references)==len(records)
    return papers,references


def run(data_dir:Path, dry_run=False) -> dict:
    src=data_dir/"papers.json"
    dest=data_dir/"research-entities.json"
    audit=data_dir/"research-migration.json"
    raw=src.read_bytes()
    records=json.loads(raw)
    if dest.exists():
        current_papers,current_entities=partition(records)
        actual=json.loads(dest.read_text())
        if current_entities or len(current_papers)!=len(records):
            raise RuntimeError("Mixed records remain after destination already exists")
        assert all(x["record_type"]=="scholarly_paper" for x in records)
        assert all(record_kind(x) in ALLOWED_REFERENCE_KINDS for x in actual)
        assert len({str(x["id"]) for x in records+actual})==len(records)+len(actual)
        return {"status":"ALREADY_MIGRATED","papers":len(records),"references":len(actual)}
    papers,entities=partition(records)
    assert len(records)==41 and len(papers)==12 and len(entities)==29,(
        len(records),len(papers),len(entities))
    counts={k:sum(x["record_type"]==k for x in papers+entities)
            for k in sorted(set(x["record_type"] for x in papers+entities))}
    assert counts=={
        "scholarly_paper":12,
        "official_page":9,
        "person_profile":12,
        "venue_or_journal":6,
        "policy_document":1,
        "news_article":1,
    },counts
    proof={
        "migration":"P42_AI_EDUCATION_TYPED_RESEARCH_RECORDS_V1",
        "status":"PREVIEW" if dry_run else "MIGRATED",
        "input_record_count":len(records),
        "input_sha256":hashlib.sha256(raw).hexdigest(),
        "typed_papers":len(papers),"typed_references":len(entities),
        "reference_kinds":counts,
        "full_legacy_fields_preserved":True,
        "original_record_ids_preserved":True,
        "all_records_disjoint_by_id":True,
        "source_backup":"~/.local/state/hermes-upgrade-preflight/P42-backups/ai-before-record-migration/papers.json",
        "new_documents":[str(dest.relative_to(data_dir.parent.parent)),str(audit.relative_to(data_dir.parent.parent))]
    }
    if not dry_run:
        src.write_text(json.dumps(papers,ensure_ascii=False,indent=2)+"\n")
        dest.write_text(json.dumps(entities,ensure_ascii=False,indent=2)+"\n")
        audit.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n")
        # Ensure exact legacy records remain reconstructable without metadata
        # loss when deleting only the P42 classification field.
        reconstructed=papers+entities
        original_by_id={str(x["id"]):x for x in records}
        for record in reconstructed:
            back=dict(record);back.pop("record_type")
            assert back==original_by_id[str(record["id"])]
    return proof


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",type=Path,required=True)
    ap.add_argument("--dry-run",action="store_true")
    a=ap.parse_args()
    print(json.dumps(run(a.data_dir,a.dry_run),indent=2,ensure_ascii=False))
