from flask import Blueprint, request, jsonify
from . import db
from .models import User, GameSession
from .game_logic import create_deck, deal_card, calculate_hand_value, is_bust, is_blackjack, start_game, play_turn, determine_outcome
from flask_login import current_user, login_required

main = Blueprint('main', __name__)

@main.route('/place-bet', methods=['POST'])
@login_required
def place_bet():
    """Allow the player to place a bet for the game."""
    data = request.get_json()
    bet_amount = data.get('bet')

    # Validate bet amount
    if not isinstance(bet_amount, int) or bet_amount < 10 or bet_amount > 100:
        return jsonify({'error': 'Invalid bet amount. Bet must be between 10 and 100.'}), 400

    # Check if the player has enough bankroll
    if current_user.bankroll < bet_amount:
        return jsonify({'error': 'Insufficient bankroll for this bet.'}), 400

    # Deduct bet from user's bankroll and create a new game session
    current_user.bankroll -= bet_amount
    game_session = GameSession(user_id=current_user.id, bet=bet_amount, final_bankroll=current_user.bankroll)
    db.session.add(game_session)
    db.session.commit()

    return jsonify({
        'message': f'Bet of ${bet_amount} placed.',
        'remaining_bankroll': current_user.bankroll
    })

@main.route('/start-game', methods=['POST'])
@login_required
def start_game_route():
    """Start a new game, shuffle deck, deal initial hands."""
    try:
        deck, player_hand, dealer_hand, game_session = start_game(current_user, current_user.bankroll)
        db.session.add(game_session)
        db.session.commit()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # Store deck and hands in game session (can use a database if needed for multiplayer)
    game_session.deck = deck
    game_session.player_hand = player_hand
    game_session.dealer_hand = dealer_hand
    db.session.commit()

    return jsonify({
        'message': 'Game started!',
        'player_hand': player_hand,
        'dealer_upcard': dealer_hand[0]
    })

@main.route('/hit', methods=['POST'])
@login_required
def hit():
    """Allow the player to take a hit and receive another card."""
    game_session = GameSession.query.filter_by(user_id=current_user.id).order_by(GameSession.timestamp.desc()).first()
    if not game_session:
        return jsonify({'error': 'No active game session found. Please start a new game.'}), 400

    # Continue game with hit logic
    deck = game_session.deck
    player_hand = game_session.player_hand
    player_hand = play_turn(player_hand, deck)
    game_session.player_hand = player_hand
    db.session.commit()

    # Check for bust
    if is_bust(player_hand):
        outcome = "bust"
        game_session.record_outcome(outcome, current_user)
        db.session.commit()
        return jsonify({
            'player_hand': player_hand,
            'player_value': calculate_hand_value(player_hand),
            'outcome': outcome,
            'remaining_bankroll': current_user.bankroll
        })

    # If not bust, return updated hand
    return jsonify({
        'player_hand': player_hand,
        'player_value': calculate_hand_value(player_hand)
    })

@main.route('/stand', methods=['POST'])
@login_required
def stand():
    """Player chooses to stand; let dealer play and determine outcome."""
    game_session = GameSession.query.filter_by(user_id=current_user.id).order_by(GameSession.timestamp.desc()).first()
    if not game_session:
        return jsonify({'error': 'No active game session found. Please start a new game.'}), 400

    # Dealer's turn - dealer hits until reaching 17 or more
    dealer_hand = game_session.dealer_hand
    deck = game_session.deck
    while calculate_hand_value(dealer_hand) < 17:
        dealer_hand.append(deal_card(deck))

    # Determine outcome
    outcome = determine_outcome(game_session.player_hand, dealer_hand, current_user, game_session)

    # Update database with final outcome
    game_session.dealer_hand = dealer_hand
    game_session.outcome = outcome
    db.session.commit()

    return jsonify({
        'player_hand': game_session.player_hand,
        'player_value': calculate_hand_value(game_session.player_hand),
        'dealer_hand': dealer_hand,
        'dealer_value': calculate_hand_value(dealer_hand),
        'outcome': outcome,
        'remaining_bankroll': current_user.bankroll
    })
