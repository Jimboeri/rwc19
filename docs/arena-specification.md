# Arena Application Specification

## 1. Purpose

Arena is a generalized prediction-competition platform. A superadmin provisions any number of independent **competitions** - a whole tournament (e.g. a Rugby World Cup or an NPC season) or a short series (e.g. an All Blacks tour). Within each competition, administrators manage teams, rounds, games and payments, and players predict game results and winning margins. Points are calculated by a per-competition rules engine once a game is marked finished.

This specification describes the behavior implemented by `swim/arena`. It supersedes the per-tournament `rwc19`/`rwc23` apps for new competitions; those apps are kept unmodified as frozen archives at their existing URLs (`/rwc19/`, `/rwc23/`) and are not part of this spec.

This is a living document - update it whenever `arena`'s models, views, URLs, or scoring contract change.

## 2. Actors

### Superadmin

A Django `is_superuser` account. Can:
- Create, edit and archive competitions, including a competition's scoring rules.
- Assign or remove per-competition administrators.
- Do everything an administrator or player can do, in any competition.

### Administrator

A user with a `Membership.role = ADMIN` in a specific competition. Scoped to that competition only - being an admin of one competition grants no rights in another. Can:
- Manage that competition's teams and rounds.
- Add games to a round and edit game scores/results.
- Edit any player's predictions for a game and mark individual predictions as an `override` (excluded from automatic recalculation).
- Recalculate round statuses on demand.
- Manage player contact details, block a player, and record/View payments.

### Player

Any authenticated user with a `Membership` (of either role) in a competition. Can:
- Join a `PUBLIC` competition that is `OPEN` or `ACTIVE`.
- Belong to multiple competitions simultaneously with a single account.
- View the current round, submit/update predictions for games that haven't started, and view the round leaderboard.
- View their own history, other rounds, other players' round results, and individual game/points detail.

## 3. Competition Concepts

### Competition

- `name`, `slug` (unique, used in all competition-scoped URLs).
- `kind`: `TOURNAMENT` / `SERIES` / `LEAGUE` / `OTHER` - a display label only; it does not change behavior. A whole-tournament competition and a short tour series are modeled identically (a `Competition` with one or more `Round`s).
- `status`: `DRAFT` / `OPEN` / `ACTIVE` / `FINISHED` / `ARCHIVED`.
- `visibility`: `PUBLIC` (anyone can browse and join) or `INVITE` (membership must be granted directly - there is currently no in-app invite flow beyond a superadmin/admin adding a `Membership`).
- `default_entry_fee`, overridable per round.
- `scoring_rules`: a JSON Decision Model (JDM) graph evaluated by the GoRules ZEN Engine - see §4.

### Membership

Joins a `User` to a `Competition` with a `role` (`ADMIN`/`PLAYER`), plus per-competition profile fields: `phone_number`, `blocked`, `fully_paid`. One `(user, competition)` pair is unique - a user has independent role/payment/contact state in each competition they belong to.

### Team, Round, Game

Scoped to a single competition (`Team.competition`, `Round.competition`, `Game.round`). Semantics match the original `rwc23` app:
- A `Round` has an `order`, a `status` (`N`/`C`/`F`), and an optional `entry_fee` override.
- The current round is the first round with status `C`. Round statuses are only recalculated when a competition admin explicitly triggers it (`Competition.refresh_round_statuses()`) - never as a side effect of a player viewing a page.
- A `Game` has two teams, an optional date, two scores, and a `finished` flag. `Game.result()` returns `0` (not finished), `1`/`2` (team win) or `3` (draw); `Game.spread()` is the absolute score difference once finished.

### PlayerRound and Prediction

- A `PlayerRound` joins a `Membership` to a `Round` and stores the calculated `total_points` and payment fields (`paid`, `paid_amount`).
- A `Prediction` belongs to one `PlayerRound` and one `Game`, storing the player's `result` selection (`0` none, `1`/`2` team win, `3` draw), predicted `spread`, calculated `points`, and an `override` flag (set by an admin to exclude a prediction from automatic recalculation).
- `(membership, round)` and `(player_round, game)` are both unique - enforced at the database level.

## 4. Scoring via a rules engine

Scoring is **not** a hard-coded formula. Each competition owns a `scoring_rules` JDM decision graph (GoRules ZEN Engine, `zen-engine` package). `Prediction.calc_score()` is a thin adapter (`arena/models.py`) that, once a game is finished, builds a facts dict and asks the engine for a point value (`arena/rules.py`):

```json
{
  "predictedResult": 0,
  "actualResult": 0,
  "predictedSpread": 0,
  "actualSpread": 0
}
```

- `predictedResult` / `actualResult`: `0` none/not finished, `1` team1 win, `2` team2 win, `3` draw.
- `predictedSpread` / `actualSpread`: the player's predicted margin and the actual final margin.

The engine's decision table must return an object with a numeric `points` field. All scoring policy - what counts as a correct pick, how margin difference maps to points, any draw bonus, any minimum-points floor - lives entirely inside the JDM graph, authored by a superadmin as raw JSON (no visual editor is built). **A competition cannot be scored until its `scoring_rules` are set** - there is no implicit default. If rules are missing or fail to evaluate, `calc_score()` records `0` points and logs a warning rather than raising into a page.

`swim/arena/rules/example_margin_scoring.json` is a worked example reproducing the classic RWC scoring exactly (20 minus margin difference, floor of 5 for a correct winner pick, 25 for a correct draw, 0 otherwise) as a genuine decision table, intended as a copy-paste starting point for a new competition - it is never auto-attached.

## 5. Main Workflows

### Registration and activation

Unchanged in spirit from `rwc23`: signup creates an inactive `User`, sends an activation email, and activation marks the user active. Unlike `rwc23`, activation does **not** create any competition-specific records - those are created when the user explicitly joins a competition (see below), since a user isn't tied to a single competition anymore.

### Joining a competition

1. A logged-in user browses public, joinable (`OPEN`/`ACTIVE`) competitions from their dashboard.
2. Joining creates a `Membership` (role `PLAYER`) and calls `Membership.ensure_player_rounds()`, which creates a `PlayerRound` and predictions for every existing round/game in that competition.
3. Invite-only competitions have no self-service join - a superadmin or that competition's admin must create the `Membership` directly (admin console/Django admin).

### Making predictions

Same as `rwc23`: a pick-update page lists editable predictions for games that haven't started and read-only past predictions for games that have. Saving a `3` (draw) selection always zeroes the stored spread.

### Recording a game result

A competition admin edits a game's scores and `finished` flag, and may edit/override any player's prediction for that game. When a game is marked finished, its `result_text` is computed and every non-overridden prediction is recalculated through the competition's rules engine; each affected `PlayerRound.total_points` is recalculated.

### Payment administration

Unchanged in spirit from `rwc23`: an admin edits `paid`/`paid_amount` per `PlayerRound`; a round counts as paid once `paid_amount >= round.effective_entry_fee`; `Membership.fully_paid` is true only when every round meets its fee. A "mark fully paid" action sets every round's `paid_amount` to its effective entry fee.

## 6. URL Contract

Namespace: `arena`, mounted at the site root (`/`). See `swim/arena/urls.py` for the authoritative list. Summary:

| Area | Routes |
| --- | --- |
| Player | `/`, `/join/<slug>/`, `/c/<slug>/`, `/c/<slug>/pickupdate/<round_id>/`, `/c/<slug>/player/<user_id>/`, `/c/<slug>/game/view/<game_id>/`, `/c/<slug>/otherrounds/`, `/c/<slug>/disprounds/<user_id>/<round_id>/`, `/c/<slug>/pointsview/<prediction_id>/`, `/c/<slug>/about/` |
| Competition admin | `/c/<slug>/admin/teams/`, `/c/<slug>/admin/rounds/`, `/c/<slug>/admin/rounds/<round_id>/games/`, `/c/<slug>/admin/game/edit/<game_id>/`, `/c/<slug>/admin/players/`, `/c/<slug>/admin/player/<user_id>/`, `/c/<slug>/admin/player/<user_id>/payment/` |
| Superadmin | `/superadmin/competitions/`, `/superadmin/competitions/new/`, `/superadmin/competitions/<slug>/edit/`, `/superadmin/competitions/<slug>/admins/` |
| Auth | `/signup/`, `/activate/<uidb64>/<token>/`, `/login/`, `/logout/`, `/password-reset/...` |

`rwc19` and `rwc23` keep their own existing URL prefixes (`/rwc19/`, `/rwc23/`) untouched.

## 7. Access control

- `competition_member_required` (`arena/permissions.py`): requires a `Membership` in the competition named by the URL's `slug`; redirects to the join page for a public competition the user hasn't joined yet, otherwise 403.
- `competition_admin_required`: requires `is_superuser` or an unblocked `Membership(role=ADMIN)` in that competition.
- `superadmin_required`: requires `is_superuser`.
- Both member/admin decorators stash the resolved `Competition` on `request.competition`, which a context processor (`arena/context_processors.py`) uses to expose `competition` and `is_admin` in every template automatically.

## 8. UI separation

Player-facing views/templates/static assets are mobile-first (`arena/views/player.py`, `templates/arena/player/`, `static/arena/player.css`) - single column, large tap targets, no JS framework dependency. Competition-admin and superadmin views/templates/static assets assume a laptop-width viewport (`arena/views/admin.py`, `arena/views/superadmin.py`, `templates/arena/admin/`, `static/arena/admin.css`) - denser tables, a persistent sidebar. Both are server-rendered Django templates; there is no separate JSON API or SPA.

## 9. Configuration Dependencies

In addition to `rwc23`'s existing requirements (PostgreSQL, SMTP, secret key/DB credentials from the environment):
- `zen-engine` (GoRules ZEN Engine Python bindings) must be installed - see `requirements.txt`. It ships prebuilt wheels; no Rust toolchain is required.
- `ARENA_WEB_BASE_URL` environment variable (optional) is used as a fallback base URL in activation emails.

## 10. Known Limitations

- A `Game` with no `gamedate` set is silently excluded from the player pick form (`pick_update`'s `exclude(game__gamedate__lt=timezone.now())` never matches a `NULL` gamedate under SQL's three-valued logic, and `.exclude()` does not include `NULL` rows by default). Inherited from the same pattern in `rwc23`. Admins should always set a game's date when creating it.
- There is no in-app UI to invite a specific user to an `INVITE`-only competition; membership must be created via the superadmin/admin console or Django admin.
- `scoring_rules` are authored as raw JSON with no visual editor or schema validation beyond what the engine itself enforces at evaluation time.
- `swim/arena/rules/example_margin_scoring.json` has been executed against a live `zen-engine==2.0.2` install inside the project's Docker image and confirmed to reproduce the classic scoring table exactly (draw, exact-margin win, the 15+ margin floor, wrong result, and no-selection cases). Re-verify it the same way (inside Docker, never on the host - see `CLAUDE.md`) if the engine version or the ruleset changes.

## 11. Source of Truth

Derived from `swim/arena/models.py`, `forms.py`, `views/`, `urls.py`, `permissions.py`, `rules.py`, `templates/`, and `swim/arena/tests/`.
