# Session 009 Takeaways

**Date:** 2026-01-04

---

## Key Deliverables

- **CR-009 completed:** SOP-003 (Deviation Management) and SOP-004 (Document Execution) now EFFECTIVE
- **RS-001 restructured:** Requirements now have verification types, ready for RTM integration
- **Three conceptual frameworks documented** for future implementation

---

## Architectural Insights

### 1. "The agent doesn't learn. The QMS learns."

When agents encounter edge cases or discover gaps, the insight gets codified in SOPs via INVs/CRs — not stored in agent memory. The QMS is the persistent memory. Agents are stateless executors; documents are durable state.

### 2. CAPAs are execution items, not documents

Significant simplification from traditional QMS. CAPAs exist only within INVs, numbered `INV-XYZ-CAPA-NNN`. This reduces document proliferation while maintaining full traceability. Child CRs must close before CAPA can close, which must happen before INV can close.

### 3. Two-category verification eliminates the middle ground

Everything is either:
- **Unit Test:** Automated, reproducible script
- **Qualitative Proof:** Intelligent analysis (AI, human, or both)

There's no "manual test execution" category — that's just an unautomated unit test waiting to be scripted. OQ may be retired; TPs become scripts.

### 4. Lead discretion + QA oversight

For judgment calls (e.g., "does this need an INV?"), we don't prescribe rigid classification schemes. Lead has discretion, QA provides the check. Agent judgment is explicitly acknowledged as integral to making the QMS work. Not everything can be codified.

### 5. No deferral — ever

The concept of "deferring" scope items was explicitly rejected. Either complete the item or document an exception via ER. Deferral is a recipe for losing track of important work. Removed from all SOPs and CR templates.

### 6. Model C: Manifests as behavioral layer

- **SOPs define WHAT** must happen (policy, requirements)
- **Manifests define HOW** agents operationalize it (tools, sequence, response format)

Manifests don't duplicate SOP content; they translate requirements into agent behavior. This creates a natural testing boundary and keeps orchestration prompts minimal.

### 7. Source vs rendition for documents

- **Source:** Clean content in workspace during checkout
- **Rendition:** Polished document in QMS with auto-injected header/footer

Authors never maintain metadata manually. The QMS injects it from `.meta/` and `.audit/` at checkin. Checkout strips injected layers, returning clean source.

---

## Process Observations

### Full CR lifecycle executed autonomously

CR-009 went from draft to closed with minimal intervention:
- Pre-review, pre-approval
- Execution (both SOPs created, drafted, reviewed, approved to EFFECTIVE)
- Post-review, post-approval, closure

QA was spawned/resumed as needed. The recursive governance loop is functional.

### Session recovery is valuable

The chronicle capture hook failed for one session, but the raw transcript persisted in Claude Code's data directory. Recovery was possible by parsing the JSONL directly. Session chronicles are worth preserving.

---

## Quotes Worth Remembering

> "We must never defer. Deferring tasks is a recipe for losing track of important items."

> "The judgment and discernment of all agents (human and AI) is integral to making the QMS function well. Not every scenario can be codified."

> "If a test can be scripted, it's a unit test. If it requires judgment, it's a qualitative proof."

---

**End of Takeaways**
