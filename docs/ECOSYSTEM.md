# Rho tools in a reservation application

| Tool | What it supplies |
| --- | --- |
| [Observer](https://github.com/rhovision-org/rho-observer) | A finalized block anchor with provenance and freshness for a by-hash read. |
| [Weave](https://github.com/rhovision-org/rho-weave) | A checked controller synthesized from the reachable operations in a compiled actor and a recovery objective. |
| [Forge](https://github.com/rhovision-org/rho-forge) | Concurrent reservation lanes with independent private clocks and role capabilities. |
| [Foundry](https://github.com/rhovision-org/rho-foundry) | Guarded integer contracts and arithmetic compilation for large counters. |

A caller recovering a reservation can use the [anchor endpoint](READ-ANCHOR.md) to obtain the block to read, then feed authenticated actor observations to a manifest-derived recovery controller. Forge's revision check guards each call against intervening writes. Pick Foundry when the core contract needs linear guards over counters. Each tool has a standalone entry point.
