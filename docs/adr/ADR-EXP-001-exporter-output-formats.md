\# ADR-EXP-001: Exporter Output Formats for assistant/APP



\## Status

\*\*Accepted\*\*



\## Date

2026-05-14



\## Context



The assistant/APP is an experimental, sandboxed system governed by ADR-00X, which mandates a strict build order:



1\. Summarizer (Phase A — frozen)

2\. Exporter (Phase B — current)

3\. Tool Orchestration (Phase C — deferred)



With the summarizer contract frozen, the next step is to design the \*\*Exporter\*\*, whose responsibility is to move summarizer output into durable artifacts \*\*without altering semantics\*\*.



A decision is required regarding:

\- Which output formats are supported in Phase B

\- How to balance auditability, simplicity, and future extensibility

\- How to avoid introducing unnecessary dependencies or risk during early promotion stages



\## Decision



During Phase B, the assistant/APP Exporter SHALL support \*\*only the following output formats\*\*:



1\. \*\*JSON\*\*

2\. \*\*Markdown\*\*



No other formats (including PDF, HTML, or DOCX) are permitted in Phase B.



\## Rationale



\### Why JSON



\- JSON preserves the summarizer schema \*\*losslessly\*\*

\- Ideal for testing, diffing, and automated inspection

\- Enables deterministic, machine-readable artifacts

\- Lowest possible risk of semantic distortion



JSON serves as the \*\*canonical exported representation\*\*.



\### Why Markdown



\- Human-readable and review-friendly

\- Easy to audit manually

\- Requires no external rendering libraries

\- Naturally maps to structured summaries (title, bullets, sections)



Markdown serves as the \*\*human-facing representation\*\*.



\### Why NOT PDF (or other rich formats) in Phase B



\- Introduces heavy dependencies and rendering variability

\- Increases non-determinism (fonts, layout engines)

\- Complicates testing and diffing

\- Raises certification and audit costs



These formats provide usability benefits but \*\*no semantic benefit\*\* at this stage.



\## Constraints



The Exporter is subject to the following constraints:



\- Exporters MUST NOT:

&#x20; - Modify, reorder, or reinterpret summarizer content

&#x20; - Perform tool calls or LLM calls

&#x20; - Read from or write to AIv2 memory

&#x20; - Write outside the `assistant/APP/output/` directory



\- Exporters MUST:

&#x20; - Treat summarizer output as immutable input

&#x20; - Stamp all outputs with required metadata

&#x20; - Produce deterministic output for identical input



\## Metadata Requirements



All exported artifacts MUST include:



\- `generated\_by: assistant/APP`

\- `schema\_version` (matching summarizer contract)

\- Timestamp (ISO 8601)



This applies to both JSON and Markdown outputs.



\## Alternatives Considered



\### PDF Export in Phase B

Rejected due to increased complexity, non-determinism, and audit cost.



\### Single-Format Export (JSON only)

Rejected to preserve human review usability during development and evaluation.



\## Consequences



\### Positive



\- Minimal dependency footprint

\- High auditability and testability

\- Clear semantic boundary between summarization and presentation

\- Smooth path to AIv2 promotion review



\### Negative



\- No print-ready or end-user polished formats initially

\- PDF or rich exports deferred to a later phase



These tradeoffs are intentional and acceptable.



\## Follow-Ups



\- PDF or other rich formats may be introduced in \*\*Phase C or later\*\*

\- Any new export format requires:

&#x20; - A new ADR

&#x20; - Exporter test expansion

&#x20; - Re-evaluation of promotion risk



\## Related ADRs



\- ADR-00X: Prioritization Order for assistant/APP Components

\- Phase A Completion Checklist (Summarizer Freeze)



