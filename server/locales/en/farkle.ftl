game-name-farkle = Farkle

farkle-roll = Roll { $count } { $count ->
    [one] die
   *[other] dice
}
farkle-bank = Bank { $points } points

farkle-take-single-one = Single 1 for { $points } points
farkle-take-single-five = Single 5 for { $points } points
farkle-take-three-kind = Three { $number }s for { $points } points
farkle-take-four-kind = Four { $number }s for { $points } points
farkle-take-five-kind = Five { $number }s for { $points } points
farkle-take-six-kind = Six { $number }s for { $points } points
farkle-take-small-straight = Small straight for { $points } points
farkle-take-large-straight = Large straight for { $points } points
farkle-take-three-pairs = Three pairs for { $points } points
farkle-take-double-triplets = Double triplets for { $points } points
farkle-take-full-house = Four of a kind with a pair for { $points } points

farkle-you-roll = You roll { $count } { $count ->
    [one] die
   *[other] dice
}.
farkle-player-rolls = { $player } rolls { $count } { $count ->
    [one] die
   *[other] dice
}.
farkle-you-roll-brief = You roll { $count }.
farkle-player-rolls-brief = { $player } rolls { $count }.
farkle-roll-result = The dice show: { $dice }.
farkle-roll-result-brief = Dice: { $dice }.

farkle-you-farkle = FARKLE! You lose { $points } turn points.
farkle-player-farkles = FARKLE! { $player } loses { $points } turn points.
farkle-you-farkle-brief = Farkle: you lose { $points }.
farkle-player-farkles-brief = Farkle: { $player } loses { $points }.

farkle-you-take-combo = You keep { $combo } for { $points } points.
farkle-player-takes-combo = { $player } keeps { $combo } for { $points } points.
farkle-you-take-combo-brief = You: { $combo }, +{ $points }.
farkle-player-takes-combo-brief = { $player }: { $combo }, +{ $points }.

farkle-you-hot-dice = Hot dice! You scored all six dice and may roll all six again.
farkle-player-hot-dice = Hot dice! { $player } scored all six dice and may roll all six again.
farkle-you-hot-dice-brief = You: hot dice.
farkle-player-hot-dice-brief = { $player }: hot dice.

farkle-you-bank = You bank { $points } points. Your total is now { $total }.
farkle-player-banks = { $player } banks { $points } points for a total of { $total }.
farkle-you-bank-brief = You bank { $points}; total { $total }.
farkle-player-banks-brief = { $player } banks { $points}; total { $total }.

farkle-you-win = You win with { $score } points!
farkle-winner = { $player } wins with { $score } points!
farkle-you-win-brief = You win: { $score }.
farkle-winner-brief = { $player } wins: { $score }.
farkle-winners-tie = Tie at the target! Tiebreaker players: { $players }.
farkle-tiebreaker-round-start = Tiebreaker round { $round }. Still competing: { $players }.

farkle-your-turn-score = You have { $points } points in this turn.
farkle-turn-score = { $player } has { $points } points in this turn.
farkle-no-turn = No one is currently taking a turn.

farkle-set-target-score = Target score: { $score }
farkle-enter-target-score = Enter target score (500-5000):
farkle-option-changed-target = Target score set to { $score }.

farkle-set-entrance-score = Minimum entrance score: { $score }
farkle-enter-entrance-score = Enter minimum entrance score (0-5000):
farkle-option-changed-entrance = Minimum entrance score set to { $score }.

farkle-set-bank-score = Minimum bank score: { $score }
farkle-enter-bank-score = Enter minimum bank score (0-5000):
farkle-option-changed-bank = Minimum bank score set to { $score }.

farkle-error-entrance-above-target = The minimum entrance score ({ $entrance }) cannot be higher than the target score ({ $target }).
farkle-error-bank-above-target = The minimum bank score ({ $bank }) cannot be higher than the target score ({ $target }).

farkle-must-take-combo = You must keep at least one scoring die or combination before rolling again.
farkle-cannot-bank = You can bank only after keeping a scoring die or combination this turn.
farkle-must-reach-entrance-score = You need at least { $points } turn points before banking your first score.
farkle-must-reach-bank-score = You need at least { $points } turn points before banking.
farkle-confirm-risky-roll = You can bank { $points } points now. Rolling again risks losing them; repeat Roll within { $seconds } seconds to confirm.
farkle-invalid-combo-action = That scoring choice is not recognized. Please choose one of the currently listed combinations.
farkle-combo-no-longer-available = That scoring combination is no longer available. The current scoring choices have been refreshed.

farkle-combo-single-1 = Single 1
farkle-combo-single-5 = Single 5
farkle-combo-three-kind = Three { $number }s
farkle-combo-four-kind = Four { $number }s
farkle-combo-five-kind = Five { $number }s
farkle-combo-six-kind = Six { $number }s
farkle-combo-small-straight = Small straight
farkle-combo-large-straight = Large straight
farkle-combo-three-pairs = Three pairs
farkle-combo-double-triplets = Double triplets
farkle-combo-full-house = Four of a kind with a pair

farkle-line-format = { $rank }. { $player }: { $points }
farkle-combo-fallback = { $combo } for { $points } points

farkle-check-turn-score = Check turn score
farkle-roll-label = Roll dice
farkle-bank-label = Bank points
