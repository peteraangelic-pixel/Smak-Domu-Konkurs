//! RHAE — Relative Human Action Efficiency, the ARC-AGI-3 metric.
//!
//! ```text
//! level_score_l = min( (H_l / A_l)², 1.15 )
//! game_score = min( weighted_mean(level_score), weighted_completion_fraction )
//! ```
//!
//! `H_l` = median human action count for level `l`, `A_l` = the agent's action count.
//! Later levels receive their 1-indexed level number as weight. The per-level score
//! is capped at 1.15, and the game score is capped by weighted level completion.

/// Per-level cap on the normalized squared score.
pub const RHAE_CAP: f64 = 1.15;

/// Score for one level. `human` and `agent` are action counts.
///
/// `agent == 0` cannot happen in practice (an agent that took no actions solved
/// nothing); we return 0.0 rather than divide by zero.
pub fn level_score(human: u32, agent: u32) -> f64 {
    if agent == 0 {
        return 0.0;
    }
    let ratio = human as f64 / agent as f64;
    (ratio * ratio).min(RHAE_CAP)
}

/// Unweighted mean over levels, useful as a diagnostic only.
///
/// The official game score is [`game_score`], which weights levels by their
/// 1-indexed level number and applies the completion cap.
pub fn rhae(levels: &[(u32, u32)]) -> f64 {
    if levels.is_empty() {
        return 0.0;
    }
    let total: f64 = levels.iter().map(|&(h, a)| level_score(h, a)).sum();
    total / levels.len() as f64
}

/// Official normalized score for one game.
///
/// `human_actions` contains the baseline for every level in the game.
/// `agent_actions` contains action counts for sequentially completed levels
/// only. Uncompleted levels contribute zero, and the overall score is capped
/// by the weighted fraction of levels completed.
pub fn game_score(human_actions: &[u32], agent_actions: &[u32]) -> f64 {
    let total_levels = human_actions.len();
    if total_levels == 0 {
        return 0.0;
    }

    let completed_levels = agent_actions.len().min(total_levels);
    let total_weight: f64 = (1..=total_levels).map(|level| level as f64).sum();
    let completed_weight: f64 = (1..=completed_levels).map(|level| level as f64).sum();

    let weighted_efficiency: f64 = human_actions
        .iter()
        .zip(agent_actions.iter())
        .enumerate()
        .map(|(index, (&human, &agent))| (index + 1) as f64 * level_score(human, agent))
        .sum::<f64>()
        / total_weight;

    weighted_efficiency.min(completed_weight / total_weight)
}

/// Weighted mean (later levels carry more weight in the real benchmark).
/// Each entry is `(human_actions, agent_actions, weight)`.
pub fn rhae_weighted(levels: &[(u32, u32, f64)]) -> f64 {
    let wsum: f64 = levels.iter().map(|&(_, _, w)| w).sum();
    if wsum <= 0.0 {
        return 0.0;
    }
    let total: f64 = levels.iter().map(|&(h, a, w)| w * level_score(h, a)).sum();
    total / wsum
}

/// Maximum normalized per-game score after the official completion cap.
pub fn ceiling() -> f64 {
    1.0
}

/// Actions at the threshold where the 1.15 per-level score cap begins to apply.
/// Levels are also hard-capped at 5× the human count in the real benchmark.
pub fn actions_at_cap(human: u32) -> f64 {
    human as f64 / RHAE_CAP.sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn approx(a: f64, b: f64) -> bool {
        (a - b).abs() < 1e-12
    }

    #[test]
    fn level_cap_is_1_15_and_full_game_cap_is_1() {
        assert!(approx(level_score(10, 1), 1.15));
        assert!(approx(ceiling(), 1.0));
    }

    #[test]
    fn matching_human_scores_one() {
        assert!(approx(level_score(10, 10), 1.0));
    }

    #[test]
    fn quadratic_penalty() {
        assert!(approx(level_score(10, 20), 0.25));
        assert!(approx(level_score(10, 50), 0.04));
        assert!(approx(level_score(10, 100), 0.01));
    }

    #[test]
    fn beating_human_is_capped() {
        // agent uses fewer actions than the human -> capped, not unbounded
        assert!(approx(level_score(10, 5), RHAE_CAP));
        assert!(approx(level_score(10, 1), RHAE_CAP));
        assert!(approx(level_score(10, 8), RHAE_CAP)); // squared ratio exceeds 1.15
    }

    #[test]
    fn just_under_cap_is_not_capped() {
        // (1000/933)^2 ≈ 1.149 < 1.15 -> not capped
        assert!(approx(level_score(1000, 933), (1000.0 / 933.0_f64).powi(2)));
    }

    #[test]
    fn zero_agent_actions_is_zero_not_nan() {
        assert_eq!(level_score(10, 0), 0.0);
    }

    #[test]
    fn diagnostic_rhae_is_unweighted() {
        let levels = vec![(10, 10), (10, 20)];
        assert!(approx(rhae(&levels), 0.625));
    }

    #[test]
    fn game_score_weights_later_levels() {
        let human = [10, 10];
        let agent = [10, 20];
        assert!(approx(game_score(&human, &agent), 0.5));
    }

    #[test]
    fn game_score_applies_completion_cap() {
        let human = [10, 10, 10];
        let agent = [1];
        assert!(approx(game_score(&human, &agent), 1.0 / 6.0));
    }

    #[test]
    fn game_score_is_zero_for_no_completed_levels() {
        assert_eq!(game_score(&[10, 10], &[]), 0.0);
    }

    #[test]
    fn game_score_caps_a_completed_game_at_one() {
        assert!(approx(game_score(&[10, 10], &[1, 1]), 1.0));
    }

    #[test]
    fn weighted_mean() {
        let levels = vec![(10, 10, 3.0), (10, 20, 1.0)];
        assert!(approx(rhae_weighted(&levels), 0.8125));
    }

    #[test]
    fn empty_inputs_are_zero() {
        assert_eq!(rhae(&[]), 0.0);
        assert_eq!(rhae_weighted(&[]), 0.0);
    }

    #[test]
    fn actions_at_cap_matches_cap() {
        let human = 10u32;
        let a = actions_at_cap(human);
        assert!(approx(level_score(human, a.floor() as u32), RHAE_CAP));
        assert!(approx(level_score(human, (a.floor() as u32) + 1), 1.0));
    }
}
