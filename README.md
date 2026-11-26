# Rho Observer

Two nodes report the same finalized block. A third goes quiet. Your app has a promising answer and an incomplete picture. Which block should it read?

I built Observer to make that decision inspectable. It asks several Rholo or RChain nodes what they saw, keeps missing and conflicting replies visible, and gives an app a block to read when the evidence supports one.

Created by [AixAria](https://github.com/aixaria0).

![Observer receives two matching reports while a third source is offline and withholds the read anchor. The third source then reports block 841. A verified path from 842 to 841 makes 841 the anchor.](docs/motion/overview.gif)

[Static storyboard](docs/motion/overview.png) · [Text walkthrough](docs/motion/README.md)

## Open a report

The public testnet Observer is a quick way to see what an application receives. With curl and Python 3, fetch its read-only report.

```sh
curl -fsS https://testnet.rhobot.net/observer/v1/observation | python3 -m json.tool
```

Start with `observations` for the per-node rows and `verdict` for the comparison. Three identical reports and one missing report mean three of three comparable sources agree and coverage is three of four. Each sample carries its starting time so a client can distinguish a fresh result from an old one.

Rholox is a browser workspace for RChain. Its Observer panel consumes these reports and shows the per-source evidence and its freshness. There is a separate API for applications that need to select a block rather than display the whole report. [Public observation endpoint](https://testnet.rhobot.net/observer/v1/observation) · [Rholox consumer source](https://github.com/aixaria0/Rholox/blob/main/src/RhoObserverPanel.tsx)

## Ask for a read anchor

A read anchor names a network, shard, height and block hash. Use the hash for each related read so that, for instance, a balance and its associated record come from the same block.

`GET /v1/read-anchor` requires a fresh sample and full coverage from at least two configured sources. If they all report the same identity, the evidence is `unanimous_reports`. If sources are at different heights and every reported tip lies on a single verified justification path, the anchor is the lowest reported block and the evidence is `verified_ancestry`. A missing source, conflict, unresolved path or stale sample yields HTTP 503 with a reason.

Observer checks reported identity and verifies the raw block hashes and signatures it traverses for ancestry. Endpoint agreement describes the configured sources. Consensus and operator independence require their own evidence. Use the selected hash with a transport that binds its response to the expected network, shard and block. [Read-anchor API](docs/READ-ANCHOR.md) · [Assurance matrix](docs/ASSURANCE.md)

## Try the decision locally

You need Git and a stable Rust toolchain. This test starts loopback endpoints and exercises the real Observer API. It checks the transition from insufficient coverage to an available anchor, then ages the sample and checks the 503 response.

```sh
git clone https://github.com/rhovision-org/rho-observer.git
cd rho-observer
cargo test --locked health_readiness_freshness_and_http_boundary_are_distinct
```

With two local Rholo HTTP endpoints available, replace the example addresses and start the service. Change `--stale-after-ms` to suit how long your application can use a sample.

```sh
cargo run --locked -- \
  --node west=http://127.0.0.1:40403 \
  --node east=http://127.0.0.1:41403 \
  serve --listen 127.0.0.1:8088 --refresh-ms 5000 --stale-after-ms 30000
```

In another terminal, `curl -i http://127.0.0.1:8088/v1/read-anchor` returns the anchor envelope or a 503 reason. For one JSON sample, pass `once` immediately after the `--node` flags. The service also exposes `/health`, `/ready` and `/metrics`. [Setup and operations](docs/GUIDE.md) · [DApp integration](docs/BUILDING-DAPPS.md)

## What an application does next

![Forge and enumerated Foundry generate artifacts for Weave recovery. Observer separately supplies a finalized read anchor for an application’s by-hash read.](docs/images/ecosystem.svg)

[Weave](https://github.com/rhovision-org/rho-weave) has an optional adapter that checks an Observer envelope and binds a caller-provided read to its hash. In the native reservation demo it withheld that read when the standalone node had no finalized fringe. The actual recovery ran separately at the node's exploration checkpoint. [Reservation demo](https://github.com/rhovision-org/rho-weave/blob/main/docs/RECOVERY.md)

The decision to update state belongs to the application and its actor. [Forge](https://github.com/rhovision-org/rho-forge) builds actors for workflows whose resources can move in independent lanes. [Foundry](https://github.com/rhovision-org/rho-foundry) compiles contracts around arithmetic guards and quotas. Either can be used in an application that reads Observer evidence. [Interface map](docs/ECOSYSTEM.md)

[Repository structure and contributions](docs/DEVELOPMENT.md) · [CI](https://github.com/rhovision-org/rho-observer/actions)

## License

[Apache License 2.0](LICENSE) · [NOTICE](NOTICE). Project creator and lead developer [AixAria](https://github.com/aixaria0). Contributors retain rights in their respective contributions. Hosting in RhoVision does not transfer authorship.
