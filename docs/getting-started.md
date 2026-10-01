# Capability Lab in 5 minutes

Capability Lab starts with a simple question:

> **What does the evidence actually support about what a person can do — and what do we still not know?**

The easiest intuition is a **real-world skill tree or player profile that has to show its work**. Instead of a
skill appearing because an XP bar increased, each capability stays connected to the evidence, context,
uncertainty, and history behind it.

This is an intuition, not the formal data model. Capability Lab is a research framework, not a game.

## A concrete example

Imagine someone is learning electronics.

They build a working low-voltage motor circuit, test it, and explain why it works.

A simple skill tracker might turn that into:

```text
Electrical engineering: 87%
```

Capability Lab deliberately does not do that.

Instead, it keeps asking a series of smaller questions.

## 1. What happened?

First there is an activity or external observation:

```text
A person built, tested, and explained a low-voltage motor circuit.
```

At this point the system has a record of something that happened.

That record is **not automatically evidence**.

## 2. Should this become evidence?

A governing workflow reviews the observation.

If it is admitted, the useful parts can become neutral evidence:

```text
project artifact
test results
explanation
observed context
source and provenance
```

The review does not yet say that the person is "good at electronics." It only decides whether the observation
belongs in the evidence history.

```text
observation != evidence
```

## 3. What bounded claim could the evidence speak to?

Evidence is interpreted against a specific capability concept and scope.

For this example, a bounded claim might be:

```text
can construct a basic low-voltage motor circuit under the observed conditions
```

That is intentionally narrower than:

```text
is an electrical engineer
```

or:

```text
understands all of electronics
```

Context matters.

## 4. Does the evidence actually support the claim?

The evidence is evaluated under an explicit policy.

A result may be supported, contradicted, mixed, insufficient, or abstained depending on the exact governed
basis.

If evidence is missing, Capability Lab does not manufacture a zero.

If evidence conflicts, Capability Lab does not have to average the conflict away.

```text
unknown != failure
conflict != certainty
```

## 5. What happens to older evidence?

It stays part of the history.

A newer successful project does not silently erase an older insufficient result. A later failure does not
silently erase earlier support either.

Downstream state is derived from the complete governed history for the relevant scope.

This makes the question inspectable:

> Why does the system currently support this capability claim?

## 6. Does a derived state automatically become current?

No.

Capability Lab separates:

```text
derived
!= persisted
!= accepted
!= current
```

That separation prevents "the latest model output" from automatically becoming the person's current governed
profile.

The exact governance mechanism depends on the workflow, but current state is an explicit transition rather than
an accidental side effect.

## 7. What can progression do?

Once there is governed current state, a progression layer may identify a useful next challenge.

For the motor-circuit example:

```text
Possible next exploration:
diagnose an unfamiliar circuit fault
```

That is advice, not destiny.

The person may ignore it, explore something unrelated, or choose a different goal.

```text
progression != prescription
```

## 8. What can a product show?

A product can consume a governed read snapshot containing current capability state and advisory progression.

It still does not receive permission to turn that view into:

```text
eligible for job
licensed to practice
allowed to perform action
human rank
intelligence score
```

Those belong to other systems and policies.

```text
capability != permission
product view != authority
```

## What does Capability Lab help represent?

A Capability Lab-style system can preserve:

- what was observed;
- what became evidence;
- where that evidence came from;
- what bounded claims it can speak to;
- what the evidence currently supports or contradicts;
- what remains unknown;
- where conflict remains unresolved;
- how the governed state changed over time;
- what may be useful to explore next.

The project is intentionally conservative about turning those records into conclusions.

## When is this useful?

Capability Lab is relevant when a product or research system needs a model of human capability and cares about
**why** a capability is considered supported.

Possible settings include:

- personal learning and development;
- AI assistants that adapt to demonstrated user capabilities;
- skill/progression interfaces backed by real evidence;
- research into human capability representation;
- systems that need an advisory capability view but must keep it separate from ranking or permission.

It is currently a **research framework and reference subsystem**, not a finished consumer application.

## What is it not?

Capability Lab is not an intelligence test, personality score, HR ranking system, universal human level,
professional license, or automatic career decision-maker.

It models governed claims about capability.

It does not define the person.

## Where did the idea come from?

The project began with a simple idea:

> What if a person could have something like a real-world skill tree, but every node had to earn its place
> through evidence rather than XP?

That quickly creates harder questions.

What counts as evidence? What if evidence conflicts? What if a model is uncertain? Does a demonstrated
capability mean the person should pursue it? Who decides what state is current? Does a supported capability grant
permission to act?

Capability Lab is the research framework that grew out of trying to answer those questions without losing the
appeal of visible, meaningful personal progression.

## Where to go next

If this mental model makes sense:

- [Understand the model](overview.md) explains the major conceptual boundaries.
- [Follow the governed pipeline](governed-pipeline.md) traces the system end to end.
- [Consume the governed read boundary](consumer-boundary.md) is for product integration.
- [Architecture](architecture.md) contains the detailed current implementation structure.
- [Constitution](constitution.md) defines the human-agency, privacy, and epistemic rules.
