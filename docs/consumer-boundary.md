# Consume the governed read boundary

The stable current consumer boundary is **PR11.11 `CurrentStateGovernedPlayerWindow`**.

It is designed for a product that needs to present governed capability state and advisory progression
without becoming a new state-selection or capability-update authority.

## What a consumer receives

A governed product/read snapshot binds:

- the complete current-selection history head portfolio;
- the current selected state set;
- the freshly governed PR11.9 progression frontier;
- exact digests that bind those sources to the rendered snapshot;
- governance metadata required to distinguish meanings such as `SELECT`, `CLEAR`, and `ABSENT`.

The raw presentation window exposes every and only current `SELECT` state. Governance history remains
available outside the raw presentation surface so that omission from display does not erase meaning.

## What the consumer does not get

The request surface does not accept:

```text
caller-selected state_id
caller-selected subject
prebuilt current portfolio
prebuilt governed frontier
selected_state_ids
selected frontier object
write-back command
```

That absence is intentional. A product may ask for a view; it may not decide what the governed current
state should be simply by choosing convenient inputs.

## Fresh validation is part of consumption

A canonical JSON round-trip is useful for transport and audit, but serialization does not create authority.

```text
serialized snapshot != live authority
```

Before relying on a restored snapshot as current, validate it against the live governed source history and
authority bases. PR12.14 proves that historical appends stale older PR11.10/PR11.11 artifacts even when a
new governance act is timestamped no later than the old snapshot's generation time.

## Time semantics

The product boundary distinguishes semantic time from derivation time.

A current state may have been derived later while representing an earlier epistemic `state.as_of`.
A product request earlier than the selected state's semantic `state.as_of` fails closed rather than silently
filtering the state from view.

Malformed `generated_at < as_of` requests and governance acts from after the product generation time are
also rejected by the owning layers.

## Consumer invariants

```text
VISIBLE != CURRENT
HIDDEN != DELETED
CLEAR != ABSENT
PRESENTATION != AUTHORITY
PROGRESSION != READINESS
PROGRESSION != PERMISSION
CURRENT != MASTERY
PRODUCT VIEW != CAPABILITY WRITE-BACK
```

These are not UI slogans; they are the integration contract.

## Recommended integration posture

Treat Capability Lab as a governed subsystem that produces a read/advisory artifact.

```text
consumer application
        ↓ request
Capability Lab governed sources
        ↓ fresh derivation + validation
PR11.11 product/read snapshot
        ↓
consumer presentation / explanation
```

Keep application permissions, authentication, professional authorization, and action execution in their
own systems. Capability Lab state can inform a product without becoming the authority that decides whether
a person may act.

For the exact executable proof, read the
[PR12.14 product/read audit](generic_governed_product_read_e2e_audit_v1.md).
