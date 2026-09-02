# Civilization Bootstrap Pilot 01 — Declared Upstream-Source Lineage and Hidden-Amplification Adversarial Closure

Status: **PR10.1 adversarial closure**

This closure addresses the next dependence boundary after exact-source reuse,
same-session correlation, and repeated same-probe elicitation lineage.

The remaining adversarial geometry is:

```text
capture A != capture B
session(A) != session(B)
probe(A)   != probe(B)

BUT

both observations depend on one known upstream source
```

Examples include the same external reference, artifact, dataset, model output,
tool output, operator-provided input, or external record being reused across
otherwise distinct Pilot observations.

The important distinction is:

```text
DIFFERENT CAPTURES != DIFFERENT CAUSAL SOURCES
DIFFERENT SESSIONS != DIFFERENT CAUSAL SOURCES
DIFFERENT PROBES != DIFFERENT CAUSAL SOURCES
```

## Why PR10.1 cannot infer this from existing capture fields

Pilot 01 already preserves:

- exact capture bytes;
- session and subject identity;
- probe identity;
- declared tool names;
- exact candidate and materialized-evidence binding.

Those fields are enough for the earlier structural closures, but they do not
identify an arbitrary upstream reference or causal source.

PR10.1 deliberately does **not** treat matching `declared_tools` as proof of
common source lineage. Two observations may both use a calculator, browser, or
multimeter independently.

Likewise, this closure does not mine raw response text, participant notes, URLs,
or artifacts heuristically to guess common causality.

```text
SAME TOOL NAME != SAME TOOL OUTPUT
SIMILAR TEXT != SAME SOURCE
MODEL GUESS != PROVEN LINEAGE
```

## Separate post-materialization source declaration

The raw PR10.0 capture schema, materialization candidate schema, materialization
review schema, and neutral PR2 `EvidenceRecord` mapping remain unchanged.

Instead, PR10.1 adds separate private governance metadata:

```text
PilotMaterializationUpstreamSourceDeclaration
```

It contains:

```text
candidate_sha256
sources[]
```

Each source is a typed:

```text
PilotUpstreamSourceRef(
    kind,
    ref,
)
```

Supported source categories are:

```text
REFERENCE
ARTIFACT
DATASET
MODEL_OUTPUT
TOOL_OUTPUT
OPERATOR_INPUT
EXTERNAL_RECORD
OTHER
```

This structure is intentionally outside the raw capture and PR2 evidence
schemas. It records a source relation already known to the local governance
process; it does not infer that relation.

## Exact candidate binding

A source declaration is bound to the exact canonical materialization candidate:

```text
candidate bytes
    ↓
candidate_sha256
    ↓
upstream-source declaration
```

`build_pilot_materialization_upstream_source_declaration_v1(...)` computes the
candidate digest rather than asking a caller to retype it.

`PilotMaterializedEvidenceUpstreamLineageEntry` then combines:

```text
PilotMaterializedEvidenceBasisEntry
+
PilotMaterializationUpstreamSourceDeclaration
```

and fails closed if the declaration's `candidate_sha256` does not match the
exact candidate already bound to the EvidenceRecord.

Therefore a source declaration for Candidate A cannot be silently attached to
Candidate B.

```text
DECLARATION FOR CANDIDATE A
!=
SOURCE METADATA FOR CANDIDATE B
```

This is still structural binding rather than authentication. The declaration is
not signed, and PR10.1 does not prove that a human supplied a truthful or
complete source list.

## Source identity and dependence key

`PilotUpstreamSourceRef.ref` is a canonical opaque ASCII identifier under local
source-governance semantics.

Examples:

```text
reference:shared_note_v1
artifact:fixture_sha256_abcd
model_output:run_001
external_record:record_42
```

PR10.1 does not assume that an opaque ref is globally collision-proof or
content-addressed.

For comparison without echoing the raw source ref into ordinary validator
output, PR10.1 exposes:

```text
pilot_upstream_source_dependence_key_v1(source)
```

This returns a domain-separated SHA-256 over:

```text
source kind
source ref
```

as:

```text
pilot_upstream_source:<sha256>
```

Equality means only:

```text
SAME DECLARED KIND + SAME DECLARED REF
```

It does not authenticate the ref, prove source contents, or anonymize a
guessable identifier.

## Upstream-lineage precondition gate

The strongest PR10.1 structural gate in this closure is:

```text
validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1(...)
```

It composes all earlier checks first:

```text
exact source reuse
    -> REJECT

same session lineage
    -> REJECT

different sessions + repeated same probe
    -> REJECT
```

It then compares candidate-bound upstream-source declarations.

If the same exact declared upstream source occurs in two observations:

```text
observation A -> source X
observation B -> source X
```

the gate rejects treating that basis as source-independent:

```text
SHARED DECLARED UPSTREAM SOURCE
=> KNOWN DECLARED COMMON-SOURCE LINEAGE
=> REJECT INDEPENDENCE PRECONDITION
```

The observations themselves remain valid historical observations. They are not
deleted, merged, relabeled, or converted into one EvidenceRecord.

## Empty and incomplete declarations

An empty declaration is valid:

```text
sources = ()
```

Its meaning is only:

```text
THIS DECLARATION SUPPLIES NO UPSTREAM-SOURCE REFS
```

It does **not** mean:

```text
NO UPSTREAM SOURCE EXISTS
```

Likewise:

```text
different declared source refs
!= proven different causal sources

no shared declared source
!= source completeness

passing the gate
!= independence
```

Aliases, copied sources, transformed derivatives, undisclosed references,
coordinated operator intervention, and hidden common mechanisms can remain
undetected.

This is intentional. PR10.1 closes only dependencies that are structurally
available to the gate without inventing evidence.

## No automatic inference from tool names

`declared_tools` remains ordinary observed context.

For example:

```text
capture A declared tool = calculator
capture B declared tool = calculator
```

does not justify:

```text
shared upstream TOOL_OUTPUT
```

If both captures actually consumed one exact calculator export or one exact
model response, that shared output can be represented explicitly as:

```text
PilotUpstreamSourceRef(
    TOOL_OUTPUT,
    "tool_output:<governed_ref>",
)
```

or:

```text
PilotUpstreamSourceRef(
    MODEL_OUTPUT,
    "model_output:<governed_ref>",
)
```

The distinction prevents generic tool availability from being converted into a
false causal-dependence claim.

## Privacy boundary

Upstream refs may themselves be private metadata. The declaration is not
automatically serialized, published, copied into the raw Pilot workspace, or
embedded into the PR2 EvidenceRecord.

The dependence key reduces accidental ref echoing but is not an anonymization
primitive.

```text
HASHED SOURCE KEY != ANONYMOUS SOURCE
DECLARATION != PUBLICATION CONSENT
```

## New invariants

```text
DIFFERENT CAPTURE
+ DIFFERENT SESSION
+ DIFFERENT PROBE
!=
DIFFERENT UPSTREAM CAUSAL SOURCE
```

```text
SAME EXACT DECLARED UPSTREAM SOURCE
=>
KNOWN DECLARED COMMON-SOURCE LINEAGE
```

```text
KNOWN DECLARED COMMON-SOURCE LINEAGE
!=
MULTIPLE INDEPENDENT SUPPORT VOTES
```

```text
NO SHARED DECLARED SOURCE
!=
PROOF OF SOURCE INDEPENDENCE
```

```text
UPSTREAM DECLARATION
!=
AUTHENTICATED OR COMPLETE PROVENANCE
```

## Non-goals

This closure does not add:

- automatic URL/reference extraction;
- response-text similarity analysis;
- model-based causal inference;
- automatic `declared_tools` correlation;
- source-content fetching;
- global source registry;
- globally authenticated source identity;
- declaration signatures;
- declaration persistence or publication;
- automatic evidence weighting;
- claim creation or evaluation;
- statistical independence estimation;
- source alias resolution;
- derived-source graph closure;
- state, achievement, progression, or Player Window logic.

The next unresolved layer is no longer a simple exact-equality problem: two
different declared upstream refs may themselves be aliases, copies, transforms,
or descendants of one common source. Closing that requires explicit
source-to-source lineage rather than merely more observation-level keys.
