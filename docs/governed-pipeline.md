# Follow the governed pipeline

Capability Lab's public checkpoint is best understood as two governed chains that meet at current state.

The first chain turns an external observation into evidence and capability evaluation.
The second turns governed evaluation history into current state, advisory progression, and a safe read projection.

## External observation → governed evaluation

```mermaid
flowchart TD
    O[PR12.0 ExternalObservationEnvelope] --> M[PR12.1 HUMAN-reviewed neutral EvidenceRecord]
    M --> P[PR12.2 interpretation proposal]
    P --> H[PR12.3 HUMAN terminal review + runtime admission]
    H --> C[PR12.4 deterministic CapabilityClaim]
    C --> E1[PR12.5 conservative evidence-level ClaimEvaluation]
    E1 --> POL[PR12.6–12.7 domain policy + HUMAN admission]
    POL --> U[PR12.8 complete candidate evidence universe]
    U --> D[PR12.9 complete dispositions]
    D --> L[PR12.10 lineage / dependence audit]
    L --> R[PR12.11 HUMAN requirement mapping]
    R --> E2[PR12.12 domain-sufficient directional ClaimEvaluation]
```

Several non-inference rules are deliberate:

- requirement mapping is not directional evidence selection;
- reliability is not a hidden threshold;
- shared lineage does not become positive independence;
- evidence count is not majority vote;
- a real support/contradiction conflict remains `MIXED / UNRESOLVED`.

The exact contracts live in the [reference map](reference/archive.md).

## Governed evaluation → current state

```mermaid
flowchart TD
    E[ClaimEvaluation history] --> P[PR11.3 immutable persistence]
    P --> C[PR11.4 complete evaluation portfolio]
    C --> D[PR11.5 complete-portfolio state derivation]
    D --> S[PR11.6 state persistence]
    S --> A[PR11.7 explicit state acceptance]
    A --> X[PR11.8 explicit current-state selection + fresh authority replay]
```

There is no latest-wins rule. Structural history is not sufficient authority by itself; current selection
must survive fresh replay against the exact persisted state and acceptance basis.

## Current state → advisory/read surface

```mermaid
flowchart TD
    X[PR11.8 governed current state] --> G[PR11.9 advisory progression]
    X --> P[PR11.10 complete current profile]
    G --> W[PR11.11 governed product/read snapshot]
    P --> W
```

PR11.11 does not accept a prebuilt frontier, prebuilt current portfolio, or caller-selected state IDs.
It freshly composes the governed inputs from the same live source history.

`CLEAR` remains different from `ABSENT`, and an old serialized snapshot becomes stale when its governed
source history changes.

## The executable proof

PR12.13 proves the generic observation path can reach a governed current state through the real public APIs.
PR12.14 proves the same trace reaches PR11.11 without giving the product surface state-selection or write-back authority.

- [PR12.13 — observation to governed current state](generic_capability_inference_e2e_audit_v1.md)
- [PR12.14 — observation to governed product/read snapshot](generic_governed_product_read_e2e_audit_v1.md)

These audits are integration proofs, not new inference layers.

## What is intentionally still absent

```text
automatic activity -> capability update
automatic product write-back
readiness / mastery authority
professional permission
human-worth scoring
```

Those are not implied by the existence of the governed pipeline.
