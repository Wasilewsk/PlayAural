game-name-fivecarddraw = Poker Five Card Draw

draw-set-starting-chips = Starting chips: { $count }
draw-enter-starting-chips = Enter starting chips
draw-option-changed-starting-chips = Starting chips set to { $count }.

draw-set-ante = Ante: { $count }
draw-enter-ante = Enter ante amount
draw-option-changed-ante = Ante set to { $count }.

draw-set-turn-timer = Turn timer: { $mode }
draw-select-turn-timer = Select turn timer
draw-option-changed-turn-timer = Turn timer set to { $mode }.

draw-set-raise-mode = Raise mode: { $mode }
draw-select-raise-mode = Select raise mode
draw-option-changed-raise-mode = Raise mode set to { $mode }.

draw-set-max-raises = Maximum raises per betting round: { $count }
draw-enter-max-raises = Enter maximum raises per betting round (0 for unlimited)
draw-option-changed-max-raises = Maximum raises per betting round set to { $count }.

draw-set-draw-limit = Draw rule: { $mode }
draw-select-draw-limit = Select the draw rule
draw-option-changed-draw-limit = Draw rule set to { $mode }.
draw-limit-three-cards = Up to 3 cards (standard)
draw-limit-four-with-ace = Up to 4 cards when keeping an ace

draw-error-ante-too-high = The ante ({ $ante } chips) must be lower than the starting stack ({ $chips } chips) so players can still make betting decisions after the deal.
draw-error-capped-mode-needs-ante = { $mode ->
    [pot_limit] Pot limit
    [double_pot] Double pot limit
   *[other] This capped raise mode
} requires an ante greater than 0 so the first player has a pot-based amount available to bet.

draw-antes-posted = Antes are posted. The pot now contains { $amount } chips.
draw-betting-round-1 = First betting round.
draw-betting-round-2 = Second betting round.
draw-begin-draw = Draw phase. Starting with the first active player to the dealer's left, choose cards to exchange or stand pat.
draw-not-draw-phase = Drawing cards is available only after the first betting round. Continue with the current betting action.
draw-not-betting = Betting is unavailable during the draw phase. Select any cards to exchange, then choose Draw cards.
draw-fold-not-available = Folding is unavailable during the draw phase. Select any cards to exchange, then choose Draw cards.

draw-toggle-discard = Select card { $index } to exchange
draw-card-keep = { $card }
draw-card-discard = { $card }, selected to exchange
draw-draw-cards = Draw cards
draw-draw-cards-count = { $count ->
    [0] Stand pat
    [one] Exchange 1 card
   *[other] Exchange { $count } cards
}
draw-dealt-cards = Your five cards are { $cards }.
draw-you-drew-cards = Your { $count } replacement { $count ->
    [one] card is
   *[other] cards are
} { $cards }.
draw-you-draw = You exchange { $count } { $count ->
    [one] card
   *[other] cards
}.
draw-player-draws = { $player } exchanges { $count } { $count ->
    [one] card
   *[other] cards
}.
draw-you-stand-pat = You stand pat and keep all five cards.
draw-player-stands-pat = { $player } stands pat and keeps all five cards.
draw-you-discard-limit = You may exchange no more than { $count } cards under the selected draw rule.
draw-four-requires-kept-ace = Exchanging 4 cards requires you to keep at least one ace. Deselect an ace or exchange no more than 3 cards.

draw-raise-invalid = Enter a whole number greater than 0 for the amount to raise.
draw-raise-cap-reached = The limit of { $count } raises has already been reached in this betting round. You may call or fold.
draw-raise-over-stack = You tried to raise by { $requested } chips, but you have only { $chips } chips remaining. Enter a smaller raise or choose All in.
draw-raise-too-small = You tried to raise by { $requested } chips. The minimum raise is { $minimum } chips.
draw-raise-over-limit = You tried to raise by { $requested } chips. Under { $mode ->
    [pot_limit] pot limit
    [double_pot] double pot limit
   *[other] the selected raise mode
}, the largest raise available after calling is { $maximum } chips.
draw-all-in-over-limit = You cannot go all in with your remaining { $stack } chips because { $mode ->
    [pot_limit] pot limit
    [double_pot] double pot limit
   *[other] the selected raise mode
} currently allows a raise of at most { $maximum } chips after calling. Use Raise to enter an allowed amount.
draw-all-in-raise-cap-reached = You cannot go all in as a full raise because the limit of { $count } raises has already been reached. You may call or fold.
draw-all-in-unavailable-raise-cap = All in is unavailable because it would be a full raise after the raise limit was reached. You may call or fold.
draw-all-in-unavailable-limit = All in is unavailable because your stack exceeds the current betting limit. Use Raise to enter an allowed amount.
draw-raise-unavailable-cap = Raising is unavailable because this betting round has reached its raise limit.
draw-raise-unavailable-limit = A full raise is unavailable with your stack and the current betting limit. You may call, fold, or use All in when it is legal.

draw-current-bet = The current table bet is { $amount } chips.
draw-raise-range = The minimum raise is { $minimum } chips. You can raise by up to { $maximum } chips after calling.
draw-no-full-raise-available = You need { $to_call } chips to call and have { $chips } chips remaining, so you cannot make a full raise. You may call all in or fold.
draw-dealer-unavailable = There is no dealer position for the current hand yet.
draw-position-unavailable = You are not active in the current hand, so you do not have a betting position.

draw-card-key = Card key { $index }

draw-winner-chips = { $rank }. { $player }: { $chips } { $chips ->
    [one] chip
   *[other] chips
}
