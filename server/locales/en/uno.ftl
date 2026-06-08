game-name-uno = UNO

# Colors
uno-color-red = Red
uno-color-yellow = Yellow
uno-color-green = Green
uno-color-blue = Blue
uno-color-wild = Wild

# Card names
uno-card-number = { $color } { $value }
uno-card-skip = { $color } Skip
uno-card-reverse = { $color } Reverse
uno-card-draw-two = { $color } Draw Two
uno-card-wild = Wild
uno-card-wild-four = Wild Draw Four

# Options
uno-set-winning-score = Score limit: { $score }
uno-enter-winning-score = Enter score limit
uno-option-changed-winning-score = Score limit set to { $score }.

uno-set-scoring-mode = Scoring: { $mode }
uno-select-scoring-mode = Select scoring mode
uno-option-changed-scoring-mode = Scoring set to { $mode }.
uno-scoring-first = First to limit wins
uno-scoring-elimination = Elimination

uno-set-skip-after-draw = Skip turn after drawing: { $enabled }
uno-option-changed-skip-after-draw = Skip turn after drawing { $enabled }.

uno-set-responses = Stacking responses: { $enabled }
uno-option-changed-responses = Stacking responses { $enabled }.

uno-set-advanced-responses = Advanced responses: { $enabled }
uno-option-changed-advanced-responses = Advanced responses { $enabled }.

uno-set-wait-for-draw-responses = Wait for draw responses: { $enabled }
uno-option-changed-wait-for-draw-responses = Wait for draw responses { $enabled }.

uno-set-bluff = Bluffs: { $enabled }
uno-option-changed-bluff = Bluffs { $enabled }.

uno-set-straights = Straights: { $enabled }
uno-option-changed-straights = Straights { $enabled }.

uno-set-interceptions = Interceptions: { $enabled }
uno-option-changed-interceptions = Interceptions { $enabled }.

uno-set-super-interceptions = Super interceptions: { $enabled }
uno-option-changed-super-interceptions = Super interceptions { $enabled }.

uno-set-zero-seven = Zero / seven rule: { $enabled }
uno-option-changed-zero-seven = Zero / seven rule { $enabled }.

uno-set-free-draws = Free draws per turn: { $count }
uno-enter-free-draws = Enter free draws per turn
uno-option-changed-free-draws = Free draws per turn set to { $count }.

# Option validation
uno-error-advanced-responses-require-responses = Advanced responses require Stacking responses to be enabled.
uno-error-wait-responses-require-responses = Wait for draw responses requires Stacking responses to be enabled.
uno-error-super-interceptions-require-interceptions = Super interceptions require Interceptions to be enabled.

# Actions
uno-draw = Draw
uno-say-uno = UNO
uno-read-top = Read top card
uno-read-color = Read current color
uno-read-counts = Read card counts
uno-read-hand = Read your hand value
uno-sort-color = Sort by color
uno-sort-number = Sort by number

# Gameplay announcements
uno-new-hand = Round { $round }.
uno-start-card = { $player } turns up { $card }.
uno-current-color = Current color: { $color }.
uno-dealt-cards = Everyone is dealt { $cards } cards.
uno-direction-reversed = The direction is reversed.
uno-player-plays = { $player } plays { $card }.
uno-you-play = You play { $card }.
uno-color-chosen = The color is now { $color }.
uno-player-draws-one = { $player } draws a card.
uno-player-draws-many = { $player } draws { $count } cards.
uno-you-draw-one = You draw a card.
uno-you-draw-many = You draw { $count } cards.
uno-cant-play = { $player } can't play.
uno-you-cant-play = You can't play.
uno-you-skipped = You are skipped.
uno-says-uno = { $player } says UNO!
uno-you-say-uno = You say UNO!
uno-callout = { $caller } calls out { $player } for not saying UNO! { $player } draws four.
uno-you-callout = You call out { $player } for not saying UNO! { $player } draws four.
uno-callout-you = { $caller } calls you out for not saying UNO! You draw four.
uno-cannot-play-that = You can't play that card.
uno-reshuffle = Reshuffling the discard pile.
uno-hand-blocked = No one can play. The round ends.

# Bluff challenge
uno-bluff-challenge = Call bluff
uno-bluff-caught = { $player } was bluffing and draws { $count } cards!
uno-you-bluff-caught = You were bluffing and draw { $count } cards!
uno-bluff-wrong = { $player } challenged wrongly and draws { $count } cards!
uno-you-bluff-wrong = You challenged wrongly and draw { $count } cards!

# Zero / seven rule
uno-rotate-hands = Everyone passes their hand!
uno-swap-hands = { $player } swaps hands with { $target }!
uno-you-swap = You swap hands with { $target }!
uno-swap-with-you = { $player } swaps hands with you!
uno-swap-with = Swap hands with { $player }

# Interceptions / straights
uno-player-intercepts = { $player } intercepts with { $card }!
uno-you-intercept = You intercept with { $card }!
uno-bad-intercept = That was not a valid interception. Three penalty points.
uno-not-your-turn = It's not your turn.

# Info
uno-no-top = There is no top card yet.
uno-top-card = { $card }.
uno-color-is = { $color }.
uno-deck-count = deck { $count }
uno-sorting-color = Sorting by color.
uno-sorting-number = Sorting by number.

# Round / game end
uno-round-winner = { $player } wins the round!
uno-you-win-round = You win the round!
uno-round-points-from = { $points } from { $player }
uno-round-details-none = No points were taken from opponents.
uno-round-summary = { $details }. { $player } gains { $total }.
uno-round-summary-you = { $details }. You gain { $total }.
uno-round-points = { $player } had { $points } points left in hand.
uno-eliminated = { $player } has been eliminated!
uno-game-winner = { $player } wins the game with { $score } points!
uno-game-tie = Everyone has been eliminated. The game is a tie!
uno-line-format = { $rank }. { $player }: { $score }

# Hand value (d key)
uno-read-hand-value = { $count ->
    [one] { $count } card
   *[other] { $count } cards
 } worth { $points ->
    [one] { $points } point
   *[other] { $points } points
 }.
