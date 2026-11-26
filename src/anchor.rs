use std::{collections::HashSet, time::Duration};

use serde::Serialize;

use crate::{
    model::{AncestryClass, FinalizedIdentity, ObservationReport, VerdictClass},
    verdict::finalized_identity,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AnchorStatus {
    Available,
    Stale,
    InsufficientSources,
    Conflicting,
    Unresolved,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AnchorEvidence {
    UnanimousReports,
    VerifiedAncestry,
}

#[derive(Debug, Serialize)]
pub struct ReadAnchor {
    pub schema: &'static str,
    pub status: AnchorStatus,
    pub anchor: Option<FinalizedIdentity>,
    pub evidence: Option<AnchorEvidence>,
    pub observed_at_ms: u64,
    pub snapshot_age_ms: u64,
    pub stale_after_ms: u64,
    pub observed_nodes: usize,
    pub comparable_nodes: usize,
}

impl ReadAnchor {
    pub fn from_report(report: &ObservationReport, age: Duration, stale_after: Duration) -> Self {
        let mut response = Self {
            schema: "rho-observer/read-anchor/v1",
            status: AnchorStatus::Stale,
            anchor: None,
            evidence: None,
            observed_at_ms: report.observed_at_ms,
            snapshot_age_ms: age.as_millis().min(u128::from(u64::MAX)) as u64,
            stale_after_ms: stale_after.as_millis().min(u128::from(u64::MAX)) as u64,
            observed_nodes: report.verdict.observed_nodes,
            comparable_nodes: report.verdict.comparable_nodes,
        };
        if age < stale_after {
            match select(report) {
                Ok((anchor, evidence)) => {
                    response.status = AnchorStatus::Available;
                    response.anchor = Some(anchor);
                    response.evidence = Some(evidence);
                }
                Err(status) => response.status = status,
            }
        }
        response
    }
}

fn select(report: &ObservationReport) -> Result<(FinalizedIdentity, AnchorEvidence), AnchorStatus> {
    let verdict = &report.verdict;
    if matches!(
        verdict.class,
        VerdictClass::Majority
            | VerdictClass::Divergence
            | VerdictClass::ConflictingFinalizedHistory
    ) {
        return Err(AnchorStatus::Conflicting);
    }
    if verdict.observed_nodes < 2
        || verdict.comparable_nodes != verdict.observed_nodes
        || report.observations.len() != verdict.observed_nodes
    {
        return Err(AnchorStatus::InsufficientSources);
    }
    let identities = report
        .observations
        .iter()
        .map(finalized_identity)
        .collect::<Option<Vec<_>>>()
        .ok_or(AnchorStatus::InsufficientSources)?;
    let lowest = identities
        .iter()
        .min_by_key(|id| id.block_number)
        .ok_or(AnchorStatus::InsufficientSources)?;
    if identities.iter().all(|id| id == lowest) {
        return Ok((lowest.clone(), AnchorEvidence::UnanimousReports));
    }
    if verdict.class != VerdictClass::ProvenLag {
        return Err(AnchorStatus::Unresolved);
    }

    // Separate proofs from two tips to the highest block do not establish
    // ancestry between those tips. Require every reported finalized hash to
    // lie on a single verified path to the selected lowest identity.
    let chain = report.ancestry_checks.iter().find(|check| {
        check.class == AncestryClass::ProvenLag
            && &check.lower == lowest
            && Some(&check.higher) == verdict.reference.as_ref()
            && check.path.first() == Some(&check.higher.block_hash)
            && check.path.last() == Some(&check.lower.block_hash)
            && check.cryptographically_verified_blocks >= check.path.len()
    });
    let path = chain.ok_or(AnchorStatus::Unresolved)?;
    let hashes: HashSet<_> = path.path.iter().map(String::as_str).collect();
    if identities.iter().any(|id| {
        id.network_id != lowest.network_id
            || id.shard_id != lowest.shard_id
            || !hashes.contains(id.block_hash.as_str())
    }) {
        return Err(AnchorStatus::Unresolved);
    }
    Ok((lowest.clone(), AnchorEvidence::VerifiedAncestry))
}
