# LSH Band Matcher

A `nanoagent.plugin/v0001` plugin, created by `nanoagent plugin new` with the
structure of NanoAgent's reference plugin,
[arxiv-source](https://github.com/zeyuyang8/arxiv-source).

## Tools

| Tool | Does | Code |
|---|---|---|
| `match_bands` | Cuts each MinHash signature into `bands` bands of `rows` entries, hashes every band to a bucket ID, and returns the documents that share a bucket with the query signature in at least one band | `src/plugin/bands.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `find-lsh-candidates` | Finds the documents that collide with a query signature | `agent`, with `match_bands` |

Every signature, the query's included, must have exactly `bands * rows`
entries. Band `j` is entries `j * rows` up to `(j + 1) * rows`, and its bucket
ID is the first 16 hex digits of the SHA-256 of `"<j>|<v1>,<v2>,..."`. The band
number is part of the hash, so a bucket in one band never equals a bucket in
another. A document collides with the query when its bucket equals the query's
in the same band. A candidate pair is `(query, doc_id)` with the list of bands
that collided; pairs come with the most shared bands first and ties by
`doc_id`. No collisions is a valid answer: the list is empty.

Documents need distinct, non-empty ids. A signature of the wrong length, or
`bands` or `rows` below 1, is an error.

`verifier/lsh.py` needs nothing but `hashlib`, so it recomputes every bucket
ID and the full list of candidate pairs from the task's arguments and
compares them with the submitted output; the task has no reference tool.
Input limits are 1 to 64 bands, 1 to 64 rows, and at most 1000 documents.

## Layout

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs, never values
├── src/plugin/      # the MCP server: __main__.py, its IMPLEMENTATIONS, and the plugin's own modules
├── tests/
├── ui/              # how the page draws the outputs: renderers.js and renderers.css
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
```

NanoAgent passes the folder the plugin may write to as `NANOAGENT_WORKSPACE`.
This plugin writes nothing there.
