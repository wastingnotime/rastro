# Service order lifecycle refinement check

- The model distinguishes the motorcycle subject from owner and mechanic actors.
- The happy path includes one rejected proposal and one accepted revision.
- Authorization, rejection, premature start, maintenance update, invoice, and
  payment invariants have deterministic tests.
- Runtime evidence exposes the complete ordered lifecycle.
- Discovery, diagnosis, scheduling, payment settlement, refunds, and disputes
  remain explicit follow-up scope.
