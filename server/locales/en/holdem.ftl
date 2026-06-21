game-name-holdem = Poker Texas Hold'em

holdem-set-starting-chips = Starting chips: { $count }
holdem-enter-starting-chips = Enter starting chips
holdem-option-changed-starting-chips = Starting chips set to { $count }.

holdem-set-big-blind = Big blind: { $count }
holdem-enter-big-blind = Enter big blind
holdem-option-changed-big-blind = Big blind set to { $count }.

holdem-set-ante = Ante: { $count }
holdem-enter-ante = Enter ante
holdem-option-changed-ante = Ante set to { $count }.

holdem-set-ante-start = Ante starts at level: { $count }
holdem-enter-ante-start = Enter blind level to enable ante
holdem-option-changed-ante-start = Ante start level set to { $count }.

holdem-set-turn-timer = Turn timer: { $mode }
holdem-select-turn-timer = Select turn timer
holdem-option-changed-turn-timer = Turn timer set to { $mode }.

holdem-set-blind-timer = Blind timer: { $mode }
holdem-select-blind-timer = Select blind timer
holdem-option-changed-blind-timer = Blind timer set to { $mode }.

holdem-set-raise-mode = Raise mode: { $mode }
holdem-select-raise-mode = Select raise mode
holdem-option-changed-raise-mode = Raise mode set to { $mode }.

holdem-set-max-raises = Maximum raises per betting round: { $count }
holdem-enter-max-raises = Enter maximum raises per betting round (0 for unlimited)
holdem-option-changed-max-raises = Maximum raises per betting round set to { $count }.

holdem-error-big-blind-too-high = The big blind ({ $blind } chips) must be lower than the starting stack ({ $chips } chips).
holdem-error-ante-too-high = The ante ({ $ante } chips) must be lower than the starting stack ({ $chips } chips).
holdem-error-forced-bets-too-high = With antes active from level 0, the ante plus big blind ({ $ante } + { $blind } chips) must be lower than the starting stack ({ $chips } chips).

holdem-antes-posted = Antes are posted. The pot now contains { $amount } chips.
holdem-you-post-small-blind = You post the small blind ({ $sb } chips). { $bb_player } posts the big blind ({ $bb } chips).
holdem-you-post-big-blind = { $sb_player } posts the small blind ({ $sb } chips). You post the big blind ({ $bb } chips).
holdem-players-post-blinds = { $sb_player } posts the small blind ({ $sb } chips). { $bb_player } posts the big blind ({ $bb } chips).

holdem-raise-invalid = Enter a whole number greater than 0 for the amount to raise.
holdem-raise-cap-reached = The limit of { $count } raises has already been reached in this betting round. You may call or fold.
holdem-raise-over-stack = You tried to raise by { $requested } chips, but you have only { $chips } chips remaining. Enter a smaller raise or choose All in.
holdem-raise-too-small = You tried to raise by { $requested } chips. The minimum raise is { $minimum } chips.
holdem-raise-over-limit = You tried to raise by { $requested } chips. Under { $mode ->
    [pot_limit] pot limit
    [double_pot] double pot limit
   *[other] the selected raise mode
}, the largest raise available after calling is { $maximum } chips.
holdem-all-in-over-limit = You cannot go all in with your remaining { $stack } chips because { $mode ->
    [pot_limit] pot limit
    [double_pot] double pot limit
   *[other] the selected raise mode
} currently allows a raise of at most { $maximum } chips after calling. Use Raise to enter an allowed amount.
holdem-all-in-raise-cap-reached = You cannot go all in as a full raise because the limit of { $count } raises has already been reached. You may call or fold.
holdem-all-in-unavailable-raise-cap = All in is unavailable because it would be a full raise after the raise limit was reached. You may call or fold.
holdem-all-in-unavailable-limit = All in is unavailable because your stack exceeds the current betting limit. Use Raise to enter an allowed amount.
holdem-raise-unavailable-cap = Raising is unavailable because this betting round has reached its raise limit.
holdem-raise-unavailable-limit = A full raise is unavailable with your stack and the current betting limit. You may call, fold, or use All in when it is legal.

holdem-current-bet = The current table bet is { $amount } chips.
holdem-raise-range = The minimum raise is { $minimum } chips. You can raise by up to { $maximum } chips after calling.
holdem-no-full-raise-available = You need { $to_call } chips to call and have { $chips } chips remaining, so you cannot make a full raise. You may call all in or fold.
holdem-button-unavailable = There is no button position for the current hand yet.
holdem-position-unavailable = You are not active in the current hand, so you do not have a betting position.
holdem-reveal-no-live-hand = You can reveal hole cards only when you reached showdown with a live hand.
holdem-private-hand-unavailable = You are out of chips and no longer have a live hand to read.

holdem-winner-chips = { $rank }. { $player }: { $chips } { $chips ->
    [one] chip
   *[other] chips
}
