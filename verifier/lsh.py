import hashlib

from .checks import result

MOST_BANDS = 64
MOST_ROWS = 64
MOST_DOCUMENTS = 1000


def buckets(signature, bands, rows):
    ids = []
    for band in range(bands):
        chunk = ",".join(map(str, signature[band * rows :][:rows]))
        ids.append(hashlib.sha256(f"{band}|{chunk}".encode()).hexdigest()[:16])
    return ids


def verify_input(value):
    if not 1 <= value.bands <= MOST_BANDS:
        return result(False, f"bands must be between 1 and {MOST_BANDS}")
    if not 1 <= value.rows <= MOST_ROWS:
        return result(False, f"rows must be between 1 and {MOST_ROWS}")
    if len(value.documents) > MOST_DOCUMENTS:
        return result(False, f"at most {MOST_DOCUMENTS} documents are allowed")
    ids = [document.doc_id for document in value.documents]
    if any(not doc_id for doc_id in ids):
        return result(False, "doc_id must not be empty")
    if len(set(ids)) != len(ids):
        return result(False, "doc_id values must be distinct")
    width = value.bands * value.rows
    if len(value.query) != width:
        return result(False, f"query has {len(value.query)} entries, expected bands * rows = {width}")
    for document in value.documents:
        if len(document.signature) != width:
            return result(False, f"{document.doc_id} has {len(document.signature)} entries, expected {width}")
    return result(True, "input accepted")


def expected_output(value):
    query = buckets(value.query, value.bands, value.rows)
    table = {d.doc_id: buckets(d.signature, value.bands, value.rows) for d in value.documents}
    pairs = []
    for doc_id, ids in table.items():
        shared = [band for band in range(value.bands) if ids[band] == query[band]]
        if shared:
            pairs.append((doc_id, shared))
    pairs.sort(key=lambda pair: (-len(pair[1]), pair[0]))
    return query, table, pairs


def verify_output(input_value, output_value, workspace):
    problem = verify_input(input_value)
    if not problem["valid"]:
        return problem
    query, table, pairs = expected_output(input_value)
    if output_value.query_buckets != query:
        return result(False, "query_buckets are not the query's band buckets")
    if [d.doc_id for d in output_value.documents] != [d.doc_id for d in input_value.documents]:
        return result(False, "documents must list every input document, in the input order")
    for document in output_value.documents:
        if document.buckets != table[document.doc_id]:
            return result(False, f"buckets of {document.doc_id} are wrong")
    given = [(pair.doc_id, tuple(pair.bands)) for pair in output_value.pairs]
    wanted = [(doc_id, tuple(bands)) for doc_id, bands in pairs]
    if given != wanted:
        right = len(set(given) & set(wanted))
        score = right / max(len(given), len(wanted))
        missing = sorted({doc_id for doc_id, _ in wanted} - {doc_id for doc_id, _ in given})
        extra = sorted({doc_id for doc_id, _ in given} - {doc_id for doc_id, _ in wanted})
        return result(
            False, "candidate pairs are not the expected collisions", score=score, missing=missing, extra=extra
        )
    return result(True, "buckets and candidate pairs match the recomputation", candidates=len(pairs))


def verify_task(arguments, output, reference, workspace):
    return verify_output(arguments, output, workspace)
