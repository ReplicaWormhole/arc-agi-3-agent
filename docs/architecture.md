# Architecture

## Design goal

The agent should learn an unfamiliar game without treating real environment
actions as free simulation. Every real action is issued by one executor and is
recorded in an immutable observation log.

```text
environment -> observation log -> state/difference parser -> hypothesis ledger
                                                    |                 |
                                                    v                 v
                                           transition graph    model proposers/critics
                                                    \                 /
                                                     v               v
                                              verified simulator / planner
                                                        |
                                                        v
                                               single action executor
```

## Current implementation

`arc_agent.explorer` implements the first model-free layer:

1. `TransitionGraph` records exact observed frame/action transitions.
2. `HypothesisLedger` makes modest, falsifiable claims such as whether an
   action changes the visible state.
3. `ExplorationController` balances legal-action coverage while avoiding a
   repeated exact state/action pair.
4. The planner can use only an already observed route to progress and must not
   claim that an unobserved transition will succeed.

This is intentionally not yet an object-level simulator. The next layer will
parse persistent objects, displacement, collisions, and level goals; only then
should it compile hypotheses into executable transition functions.

## Model boundary

`arc_agent.model_client` provides an OpenAI-compatible chat endpoint adapter.
It is used only as a proposal mechanism: a response may propose hypotheses or
candidate simulator code, never authorize an action by itself. The same adapter
can point at a local server or a remote development endpoint. The executor,
verifier, and test suite must remain model-provider independent.
