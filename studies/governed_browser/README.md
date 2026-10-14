# Offline governed-browser contract

Original experimental adapter study by Carlos Felipe (ofelipepeixoto), MIT as
the repository license. Upstream Browser Use remains attributed to its authors.
Baseline: c75e8476e26d18b7617643bc2ae082fae8eae431.

This study never imports Browser Use, opens a browser, connects MCP, calls a
model, or sends network traffic. The only executor is a synthetic fixture.
It uses the existing Pydantic v2 dependency; no new service or infrastructure.

Run from this directory: `python -m unittest -v test_contract.py`.

The contract rejects unknown fields/actions and real destinations. Consequential
fixture actions require a one-use, proposal-bound, expiring review token and
produce a receipt. Simulated integer units are reserved before the result;
uncertain results retain their reservation and job IDs cannot replay.

Approval is explicitly synthetic: `fixture-human` is NOT an authenticated person.
The caller supplies a synthetic clock. State is in memory and single-process;
it is not durable, thread-safe, distributed, tamper-evident or multi-tenant.
Units are not currency and do not enforce a provider account's billing limit.

Egress is absent by construction (no network transport). Configuration returned
by `browser_configuration()` documents an exact allowlist and disabled telemetry
and cloud sync, but is NOT an OS firewall or a configuration applied to a live
browser. DNS, redirects, subresources and real browser isolation are untested.

Before any live adapter: authenticated backend review, trusted clock, durable
atomic reservations/receipts, independent egress controls, disposable profiles,
provider budget enforcement and local browser integration tests are required.
Reuse `browser_use/mcp/server.py` if a real MCP consumer is needed; this study
does not add another server. No hub integration or deployment is claimed.

Review UI should display destination, action, proposal hash, unit cap, expiry,
cancel control and the explicit `uncertain` state. No UX study was performed.
