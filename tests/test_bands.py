import hashlib
from pathlib import Path

import pytest

from contract import DocumentSignature, MatchInput
from plugin import match_bands


def docs(**signatures):
    return [DocumentSignature(doc_id=name, signature=signature) for name, signature in signatures.items()]


def run(documents, query, bands, rows):
    return match_bands(MatchInput(documents=documents, query=query, bands=bands, rows=rows), Path("."))


def digest(band, values):
    return hashlib.sha256(f"{band}|{','.join(map(str, values))}".encode()).hexdigest()[:16]


def test_bucket_ids_hash_each_band_of_rows():
    made = run(docs(a=[1, 2, 3, 4]), [1, 2, 9, 9], 2, 2)
    assert made.query_buckets == [digest(0, [1, 2]), digest(1, [9, 9])]
    assert made.documents[0].buckets == [digest(0, [1, 2]), digest(1, [3, 4])]


def test_a_document_is_a_candidate_when_one_band_matches():
    made = run(docs(a=[1, 2, 3, 4], b=[7, 7, 3, 4], c=[5, 5, 5, 5]), [1, 2, 3, 4], 2, 2)
    assert [(p.doc_id, p.bands) for p in made.pairs] == [("a", [0, 1]), ("b", [1])]


def test_equal_buckets_in_different_bands_do_not_collide():
    made = run(docs(a=[1, 2, 0, 0]), [0, 0, 1, 2], 2, 2)
    assert made.pairs == []


def test_a_partial_band_match_is_not_a_collision():
    assert run(docs(a=[1, 2, 3, 4]), [1, 9, 3, 9], 2, 2).pairs == []


def test_pairs_sort_by_shared_bands_then_doc_id():
    documents = docs(z=[1, 1, 1, 1], b=[1, 1, 0, 0], a=[1, 1, 0, 0])
    made = run(documents, [1, 1, 1, 1], 2, 2)
    assert [p.doc_id for p in made.pairs] == ["z", "a", "b"]


def test_no_documents_gives_no_pairs():
    made = run([], [1, 2], 1, 2)
    assert made.pairs == [] and made.documents == [] and len(made.query_buckets) == 1


def test_one_band_of_one_row_is_a_boundary():
    made = run(docs(a=[5], b=[6]), [5], 1, 1)
    assert [(p.doc_id, p.bands) for p in made.pairs] == [("a", [0])]


def test_identical_signatures_collide_in_every_band():
    signature = list(range(12))
    made = run(docs(same=signature), signature, 4, 3)
    assert made.pairs[0].bands == [0, 1, 2, 3]


def test_more_rows_make_collisions_rarer():
    near = [1, 2, 3, 4, 5, 6, 7, 8]
    other = [1, 2, 3, 4, 5, 6, 0, 0]
    assert len(run(docs(a=other), near, 4, 2).pairs[0].bands) == 3
    assert run(docs(a=other), near, 1, 8).pairs == []


@pytest.mark.parametrize(("bands", "rows"), [(0, 2), (2, 0), (-1, 2)])
def test_bands_and_rows_below_one_are_rejected(bands, rows):
    with pytest.raises(ValueError, match="at least 1"):
        run(docs(a=[1, 2]), [1, 2], bands, rows)


def test_a_signature_of_the_wrong_length_is_rejected():
    with pytest.raises(ValueError, match="expected bands \\* rows = 4"):
        run(docs(a=[1, 2, 3]), [1, 2, 3, 4], 2, 2)
    with pytest.raises(ValueError, match="query has 3"):
        run(docs(a=[1, 2, 3, 4]), [1, 2, 3], 2, 2)


def test_duplicate_doc_ids_are_rejected():
    documents = [DocumentSignature(doc_id="a", signature=[1, 2]), DocumentSignature(doc_id="a", signature=[3, 4])]
    with pytest.raises(ValueError, match="distinct"):
        run(documents, [1, 2], 1, 2)
