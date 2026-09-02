# Civilization Bootstrap Pilot 01 — Upstream Source Ancestry, Alias/Copy/Transform Lineage and False-Independence Adversarial Closure

Status: **PR10.1 adversarial closure**

This closure addresses the next dependence boundary after exact declared upstream-source equality.

The previous PR10.1 layer can already reject:

```text
observation A -> upstream source X
observation B -> upstream source X
```

But two different declared refs can still name related source material:

```text
observation A -> source A
observation B -> source B

source A != source B

BUT

source A COPY_OF root
source B TRANSFORM_OF root
```

or:

```text
source A ALIAS_OF source B
```

or:

```text
source A DERIVED_FROM middle
middle COPY_OF root
source B DERIVED_FROM root
```

Different opaque refs therefore do not establish source independence.

```text
DIFFERENT SOURCE REFS != DIFFERENT CAUSAL ORIGINS
DIFFERENT SOURCE KEYS != INDEPENDENT SOURCES
DERIVED COPY != NEW INDEPENDENT SOURCE
TRANSFORMED SOURCE != NEW INDEPENDENT SOURCE
```

## Separate source-to-source lineage graph

PR10.1 adds a new private governance object:

```text
PilotUpstreamSourceLineageGraph
```

The graph does not change:

- the PR10.0 raw capture schema;
- the materialization candidate schema;
- the materialization review schema;
- the neutral PR2 `EvidenceRecord`;
- the existing candidate-bound upstream source declaration.

It only records source-to-source relations that the local governance process already knows.

Graph edges are:

```text
ALIAS_OF
COPY_OF
TRANSFORM_OF
DERIVED_FROM
```

represented by:

```text
PilotUpstreamSourceRelation(
    relation_kind,
    source,
    upstream,
)
```

For `COPY_OF`, `TRANSFORM_OF`, and `DERIVED_FROM`:

```text
source -> upstream
```

means that `source` is the downstream value and `upstream` is the declared parent.

`ALIAS_OF` is symmetric.

The graph is declaration metadata, not a discovery engine.

```text
GRAPH EDGE != AUTOMATICALLY DISCOVERED FACT
GRAPH EDGE != AUTHENTICATED PROVENANCE
GRAPH EDGE != SOURCE CONTENT VERIFICATION
```

## Why relation kinds stay explicit

PR10.1 does not flatten every relation into one undifferentiated `RELATED_TO`.

The relation kind preserves the bounded observation that was actually declared:

```text
A ALIAS_OF B
A COPY_OF B
A TRANSFORM_OF B
A DERIVED_FROM B
```

All four are sufficient to establish known dependence for this gate, but they are not semantically identical.

A future provenance system may care whether a source was byte-copied, transformed, generically derived, or merely represented by a second alias.

## Alias contraction and DAG validation

Alias relations create equivalence classes.

They are therefore not treated as ordinary two-way directed ancestry edges when validating graph acyclicity.

The validator first contracts:

```text
A ALIAS_OF B
```

into one alias class.

It then validates the directed `COPY_OF`, `TRANSFORM_OF`, and `DERIVED_FROM` graph between alias classes.

This catches hidden cycles such as:

```text
A ALIAS_OF B
B DERIVED_FROM C
C COPY_OF A
```

because after alias contraction the directed graph becomes:

```text
[A,B] -> C -> [A,B]
```

and is rejected.

The graph also rejects:

- self-relations;
- exact duplicate relations;
- reverse duplicates of the same alias pair;
- conflicting directed relation kinds for the same ordered source pair;
- directed relations that collapse inside one alias class;
- directed cycles after alias contraction.

```text
SOURCE LINEAGE GRAPH
=> DECLARED ACYCLIC UPSTREAM ANCESTRY AFTER ALIAS CONTRACTION
```

This does not prove that the real-world causal graph is complete or acyclic. It only keeps the declared governance structure internally coherent.

## Declared lineage closure

PR10.1 exposes:

```text
pilot_upstream_source_lineage_closure_keys_v1(source, graph)
```

The returned closure always contains the source itself.

Traversal semantics are:

```text
ALIAS_OF
    <->

COPY_OF
TRANSFORM_OF
DERIVED_FROM
    downstream -> upstream
```

Therefore:

```text
child TRANSFORM_OF parent
```

produces:

```text
closure(child)  = {child, parent, ...ancestors}
closure(parent) = {parent, ...ancestors}
```

and does not incorrectly make the parent descend from the child.

The closure is transitive.

If:

```text
leaf TRANSFORM_OF middle
middle COPY_OF root
```

then `closure(leaf)` contains all three declared source identities.

Ordinary validator output uses the existing domain-separated source dependence keys rather than echoing raw source refs.

```text
HASHED LINEAGE KEY != ANONYMIZATION
HASHED LINEAGE KEY != SOURCE AUTHENTICATION
```

## Source-ancestry independence precondition gate

The strongest structural PR10.1 gate in this closure is:

```text
validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(...)
```

It first composes every earlier layer:

```text
exact PilotCaptureRecord reuse
    -> REJECT

same Pilot session lineage
    -> REJECT

cross-session repeated same probe
    -> REJECT

same exact declared upstream source
    -> REJECT
```

It then expands every declared upstream source through the supplied source-lineage graph.

If two observations' closures intersect, the observations have a known common declared source lineage.

Examples:

```text
A declares source_a
B declares source_b

source_a ALIAS_OF source_b
    -> REJECT
```

```text
source_a DERIVED_FROM source_b
    -> REJECT
```

```text
source_a TRANSFORM_OF root
source_b COPY_OF root
    -> REJECT
```

```text
source_a TRANSFORM_OF middle
middle COPY_OF root
source_b DERIVED_FROM root
    -> REJECT
```

The records remain valid historical observations. The gate rejects only the stronger interpretation that these observations satisfy source-independence preconditions.

## Common ancestor rather than connected component

The closure follows only upstream ancestry, except that aliases are symmetric.

This distinction matters.

If:

```text
child DERIVED_FROM parent
```

then the child's closure contains the parent, but the parent's closure does not contain the child.

PR10.1 therefore detects:

- exact common source;
- aliases;
- ancestor/descendant reuse;
- siblings with a declared common ancestor;
- transitive copy/transform/derivation ancestry.

It does not classify two sources as dependent merely because they share a downstream descendant.

That would reverse the causal direction.

## Empty and incomplete graph semantics

An empty graph is valid:

```text
PilotUpstreamSourceLineageGraph(relations=())
```

Its meaning is only:

```text
NO SOURCE-TO-SOURCE RELATIONS WERE SUPPLIED
```

It does not mean:

```text
THE SOURCES HAVE NO COMMON ORIGIN
```

Likewise, if two declared refs have disjoint closures in the supplied graph:

```text
PASS
```

means only:

```text
THE SUPPLIED GRAPH DID NOT EXPOSE A COMMON ALIAS OR ANCESTOR
```

It does not mean:

```text
THE SOURCES ARE INDEPENDENT
```

The graph may be incomplete, stale, wrong, or missing hidden relations.

```text
NO DECLARED COMMON ANCESTOR != NO COMMON ANCESTOR
DISJOINT DECLARED CLOSURES != STATISTICAL INDEPENDENCE
PASS != EPISTEMIC INDEPENDENCE
```

## No automatic alias inference

PR10.1 deliberately does not infer:

```text
similar refs -> aliases
same filename -> copies
similar text -> derivation
same model family -> common output
same URL host -> common source
same tool -> common source
```

An alias, copy, transform, or derivation edge must be explicitly represented.

This prevents the dependence layer from inventing causal facts that were never observed.

## Candidate and observation binding remain unchanged

Observation-to-upstream-source declarations remain exactly candidate-bound through:

```text
candidate_sha256
```

The new graph describes relations among those already-declared upstream source identities.

The graph does not weaken the earlier binding:

```text
EvidenceRecord
    <- exact candidate
    <- exact candidate-bound source declaration
    <- source-to-source lineage graph
```

A caller still cannot attach Candidate A's source declaration to Candidate B.

## New invariants

```text
DIFFERENT DECLARED SOURCE REFS
!=
DIFFERENT CAUSAL ORIGINS
```

```text
ALIAS
COPY
TRANSFORM
DERIVATION
=>
KNOWN DECLARED SOURCE DEPENDENCE
```

```text
TWO DISTINCT SOURCES
+
ONE DECLARED COMMON ANCESTOR
=>
NOT TWO SOURCE-INDEPENDENT SUPPORT VOTES
```

```text
TRANSITIVE DECLARED ANCESTRY
MUST REMAIN TRANSITIVE FOR DEPENDENCE GOVERNANCE
```

```text
EMPTY OR INCOMPLETE LINEAGE GRAPH
!=
PROOF OF SOURCE INDEPENDENCE
```

```text
PASSING SOURCE-ANCESTRY PRECONDITIONS
!=
AUTHORITY TO CLAIM INDEPENDENCE
```

## Non-goals

This closure does not add:

- automatic lineage discovery;
- source content fetching;
- byte-level copy detection;
- perceptual or semantic similarity;
- source alias resolution from names;
- signatures or authenticated source identity;
- authenticated graph authorship;
- graph persistence or publication;
- confidence scores for lineage edges;
- probabilistic causal inference;
- statistical independence estimation;
- automatic evidence weighting;
- claim creation or evaluation;
- PR3 state derivation;
- achievements, progression, or Player Window logic.

The next unresolved boundary is no longer ordinary graph reachability. A declared source graph can still be incomplete or untrusted, and two apparently disconnected roots can share a hidden origin. Closing that requires stronger source-origin provenance or reviewed lineage-completeness/unknown-dependence governance rather than inventing another equality rule.
