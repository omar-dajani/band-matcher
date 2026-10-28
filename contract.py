from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    MATCH_BANDS = "match_bands"


class Task(Enum):
    FIND_LSH_CANDIDATES = "find-lsh-candidates"


@dataclass
class DocumentSignature(Output):
    doc_id: Annotated[str, "Unique name of the document"]
    signature: Annotated[list[int], "The document's MinHash signature, exactly bands * rows entries"]


@dataclass
class MatchInput(Output):
    documents: Annotated[list[DocumentSignature], "The indexed documents, each with a distinct doc_id"]
    query: Annotated[list[int], "The query's MinHash signature, the same length as every document's"]
    bands: Annotated[int, "b: how many bands each signature is cut into"]
    rows: Annotated[int, "r: how many consecutive signature entries make one band"]


@dataclass
class DocumentBuckets(Output):
    doc_id: Annotated[str, "The document's id"]
    buckets: Annotated[list[str], "The document's bucket ID in each band, band 0 first"]


@dataclass
class CandidatePair(Output):
    doc_id: Annotated[str, "A document that shares a bucket with the query in at least one band"]
    bands: Annotated[list[int], "The bands, in increasing order, in which the document and the query share a bucket"]


@dataclass
class MatchOutput(Output):
    query_buckets: Annotated[list[str], "The query's bucket ID in each band, band 0 first"]
    documents: Annotated[list[DocumentBuckets], "Every document's bucket IDs, in the input order"]
    pairs: Annotated[list[CandidatePair], "Candidate pairs (query, doc_id), most shared bands first, ties by doc_id"]


TOOLS = {
    Tool.MATCH_BANDS: (MatchInput, MatchOutput),
}
TASKS = {
    Task.FIND_LSH_CANDIDATES: (MatchInput, MatchOutput),
}
