# RWC23 Application Specification

## 1. Purpose

RWC23 is a web application for running a rugby prediction competition. Authenticated players predict the result and winning margin of each game. The application calculates points after results are entered and provides round standings, player history, and payment administration.

This specification describes the behavior implemented by `swim/rwc23`.

## 2. Actors

### Player

A player can:

- Register with an email address, first name, surname, and password.
- Activate the account from an emailed activation link.
- Sign in and sign out.
- View the current round and standings.
- Submit or update predictions for games that have not started.
- View past predictions, game results, points, and other rounds.
- View player details and the about page.

### Staff user

A staff user has all player capabilities and can additionally:

- View all registered players.
- Create missing player-round and prediction records.
- Edit game scores and completion status.
- Review and edit every prediction for a game.
- Recalculate game results and player-round totals.
- Record round payments.
- Mark a player fully paid across all rounds.

### Superuser

A superuser additionally drives current-round status calculation when opening the current-round view. The implementation relies on Django's built-in `is_superuser` flag for this behavior.

## 3. Competition Concepts

### Round

A competition consists of ordered rounds. A round has:

- A display name.
- An integer order.
- Optional start and finish timestamps.
- Started and finished flags.
- A one-character status.
- An entry fee, defaulting to 5.

The status values used by the application are:

| Status | Meaning |
| --- | --- |
| `N` | Not current / not started |
| `C` | Current round |
| `F` | Finished round |

The current round is the first round with status `C`.

### Team

A team has a name, optional description, optional pool, and a three-character display code. Teams are displayed alphabetically by name.

### Game

A game belongs to one round and has two teams, an optional date, two non-negative scores, a finished flag, a high-point value, an average value, and optional result text.

Games are ordered by round and date. A game is considered started when its date is earlier than the current time. Predictions for started games are excluded from the player pick form.

### Player round

A player-round joins a Django user to a round. It stores:

- Calculated total points.
- Last update timestamp.
- Paid flag.
- Amount paid.

A player-round is created as needed. It receives one prediction for every game in its round.

### Prediction

A prediction belongs to one player-round and one game. It stores:

- Result selection: `0` no selection, `1` team 1 wins, `2` team 2 wins, or `3` draw.
- Predicted winning margin.
- Calculated points.
- An override flag.
- Last update timestamp.

Predictions are ordered by game date.

## 4. Scoring Rules

Scoring is applied only after a game is marked finished.

1. A correct draw prediction scores 25 points.
2. A correct winning-team prediction scores `20 - absolute(actual_margin - predicted_margin)`.
3. A correct winning-team prediction scores at least 5 points, even when the margin differs by more than 15.
4. An incorrect result selection scores 0 points.
5. A prediction with no result selection scores 0 points.
6. A player receives no points for a game whose prediction was not submitted before the game started, because started games are excluded from the pick form.
7. A draw prediction always has a spread of 0 when saved through the pick or game administration workflows.

A player's round total is the sum of points from finished games in that round. Recalculation updates both each prediction's points and the stored player-round total.

## 5. Main Workflows

### Registration and activation

1. An unauthenticated visitor submits the signup form.
2. The application creates an inactive Django user and an associated profile.
3. An activation email is sent using the configured SMTP backend.
4. The activation link validates the user and token.
5. On successful activation, the user is marked active and player-round and prediction records are created for all existing rounds and games.
6. The user is redirected to login.

### Viewing the current round

1. A logged-in user opens the RWC23 index.
2. A superuser updates round statuses based on whether all games in each round are finished.
3. The current round is selected by status `C`.
4. The user's player-round is created if necessary.
5. Missing predictions for current-round games are created.
6. The user's total is recalculated.
7. The page displays the current round, the user's predictions, and the round leaderboard.

### Making predictions

1. A player opens a round's pick-update page.
2. Existing predictions for started games are shown as past predictions.
3. Predictions for games not yet started are displayed in an editable formset.
4. The player selects a result and, for a win, a predicted spread.
5. Valid submissions are saved and the player is redirected to the round display.

### Recording a game result

1. A staff user opens a game administration page.
2. The user enters both scores and marks the game finished when appropriate.
3. Staff may edit all associated predictions and their override flags.
4. When a game is finished, its result text is generated.
5. Predictions without an override are recalculated.
6. Each affected player-round total is recalculated.

### Payment administration

1. A staff user opens a player's payment page.
2. Payment status and amount are edited per player-round.
3. A round is considered paid when `paidAmount` is at least that round's entry fee.
4. The player's `FullyPaid` profile flag is true only when every player-round meets its entry fee.
5. The full-payment action marks every round paid and sets each amount to the round entry fee.

## 6. URL Contract

The application namespace is `rwc23`.

| Route | Name | Access | Purpose |
| --- | --- | --- | --- |
| `/` | `index` | Login required | Current round and leaderboard |
| `/pickupdate/<round>/` | `pickUpdate` | Login required | Edit predictions |
| `/player/<player>/` | `playerDets` | Login required | Player details |
| `/game/edit/<game>/` | `gameEdit` | Login required; intended for staff | Edit game and predictions |
| `/game/view/<game>/` | `gameView` | Login required | View game predictions/results |
| `/about/` | `about` | Login required | About page |
| `/otherrounds/` | `otherRounds` | Login required | List rounds |
| `/disprounds/<player>/<round>/` | `dispRound` | Login required | Show a player's round |
| `/pointsView/<prediction>/` | `pointsView` | Login required | Show prediction points |
| `/admin/users/` | `adminUsers` | Staff required | Manage players |
| `/admin/user/detail/<player>` | `adminUserDetail` | Staff required | Edit player profile |
| `/admin/user/payment/<player>` | `adminUserPayment` | Staff required | Edit payments |
| `/admin/user/fullpayment/<player>` | `adminUserFullPayment` | Staff required | Mark fully paid |
| `/admin/general/` | `adminGeneral` | No explicit check in view | Populate player-rounds and recalculate totals |
| `/email_results/<game>/` | `email_results` | Login required | Process result email workflow |
| `/signup/` | `signup` | Anonymous | Register |
| `/activate/.../` | `activate` | Anonymous | Activate account |
| `/login/` | `login` | Anonymous | Authenticate |
| `/logout/` | `logout` | Logged-in flow | Sign out |
| `/password-reset/` | `password_reset` | Anonymous | Start password reset |

Django's built-in account URLs are also included below `/accounts/`.

## 7. Persistence and Relationships

- `Profile.user` is a one-to-one relationship with Django's built-in `User`.
- `Game.Team1` and `Game.Team2` reference `Team` and are deleted with the team.
- `Game.Round` references `Round` and is deleted with the round.
- `PlayerRound.player` references `User` and `PlayerRound.round` references `Round`.
- `Prediction.game` references `Game` and `Prediction.playerRound` references `PlayerRound`.
- Deleting a user, round, game, or player-round cascades to dependent records according to these relationships.
- The model layer does not currently declare uniqueness constraints for team names, player-round pairs, or prediction pairs. Creation workflows use `get_or_create` in many places, but the database does not enforce those invariants.

## 8. Configuration Dependencies

The app requires:

- Django settings configured for PostgreSQL.
- A PostgreSQL database reachable as `db` in the Docker Compose network.
- SMTP settings for activation and password-reset mail.
- A secret key and database credentials supplied by the container environment.

The application is currently served by Django's development server in Compose. A production deployment should use a production WSGI/ASGI server and configure `DEBUG`, allowed hosts, secure cookies, CSRF origins, static files, and email credentials per environment.

## 9. Known Implementation Gaps

These are observations from the current `rwc23` implementation, not requirements for a rewrite:

- Several administrative views check `is_staff`, but `gameEdit`, `adminGeneral`, and `email_results` do not consistently enforce staff authorization.
- `adminGeneral` has no explicit login or staff decorator.
- The scoring and total-calculation methods save from inside read-like operations, which can cause repeated writes during page views.
- Payment amounts use floating-point fields rather than a fixed-precision monetary type.
- The registration email duplicate check queries `username` while registration uses the email as the username; this should be made explicit and unique at the database level.
- URL patterns contain escaped hyphens in normal Python strings, producing warnings on current Python versions.
- There are limited automated tests in `rwc23/tests.py`; scoring, permissions, registration, activation, payment, and round-state transitions need dedicated coverage.

## 10. Source of Truth

This specification was derived from:

- `swim/rwc23/models.py`
- `swim/rwc23/forms.py`
- `swim/rwc23/views.py`
- `swim/rwc23/urls.py`
- `swim/rwc23/migrations/0001_initial.py` through `0022_team_code.py`
- `swim/rwc23/templates/`
