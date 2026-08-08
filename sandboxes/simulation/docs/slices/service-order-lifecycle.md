# Slice: negotiated service order lifecycle

## Selected implementation pack

Python event-sourced simulation inside the existing repository-owned MRL
environment.

## Use-case contract

An owner identifies a motorcycle, turns maintenance needs and known information
gaps into a request for an assigned mechanic, and negotiates a versioned work
proposal. Work may start only after owner acceptance. Completion updates the
maintenance history, the mechanic invoices the accepted amount, and the owner
pays that invoice.

## Actors

- `owner`: identifies the motorcycle, requests service, responds to proposals,
  and pays completed work;
- `mechanic`: reviews a request, accepts or rejects it, proposes work, starts and
  completes the agreed job, and issues the invoice.

The motorcycle is the subject of the order, not an actor.

## Lifecycle

```text
requested -> under_review -> proposed -> negotiating -> proposed -> agreed
          -> in_progress -> completed -> awaiting_payment -> paid
```

`rejected` is a terminal review outcome. Proposal rejection is not terminal; it
returns the order to `negotiating` and preserves every proposal version.

## Rules

- motorcycle identity is bound to one owner;
- only the owner may create a request or respond to a proposal;
- only the assigned mechanic may review, propose, start, complete, or invoice;
- a rejected request requires a reason;
- a rejected proposal requires a reason and preserves negotiation history;
- work cannot start before a proposal is accepted;
- completion creates the existing auditable `ServiceRecorded` event and resets
  only the selected maintenance baselines;
- the invoice must use the accepted proposal price;
- payment must match the invoice exactly.

## Deterministic scenario

The owner identifies a Honda CB 500X and requests a chain inspection while
disclosing a missing condition photo. The mechanic accepts the request and
proposes work for 25,000 cents. The owner rejects that price. The mechanic
submits version 2 for 22,000 cents, which the owner accepts. The mechanic starts
and completes the job, the maintenance baseline is updated at 18,510 km, the
mechanic invoices 22,000 cents, and the owner pays.

## Done criteria

- every lifecycle transition is represented by an append-only event;
- rejected requests and proposal negotiation are tested;
- actor authorization is tested;
- premature work is rejected;
- completion updates maintenance history;
- invoice and payment amounts are tied to the accepted proposal;
- runtime evidence and Observatory paths include both actors and all lifecycle
  events.

## Out of scope

Mechanic discovery, scheduling capacity, diagnosis, inventory, taxes, payment
provider settlement, refunds, disputes, chat transport, and production APIs.
