# Pinning a read to a finalized block

Query the Observer service you trust for endpoint observations.

```sh
curl --fail-with-body http://127.0.0.1:8088/v1/read-anchor
```

| Response | Condition |
| --- | --- |
| 200 `available`, `unanimous_reports` | Every configured endpoint returned the same complete finalized identity and at least two endpoints reported. |
| 200 `available`, `verified_ancestry` | Full coverage and one verified justification path from the highest reported block through every reported hash down to the lowest. The selected anchor is the lowest. |
| 503 `stale` | Age from the start of sampling meets or exceeds the configured freshness threshold. |
| 503 `insufficient_sources` | Fewer than two configured endpoints or at least one report is missing or unusable. |
| 503 `conflicting` | The report contains conflicting finalized identities or incompatible network or shard identities. |
| 503 `unresolved` | The available ancestry evidence cannot support a common reported read anchor. |

The schema string is `rho-observer/read-anchor/v1`. An available response includes `anchor` with `network_id`, `shard_id`, `block_number`, and a lowercase hexadecimal `block_hash`. On 503, both `anchor` and `evidence` are null. All responses carry the source counts, the wall-clock sampling start in `observed_at_ms`, the monotonic `snapshot_age_ms` and the service's `stale_after_ms`.

Check the expected network and shard, account for time spent in transit and application queues, and use the selected hash for every related read. The application owns the trust and response binding for its by-hash transport. Endpoint agreement is reported evidence. Verified ancestry describes justification edges checked against content hashes and signatures. Consensus finality and independent operators require their own evidence. A valid anchor can lag application writes, so mutations still require the actor's current revision and authority.

The endpoint reads the existing cache and has no write method. Independent sibling blocks may each be ancestors of the highest tip. That pair of proofs alone does not support a read anchor common to both siblings.
