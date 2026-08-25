"""
Thin adapter around the GoRules ZEN Engine (`zen-engine` package).

Each Competition owns a JDM (JSON Decision Model) decision graph in
`Competition.scoring_rules`. All scoring *policy* (what counts as a correct
pick, how margin difference maps to points, the draw bonus, the minimum
points floor for a correct winner pick) lives inside that graph, authored
by a superadmin - this module only feeds facts in and reads points back out.
"""
import json
import logging

import zen

logger = logging.getLogger(__name__)

_engine = None


class ScoringRulesError(Exception):
    """Raised when a competition's scoring rules are missing or fail to evaluate."""


def _get_engine():
    global _engine
    if _engine is None:
        _engine = zen.ZenEngine()
    return _engine


def evaluate_score(competition, facts):
    """
    Evaluate `competition.scoring_rules` against `facts` and return the
    resulting points as a float.

    Raises ScoringRulesError if the competition has no rules configured,
    or if the rules fail to evaluate or don't produce a numeric `points`
    output. Callers should treat this as "cannot score right now" rather
    than let it crash a page - see Prediction.calc_score().
    """
    if not competition.scoring_rules:
        raise ScoringRulesError(
            f"Competition '{competition}' has no scoring_rules configured."
        )

    try:
        decision = _get_engine().create_decision(json.dumps(competition.scoring_rules))
        response = decision.evaluate(facts)
    except Exception as exc:
        raise ScoringRulesError(
            f"Failed to evaluate scoring rules for competition '{competition}': {exc}"
        ) from exc

    output = response.get("result", response) if isinstance(response, dict) else response
    points = output.get("points") if isinstance(output, dict) else None
    if points is None:
        raise ScoringRulesError(
            f"Scoring rules for competition '{competition}' did not return a "
            f"'points' output (got {output!r})."
        )
    return float(points)
