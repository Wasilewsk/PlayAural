"""Combat/War system for Age of Heroes."""

from __future__ import annotations
import random
from typing import TYPE_CHECKING

from .cards import Card, CardType, EventType, get_card_name
from .state import (
    WarState,
    WarGoal,
    get_war_goal_name,
    get_tribe_name,
)

if TYPE_CHECKING:
    from .game import AgeOfHeroesGame, AgeOfHeroesPlayer


def _brief_enabled(game: AgeOfHeroesGame, user) -> bool:
    brief_checker = getattr(game, "_wants_brief", None)
    return bool(brief_checker(user)) if brief_checker else False


def _broadcast_l_with_brief(
    game: AgeOfHeroesGame,
    full_key: str,
    brief_key: str,
    **kwargs,
) -> None:
    for player in game.players:
        user = game.get_user(player)
        if not user:
            continue
        key = brief_key if _brief_enabled(game, user) else full_key
        user.speak_l(key, buffer="game", **kwargs)


def can_declare_war(game: AgeOfHeroesGame, player: AgeOfHeroesPlayer) -> str | None:
    """Check if a player can declare war. Returns error message or None."""
    if not player.tribe_state:
        return "ageofheroes-war-no-tribe"

    # Need at least one available army OR a hero card (heroes can substitute for armies)
    available_armies = player.tribe_state.get_available_armies()
    hero_count = sum(
        1
        for card in player.hand
        if card.card_type == CardType.EVENT and card.subtype == EventType.HERO
    )

    if available_armies < 1 and hero_count < 1:
        return "ageofheroes-war-no-army"

    # Need at least one valid target
    if not get_valid_war_targets(game, player):
        return "ageofheroes-war-no-targets"

    return None


def get_valid_war_targets(
    game: AgeOfHeroesGame, player: AgeOfHeroesPlayer
) -> list[tuple[int, AgeOfHeroesPlayer]]:
    """Get list of valid war targets (player_index, player)."""
    targets = []
    active_players = game.get_active_players()
    player_index = active_players.index(player)

    for i, p in enumerate(active_players):
        if i == player_index:
            continue
        if not hasattr(p, "tribe_state") or not p.tribe_state:
            continue
        if p.tribe_state.is_eliminated():
            continue

        # Can attack anyone (for simplicity)
        # In classic rules, might be limited to neighbors without roads
        targets.append((i, p))

    return targets


def get_valid_war_goals(
    game: AgeOfHeroesGame,
    attacker: AgeOfHeroesPlayer,
    defender: AgeOfHeroesPlayer,
) -> list[str]:
    """Get list of valid war goals against a specific defender."""
    goals = []

    if not defender.tribe_state:
        return goals

    # Conquest - only available from Day 3 onwards (prevents early game rush)
    if defender.tribe_state.cities > 0 and game.current_day >= 3:
        goals.append(WarGoal.CONQUEST)

    # Plunder - can always try to steal cards (if defender has any)
    if len(defender.hand) > 0:
        goals.append(WarGoal.PLUNDER)

    # Destruction - can destroy monument progress (if defender has any)
    if defender.tribe_state.monument_progress > 0:
        goals.append(WarGoal.DESTRUCTION)

    return goals


def declare_war(
    game: AgeOfHeroesGame,
    attacker: AgeOfHeroesPlayer,
    defender_index: int,
    goal: str,
) -> bool:
    """Declare war on another player."""
    active_players = game.get_active_players()

    if defender_index < 0 or defender_index >= len(active_players):
        return False

    attacker_index = active_players.index(attacker)
    defender = active_players[defender_index]

    if not hasattr(defender, "tribe_state") or not defender.tribe_state:
        return False

    # Initialize war state
    game.war_state = WarState(
        attacker_index=attacker_index,
        defender_index=defender_index,
        goal=goal,
    )

    # Announce war declaration
    game.play_sound("game_ageofheroes/war.ogg")

    for p in game.players:
        user = game.get_user(p)
        if user:
            locale = user.locale
            goal_name = get_war_goal_name(goal, locale)
            user.speak_l(
                "ageofheroes-war-declare",
                attacker=attacker.name,
                defender=defender.name,
                goal=goal_name,
                buffer="game",
            )

    return True


def check_olympics_defense(game: AgeOfHeroesGame) -> AgeOfHeroesPlayer | None:
    """Check if defender has Olympic Games card to cancel war."""
    active_players = game.get_active_players()
    war = game.war_state

    if war.defender_index < 0 or war.defender_index >= len(active_players):
        return None

    defender = active_players[war.defender_index]
    if not hasattr(defender, "hand"):
        return None

    # Check if defender has Olympic Games
    for card in defender.hand:
        if card.card_type == CardType.EVENT and card.subtype == EventType.OLYMPICS:
            return defender

    return None


def use_olympics(game: AgeOfHeroesGame, player: AgeOfHeroesPlayer) -> bool:
    """Use Olympic Games to cancel war."""
    # Find and remove Olympics card
    for i, card in enumerate(player.hand):
        if card.card_type == CardType.EVENT and card.subtype == EventType.OLYMPICS:
            removed = player.hand.pop(i)
            game.discard_pile.append(removed)

            # Cancel the war
            game.war_state.cancelled_by_olympics = True
            game.play_sound("game_ageofheroes/olympics.ogg")

            game.broadcast_personal_l(
                player,
                "ageofheroes-you-cancel-war-with-olympics",
                "ageofheroes-player-cancels-war-with-olympics",
                buffer="game",
            )
            return True

    return False


def prepare_forces(
    game: AgeOfHeroesGame,
    player: AgeOfHeroesPlayer,
    armies: int,
    generals: int,
    heroes: int = 0,
    hero_generals: int = 0,
) -> bool:
    """Prepare forces for battle."""
    if not player.tribe_state:
        return False

    active_players = game.get_active_players()
    player_index = active_players.index(player)
    war = game.war_state

    # Validate army/general counts
    available_armies = player.tribe_state.get_available_armies()
    available_generals = player.tribe_state.get_available_generals()

    # Count hero cards available
    hero_cards = sum(
        1
        for card in player.hand
        if card.card_type == CardType.EVENT and card.subtype == EventType.HERO
    )

    total_heroes_used = heroes + hero_generals
    if total_heroes_used > hero_cards:
        return False

    if armies > available_armies:
        return False
    if generals > available_generals:
        return False

    # Commit forces
    if player_index == war.attacker_index:
        war.attacker_armies = armies
        war.attacker_generals = generals
        war.attacker_heroes = heroes
        war.attacker_hero_generals = hero_generals
        war.attacker_prepared = True
    elif player_index == war.defender_index:
        war.defender_armies = armies
        war.defender_generals = generals
        war.defender_heroes = heroes
        war.defender_hero_generals = hero_generals
        war.defender_prepared = True
    else:
        return False

    # Remove hero cards from hand
    for _ in range(total_heroes_used):
        for i, card in enumerate(player.hand):
            if card.card_type == CardType.EVENT and card.subtype == EventType.HERO:
                removed = player.hand.pop(i)
                game.discard_pile.append(removed)
                break

    # Announce preparation
    user = game.get_user(player)
    if user:
        user.speak_l(
            "ageofheroes-war-prepared",
            armies=armies + heroes,
            generals=generals + hero_generals,
            heroes=0,  # Heroes already counted in armies/generals
            buffer="game",
        )

    return True


def player_roll_war_dice(game: AgeOfHeroesGame, player: AgeOfHeroesPlayer) -> int:
    """Player clicks to roll dice for war. Returns the roll value (1d6)."""
    war = game.war_state
    active_players = game.get_active_players()
    player_index = active_players.index(player)

    # Roll one die (war uses 1d6, not 2d6 like setup)
    die_roll = random.randint(1, 6)  # nosec B311

    # Store roll for this player
    if player_index == war.attacker_index:
        war.attacker_roll = die_roll
        war.attacker_dice = [die_roll]
    elif player_index == war.defender_index:
        war.defender_roll = die_roll
        war.defender_dice = [die_roll]

    # Play dice sound
    game.play_sound("game_pig/dice.ogg")

    # Announce roll
    user = game.get_user(player)
    if user:
        user.speak_l("ageofheroes-war-roll-you", roll=die_roll, buffer="game")

    # Announce to others
    for p in game.players:
        if p != player:
            other_user = game.get_user(p)
            if other_user:
                other_user.speak_l(
                    "ageofheroes-war-roll-other",
                    player=player.name,
                    roll=die_roll,
                    buffer="game",
                )

    return die_roll


def resolve_battle_round(game: AgeOfHeroesGame) -> tuple[str, int, int]:
    """Resolve one round of battle using already-rolled dice. Returns (winner, attacker_losses, defender_losses).

    Winner is 'attacker', 'defender', or 'draw'.
    NOTE: In Pascal, draws cause NO losses (unlike Risk-style games).
    """
    war = game.war_state
    active_players = game.get_active_players()

    (
        attacker_total,
        defender_total,
        att_gen_bonus,
        att_fort_bonus,
        def_gen_bonus,
        def_fort_bonus,
        attacker,
        defender,
    ) = _calculate_war_totals(war, active_players)

    _announce_war_bonuses(
        game,
        attacker,
        defender,
        att_gen_bonus,
        att_fort_bonus,
        def_gen_bonus,
        def_fort_bonus,
        attacker_total,
        defender_total,
    )

    winner, attacker_losses, defender_losses = _resolve_war_outcome(
        game, attacker, defender, attacker_total, defender_total
    )

    # Apply losses (only if not a draw)
    apply_battle_losses(game, attacker_losses, defender_losses)

    return winner, attacker_losses, defender_losses


def _calculate_war_totals(
    war: WarState, active_players: list[AgeOfHeroesPlayer]
) -> tuple[
    int,
    int,
    int,
    int,
    int,
    int,
    AgeOfHeroesPlayer | None,
    AgeOfHeroesPlayer | None,
]:
    """Compute dice totals, bonuses, and participant references for war."""
    # Use stored rolls from player clicks
    att_dice_total = war.attacker_roll
    def_dice_total = war.defender_roll

    # Calculate bonuses separately
    att_gen_bonus = 2 if war.get_attacker_total_generals() > 0 else 0
    def_gen_bonus = 2 if war.get_defender_total_generals() > 0 else 0

    def_fort_bonus = 0
    defender_index = war.defender_index
    if defender_index < len(active_players):
        defender_player = active_players[defender_index]
        if hasattr(defender_player, "tribe_state") and defender_player.tribe_state:
            def_fort_bonus = defender_player.tribe_state.fortresses

    att_fort_bonus = 0
    att_total_bonus = att_gen_bonus + att_fort_bonus
    def_total_bonus = def_gen_bonus + def_fort_bonus

    attacker_total = att_dice_total + att_total_bonus
    defender_total = def_dice_total + def_total_bonus

    attacker = (
        active_players[war.attacker_index] if war.attacker_index < len(active_players) else None
    )
    defender = (
        active_players[war.defender_index] if war.defender_index < len(active_players) else None
    )

    return (
        attacker_total,
        defender_total,
        att_gen_bonus,
        att_fort_bonus,
        def_gen_bonus,
        def_fort_bonus,
        attacker,
        defender,
    )


def _announce_war_bonuses(
    game: AgeOfHeroesGame,
    attacker: AgeOfHeroesPlayer | None,
    defender: AgeOfHeroesPlayer | None,
    att_gen_bonus: int,
    att_fort_bonus: int,
    def_gen_bonus: int,
    def_fort_bonus: int,
    attacker_total: int,
    defender_total: int,
) -> None:
    """Announce bonuses for attacker and defender when present."""
    if attacker and (att_gen_bonus + att_fort_bonus) > 0:
        _announce_war_bonus_for_side(
            game,
            attacker,
            att_gen_bonus,
            att_fort_bonus,
            attacker_total,
        )

    if defender and (def_gen_bonus + def_fort_bonus) > 0:
        _announce_war_bonus_for_side(
            game,
            defender,
            def_gen_bonus,
            def_fort_bonus,
            defender_total,
        )


def _announce_war_bonus_for_side(
    game: AgeOfHeroesGame,
    participant: AgeOfHeroesPlayer,
    gen_bonus: int,
    fort_bonus: int,
    total: int,
) -> None:
    for p in game.players:
        user = game.get_user(p)
        if not user:
            continue
        if _brief_enabled(game, user):
            key = (
                "ageofheroes-war-bonuses-you-brief"
                if p == participant
                else "ageofheroes-war-bonuses-other-brief"
            )
            kwargs = {"bonus": gen_bonus + fort_bonus, "total": total}
            if p != participant:
                kwargs["player"] = participant.name
            user.speak_l(key, buffer="game", **kwargs)
            continue
        if p == participant:
            user.speak_l(
                "ageofheroes-war-bonuses-you",
                general=gen_bonus,
                fortress=fort_bonus,
                total=total,
                buffer="game",
            )
        else:
            user.speak_l(
                "ageofheroes-war-bonuses-other",
                player=participant.name,
                general=gen_bonus,
                fortress=fort_bonus,
                total=total,
                buffer="game",
            )


def _resolve_war_outcome(
    game: AgeOfHeroesGame,
    attacker: AgeOfHeroesPlayer | None,
    defender: AgeOfHeroesPlayer | None,
    attacker_total: int,
    defender_total: int,
) -> tuple[str, int, int]:
    """Determine winner, announce outcome, and return losses."""
    if attacker_total > defender_total:
        game.play_sound("game_ageofheroes/attack_win.ogg")
        _broadcast_l_with_brief(
            game,
            "ageofheroes-round-attacker-wins",
            "ageofheroes-round-attacker-wins-brief",
            attacker=attacker.name if attacker else "Attacker",
            defender=defender.name if defender else "Defender",
            att_total=attacker_total,
            def_total=defender_total,
        )
        return "attacker", 0, 1

    if defender_total > attacker_total:
        game.play_sound("game_ageofheroes/defend_win.ogg")
        _broadcast_l_with_brief(
            game,
            "ageofheroes-round-defender-wins",
            "ageofheroes-round-defender-wins-brief",
            attacker=attacker.name if attacker else "Attacker",
            defender=defender.name if defender else "Defender",
            att_total=attacker_total,
            def_total=defender_total,
        )
        return "defender", 1, 0

    _broadcast_l_with_brief(
        game,
        "ageofheroes-round-draw",
        "ageofheroes-round-draw-brief",
        attacker=attacker.name if attacker else "Attacker",
        defender=defender.name if defender else "Defender",
        total=attacker_total,
    )
    return "draw", 0, 0


def apply_battle_losses(game: AgeOfHeroesGame, attacker_losses: int, defender_losses: int) -> None:
    """Apply army losses from battle."""
    war = game.war_state
    active_players = game.get_active_players()

    # Apply attacker losses
    if attacker_losses > 0 and war.attacker_index < len(active_players):
        attacker = active_players[war.attacker_index]
        if hasattr(attacker, "tribe_state") and attacker.tribe_state:
            # First lose heroes being used as armies
            heroes_lost = min(attacker_losses, war.attacker_heroes)
            war.attacker_heroes -= heroes_lost
            attacker_losses -= heroes_lost

            # Then lose regular armies
            if attacker_losses > 0:
                armies_lost = min(attacker_losses, war.attacker_armies)
                war.attacker_armies -= armies_lost
                attacker.tribe_state.armies -= armies_lost
                game.army_supply += armies_lost

    # Apply defender losses
    if defender_losses > 0 and war.defender_index < len(active_players):
        defender = active_players[war.defender_index]
        if hasattr(defender, "tribe_state") and defender.tribe_state:
            # First lose heroes being used as armies
            heroes_lost = min(defender_losses, war.defender_heroes)
            war.defender_heroes -= heroes_lost
            defender_losses -= heroes_lost

            # Then lose regular armies
            if defender_losses > 0:
                armies_lost = min(defender_losses, war.defender_armies)
                war.defender_armies -= armies_lost
                defender.tribe_state.armies -= armies_lost
                game.army_supply += armies_lost


def is_battle_over(game: AgeOfHeroesGame) -> bool:
    """Check if the battle is over (one side has no armies left)."""
    war = game.war_state

    attacker_armies = war.get_attacker_total_armies()
    defender_armies = war.get_defender_total_armies()

    return attacker_armies <= 0 or defender_armies <= 0


def get_battle_winner(game: AgeOfHeroesGame) -> str | None:
    """Get the winner of the battle, or None if not over."""
    if not is_battle_over(game):
        return None

    war = game.war_state
    attacker_armies = war.get_attacker_total_armies()
    defender_armies = war.get_defender_total_armies()

    if attacker_armies > 0 and defender_armies <= 0:
        return "attacker"
    elif defender_armies > 0 and attacker_armies <= 0:
        return "defender"
    else:
        # Both wiped out - defender wins by default
        return "defender"


def apply_war_outcome(game: AgeOfHeroesGame) -> None:
    """Apply the outcome of the war based on the goal."""
    war = game.war_state
    winner = get_battle_winner(game)
    active_players = game.get_active_players()

    if winner != "attacker":
        # Attacker lost or draw - no spoils
        return_surviving_forces(game)
        return

    # Attacker won - apply goal
    if war.attacker_index >= len(active_players):
        return
    if war.defender_index >= len(active_players):
        return

    attacker = active_players[war.attacker_index]
    defender = active_players[war.defender_index]

    if not hasattr(attacker, "tribe_state") or not attacker.tribe_state:
        return
    if not hasattr(defender, "tribe_state") or not defender.tribe_state:
        return

    # Get attacker's remaining army strength for calculating spoils
    attacker_strength = war.attacker_armies + war.attacker_heroes

    if war.goal == WarGoal.CONQUEST:
        # Take cities based on army strength (Pascal: wgsConquest)
        # 3+ armies: 2 cities, 1+ armies: 1 city
        if attacker_strength >= 3:
            cities_to_take = 2
        elif attacker_strength >= 1:
            cities_to_take = 1
        else:
            cities_to_take = 0

        cities_to_take = min(cities_to_take, defender.tribe_state.cities)

        if cities_to_take > 0:
            defender.tribe_state.cities -= cities_to_take
            attacker.tribe_state.cities += cities_to_take
            _broadcast_l_with_brief(
                game,
                "ageofheroes-conquest-success",
                "ageofheroes-conquest-success-brief",
                attacker=attacker.name,
                defender=defender.name,
                count=cities_to_take,
            )
            game.play_sound("game_ageofheroes/conquest.ogg")

    elif war.goal == WarGoal.PLUNDER:
        # Steal cards: 2x army strength (Pascal: wgsPlunder)
        cards_to_steal = min(2 * attacker_strength, len(defender.hand))
        if cards_to_steal > 0:
            stolen = []
            for _ in range(cards_to_steal):
                if defender.hand:
                    # Steal random card
                    idx = random.randint(0, len(defender.hand) - 1)  # nosec B311
                    card = defender.hand.pop(idx)
                    attacker.hand.append(card)
                    stolen.append(card)

            _broadcast_l_with_brief(
                game,
                "ageofheroes-plunder-success",
                "ageofheroes-plunder-success-brief",
                attacker=attacker.name,
                count=len(stolen),
                defender=defender.name,
            )
            game.play_sound("game_ageofheroes/plunder.ogg")

    elif war.goal == WarGoal.DESTRUCTION:
        # Destroy monument progress based on army strength (Pascal: wgsDestruction)
        # 3+ armies: 2 resources, 1-2 armies: 1 resource, 0 armies: 0 resources
        if attacker_strength >= 3:
            resources_to_destroy = 2
        elif attacker_strength >= 1:
            resources_to_destroy = 1
        else:
            resources_to_destroy = 0

        resources_to_destroy = min(resources_to_destroy, defender.tribe_state.monument_progress)

        if resources_to_destroy > 0:
            defender.tribe_state.monument_progress -= resources_to_destroy
            _broadcast_l_with_brief(
                game,
                "ageofheroes-destruction-success",
                "ageofheroes-destruction-success-brief",
                attacker=attacker.name,
                defender=defender.name,
                count=resources_to_destroy,
            )
            game.play_sound("game_ageofheroes/destruction.ogg")

    return_surviving_forces(game)


def has_road_connection(game: AgeOfHeroesGame, player1_index: int, player2_index: int) -> bool:
    """Check if two players have a road connection between them."""
    active_players = game.get_active_players()

    if player1_index >= len(active_players) or player2_index >= len(active_players):
        return False

    player1 = active_players[player1_index]
    player2 = active_players[player2_index]

    if not hasattr(player1, "tribe_state") or not player1.tribe_state:
        return False
    if not hasattr(player2, "tribe_state") or not player2.tribe_state:
        return False

    # Check if they are neighbors and have connecting roads
    # Players are neighbors if their indices differ by 1 (mod num_players)
    num_players = len(active_players)

    # Check if player2 is to the right of player1
    if (player1_index + 1) % num_players == player2_index:
        return player1.tribe_state.road_right and player2.tribe_state.road_left

    # Check if player2 is to the left of player1
    if (player1_index - 1) % num_players == player2_index:
        return player1.tribe_state.road_left and player2.tribe_state.road_right

    return False


def return_surviving_forces(game: AgeOfHeroesGame) -> None:
    """Return surviving armies after battle."""
    war = game.war_state
    active_players = game.get_active_players()

    # Attacker's surviving armies return
    if war.attacker_index < len(active_players):
        attacker = active_players[war.attacker_index]
        if hasattr(attacker, "tribe_state") and attacker.tribe_state:
            surviving_armies = war.attacker_armies
            surviving_generals = war.attacker_generals

            if surviving_armies > 0 or surviving_generals > 0:
                # Check if attacker has road to defender for immediate return
                has_road = has_road_connection(game, war.attacker_index, war.defender_index)

                if has_road:
                    user = game.get_user(attacker)
                    if user:
                        user.speak_l("ageofheroes-army-return-road", buffer="game")
                    game.play_sound("game_ageofheroes/backarmy.ogg")
                else:
                    # Delayed return - armies come back next turn
                    attacker.tribe_state.returning_armies = surviving_armies
                    attacker.tribe_state.returning_generals = surviving_generals

                    user = game.get_user(attacker)
                    if user:
                        user.speak_l(
                            "ageofheroes-army-return-delayed",
                            count=surviving_armies + surviving_generals,
                            buffer="game",
                        )

    # Reset war state
    war.reset()


def check_fortune_reroll(game: AgeOfHeroesGame, player: AgeOfHeroesPlayer) -> bool:
    """Check if player has Fortune card for reroll."""
    for card in player.hand:
        if card.card_type == CardType.EVENT and card.subtype == EventType.FORTUNE:
            return True
    return False


def use_fortune_reroll(game: AgeOfHeroesGame, player: AgeOfHeroesPlayer) -> bool:
    """Use Fortune card to reroll dice."""
    for i, card in enumerate(player.hand):
        if card.card_type == CardType.EVENT and card.subtype == EventType.FORTUNE:
            removed = player.hand.pop(i)
            game.discard_pile.append(removed)
            game.broadcast_personal_l(
                player,
                "ageofheroes-you-use-fortune",
                "ageofheroes-player-uses-fortune",
                buffer="game",
            )
            game.play_sound("game_ageofheroes/fortune.ogg")
            return True
    return False


def jolt_war_bots(game: AgeOfHeroesGame) -> None:
    """Jolt bot players to roll dice in war."""
    active_players = game.get_active_players()
    war = game.war_state

    if war.attacker_index < len(active_players):
        attacker = active_players[war.attacker_index]
        if attacker.is_bot and war.attacker_roll == 0:
            # Clear any pending action and set to roll immediately next tick
            attacker.bot_pending_action = None
            attacker.bot_think_ticks = 1  # Will call bot_think on next tick

    if war.defender_index < len(active_players):
        defender = active_players[war.defender_index]
        if defender.is_bot and war.defender_roll == 0:
            # Clear any pending action and set to roll immediately next tick
            defender.bot_pending_action = None
            defender.bot_think_ticks = 1  # Will call bot_think on next tick


def resolve_war_round(game: AgeOfHeroesGame) -> None:
    """Resolve one round of war battle after both players have rolled."""
    # Resolve the round
    resolve_battle_round(game)

    # Check if battle is over
    if is_battle_over(game):
        # Battle is finished
        finish_war_battle(game)
    else:
        # Continue to next round - reset rolls
        game.war_state.reset_round_rolls()
        game.refresh_menus()

        # Jolt both bots to roll for next round
        active_players = game.get_active_players()
        war = game.war_state
        if war.attacker_index < len(active_players):
            attacker = active_players[war.attacker_index]
            if attacker.is_bot:
                attacker.bot_think_ticks = 0
                attacker.bot_pending_action = None
        if war.defender_index < len(active_players):
            defender = active_players[war.defender_index]
            if defender.is_bot:
                defender.bot_think_ticks = 0
                defender.bot_pending_action = None


def execute_war_battle(game: AgeOfHeroesGame) -> None:
    """Start the interactive war battle after both sides have prepared forces.

    Players will now click to roll dice each round instead of automatic resolution.
    """
    from .state import PlaySubPhase

    # Announce battle start with army counts
    active_players = game.get_active_players()
    war = game.war_state

    if war.attacker_index < len(active_players) and war.defender_index < len(active_players):
        attacker = active_players[war.attacker_index]
        defender = active_players[war.defender_index]

        att_armies = war.get_attacker_total_armies()
        def_armies = war.get_defender_total_armies()

        # Announce battle start
        _broadcast_l_with_brief(
            game,
            "ageofheroes-battle-start",
            "ageofheroes-battle-start-brief",
            attacker=attacker.name,
            defender=defender.name,
            att_armies=att_armies,
            def_armies=def_armies,
        )

    # Check if battle is already over (one side has 0 armies)
    if is_battle_over(game):
        # Battle is already over without needing to roll
        finish_war_battle(game)
        return

    # Enter interactive battle mode
    game.sub_phase = PlaySubPhase.WAR_BATTLE
    war.battle_in_progress = True
    war.reset_round_rolls()

    # Focus human combatants on the new roll prompt; jolt bots to act immediately.
    active_players = game.get_active_players()
    if war.attacker_index < len(active_players):
        attacker = active_players[war.attacker_index]
        if attacker.is_bot:
            attacker.bot_think_ticks = 0
            attacker.bot_pending_action = None
        else:
            game.request_menu_focus(attacker, "war_roll_dice")
    if war.defender_index < len(active_players):
        defender = active_players[war.defender_index]
        if defender.is_bot:
            defender.bot_think_ticks = 0
            defender.bot_pending_action = None
        else:
            game.request_menu_focus(defender, "war_roll_dice")

    # Rebuild menus to show "Roll dice" button.
    game.refresh_menus()


def finish_war_battle(game: AgeOfHeroesGame) -> None:
    """Finish the war battle and apply outcome."""
    active_players = game.get_active_players()
    war = game.war_state

    # Save attacker/defender info BEFORE applying outcome (which resets war state)
    winner = get_battle_winner(game)
    had_rounds = war.battle_in_progress

    attacker = None
    defender = None
    if (
        0 <= war.attacker_index < len(active_players)
        and 0 <= war.defender_index < len(active_players)
    ):
        attacker = active_players[war.attacker_index]
        defender = active_players[war.defender_index]

    # Apply war outcome (this may reset war state)
    apply_war_outcome(game)

    # Announce battle end summary only when no rounds were fought
    # (immediate end due to 0 armies). When rounds were fought, the
    # per-round messages already announce the outcome.
    if not had_rounds and attacker is not None and defender is not None:
        _announce_immediate_battle_result(game, attacker, defender, winner)

    # Check for elimination of both players
    if attacker is not None:
        game._check_elimination(attacker)

    if defender is not None:
        game._check_elimination(defender)

    # Reset war state and end action
    war.reset()

    if attacker is not None:
        game._end_action(attacker)


def _announce_immediate_battle_result(
    game: AgeOfHeroesGame,
    attacker: AgeOfHeroesPlayer,
    defender: AgeOfHeroesPlayer,
    winner: str | None,
) -> None:
    """Announce an immediate battle result to both combatants and observers."""
    for listener in game.players:
        user = game.get_user(listener)
        if not user:
            continue
        if winner == "attacker":
            if listener.id == attacker.id:
                user.speak_l(
                    "ageofheroes-you-win-battle-as-attacker",
                    buffer="game",
                    defender=defender.name,
                )
            elif listener.id == defender.id:
                user.speak_l(
                    "ageofheroes-you-lose-battle-as-defender",
                    buffer="game",
                    attacker=attacker.name,
                )
            else:
                user.speak_l(
                    "ageofheroes-battle-victory-attacker",
                    buffer="game",
                    attacker=attacker.name,
                    defender=defender.name,
                )
            continue
        if winner == "defender":
            if listener.id == attacker.id:
                user.speak_l(
                    "ageofheroes-you-lose-battle-as-attacker",
                    buffer="game",
                    defender=defender.name,
                )
            elif listener.id == defender.id:
                user.speak_l(
                    "ageofheroes-you-win-battle-as-defender",
                    buffer="game",
                    attacker=attacker.name,
                )
            else:
                user.speak_l(
                    "ageofheroes-battle-victory-defender",
                    buffer="game",
                    attacker=attacker.name,
                    defender=defender.name,
                )
            continue
        if listener.id == attacker.id:
            opponent = defender.name
        elif listener.id == defender.id:
            opponent = attacker.name
        else:
            user.speak_l(
                "ageofheroes-battle-mutual-defeat",
                buffer="game",
                attacker=attacker.name,
                defender=defender.name,
            )
            continue
        user.speak_l(
            "ageofheroes-you-draw-battle",
            buffer="game",
            opponent=opponent,
        )
