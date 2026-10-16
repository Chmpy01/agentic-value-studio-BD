# 0002 — Research and discovery produces a layered knowledge graph

Status: accepted, 16 October 2026.

## Context

The studio could load a design pack but could not explain where that pack came from. The supplied
`cvs_twin_template` describes a discovery motion that starts with the industry, reads the customer's
own reporting, and only then maps value streams, functions and personas. We needed that motion to be
executable rather than a document, and we needed its output to be a knowledge graph the rest of the
studio can read.

The environment has no outbound network access, and the project rules forbid inventing evidence and
forbid presenting synthetic calculations as realised customer value. A research agent that quietly
fabricates analyst findings would breach both.

## Decision

**A local labelled corpus instead of retrieval.** `data/research/` holds three files: a source
register, an industry corpus and the template itself. Nothing is fetched at runtime and
`external_research_calls` is `false` in every generated pack. Each source declares a
`referenceType`: `repository-file` entries resolve to a real file in this repository, and
`synthetic-placeholder` entries are openly invented stand-ins so the pipeline can be built without
attributing claims to real organisations. A test asserts that every repository reference resolves.

**Evidence class decides validation status, not the author.** `statusByEvidenceType` in the template
maps each class to a validation status. Industry patterns map to `do_not_use_without_validation`,
public signals and user-provided statements to `hypothesis`, inference to `requires_discovery`.
Because the mapping is applied by code, a statement cannot be promoted by wording. A test asserts
that industry material never carries `validated`, and the upload validator rejects a register where
an inferred or pattern claim has been edited to `validated`.

**Absent evidence becomes a question.** Unknowns are first-class corpus entries. They enter the
evidence register with class `unknown`, become validation gates with an owner to confirm, and drive
the sequenced roadmap. The roadmap deliberately puts sponsor, baseline and data access before any
capability or portfolio conversation.

**Five fixed layers.** The graph is `industry_context → industry_value_stream →
customer_value_stream → function → persona`, with one relation per layer boundary (`scopes`,
`instantiated-as`, `operated-by`, `represented-by`). Keeping the shape fixed makes the view
predictable, makes the pack concept outline a true table of contents, and lets a test assert that no
edge crosses a layer boundary it should not and that no node is orphaned.

**Reuse the existing audit ledger.** Discovery runs are rows in the same `runs` and `events` tables
with `orchestrator='discovery'`, so they inherit trace ids, the SSE stream and the public run shape.
The workflow orchestrator refuses a discovery run with 409, and the discovery agent refuses a
workflow run, so the two cannot be stepped by the wrong engine. Customer input is stored in a
separate `discovery_inputs` table rather than squeezed into an existing column.

**Deterministic and content-hashed.** Each stage is a pure function of the corpus and the input, so
the pack can be rebuilt at any point in the run and compared. `discoveryHash` is a sha256 over the
canonical document, and `step` refuses to continue if the hash changes mid-run, which is the same
guard the workflow orchestrator applies to `intentHash`.

## Consequences

The discovery output is honest about its own weakness: roughly a sixth of the statements in a
generated pack rest on material already agreed in this repository, and the rest are patterns,
inferences or assumptions that the view labels as such. That is the intended result — the pack is a
structured set of questions, not a finding.

Replacing the placeholder corpus with real research is a data change, not a code change. The schema,
the classification rules and the graph assembly stay as they are; only `data/research/` moves.

A retrieval-backed version would need an egress allowlist, a cache with provenance capture, and a
human review step before a fetched claim enters the register. None of that is built here.
