import hashlib
from pathlib import Path

from contract import CandidatePair, DocumentBuckets, MatchInput, MatchOutput


def bucket_id(band: int, rows: list[int]) -> str:
    text = f"{band}|" + ",".join(str(value) for value in rows)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def bucket_ids(signature: list[int], bands: int, rows: int) -> list[str]:
    return [bucket_id(band, signature[band * rows : (band + 1) * rows]) for band in range(bands)]


def match_bands(given: MatchInput, workspace: Path) -> MatchOutput:
    if given.bands < 1 or given.rows < 1:
        raise ValueError("bands and rows must be at least 1")
    width = given.bands * given.rows
    ids = [document.doc_id for document in given.documents]
    if len(set(ids)) != len(ids):
        raise ValueError("doc_id values must be distinct")
    for name, signature in [("query", given.query)] + [(d.doc_id, d.signature) for d in given.documents]:
        if len(signature) != width:
            raise ValueError(f"{name} has {len(signature)} entries, expected bands * rows = {width}")
    query = bucket_ids(given.query, given.bands, given.rows)
    documents = [
        DocumentBuckets(doc_id=d.doc_id, buckets=bucket_ids(d.signature, given.bands, given.rows))
        for d in given.documents
    ]
    pairs = []
    for document in documents:
        shared = [band for band, (ours, theirs) in enumerate(zip(query, document.buckets)) if ours == theirs]
        if shared:
            pairs.append(CandidatePair(doc_id=document.doc_id, bands=shared))
    pairs.sort(key=lambda pair: (-len(pair.bands), pair.doc_id))
    return MatchOutput(query_buckets=query, documents=documents, pairs=pairs)
