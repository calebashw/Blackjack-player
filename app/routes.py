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
    data = request.get_json()
    hand_type = data.get('hand', 'original')  # Default to original hand if not specified

    game_session = GameSession.query.filter_by(user_id=current_user.id).order_by(GameSession.timestamp.desc()).first()
    if not game_session:
        return jsonify({'error': 'No active game session found. Please start a new game.'}), 400

    # Select the hand to hit
    hand = game_session.player_hand if hand_type == 'original' else game_session.split_hand
    hand.append(deal_card(game_session.deck))
    if hand_type == 'original':
        game_session.player_hand = hand
    else:
        game_session.split_hand = hand
    db.session.commit()

    if is_bust(hand):
        return jsonify({
            'hand_type': hand_type,
            'hand': hand,
            'outcome': 'bust',
            'remaining_bankroll': current_user.bankroll
        })

    return jsonify({
        'hand_type': hand_type,
        'hand': hand,
        'value': calculate_hand_value(hand)
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

@main.route('/double-down', methods=['POST'])
@login_required
def double_down():
    """Double the player's bet and give one card, ending their turn."""
    game_session = GameSession.query.filter_by(user_id=current_user.id).order_by(GameSession.timestamp.desc()).first()
    if not game_session or game_session.doubled_down:
        return jsonify({'error': 'Invalid operation or already doubled down.'}), 400

    # Double the bet amount and deduct from bankroll
    game_session.bet *= 2
    current_user.bankroll -= game_session.bet // 2  # Only deduct the additional bet
    game_session.doubled_down = True

    # Deal one final card to the player
    deck = game_session.deck
    player_hand = game_session.player_hand
    player_hand.append(deal_card(deck))
    game_session.player_hand = player_hand
    db.session.commit()

    # Check if the player busts after doubling down
    if is_bust(player_hand):
        outcome = "bust"
    else:
        # If not bust, handle dealer's turn immediately
        dealer_hand = game_session.dealer_hand
        while calculate_hand_value(dealer_hand) < 17:
            dealer_hand.append(deal_card(deck))
        outcome = determine_outcome(player_hand, dealer_hand, current_user, game_session)
        game_session.dealer_hand = dealer_hand
        game_session.outcome = outcome

    db.session.commit()

    return jsonify({
        'player_hand': player_hand,
        'player_value': calculate_hand_value(player_hand),
        'dealer_hand': game_session.dealer_hand,
        'dealer_value': calculate_hand_value(game_session.dealer_hand),
        'outcome': outcome,
        'remaining_bankroll': current_user.bankroll
    })


@main.route('/split', methods=['POST'])
@login_required
def split():
    """Split the player's hand into two separate hands if possible."""
    game_session = GameSession.query.filter_by(user_id=current_user.id).order_by(GameSession.timestamp.desc()).first()
    if not game_session or game_session.split_hand:
        return jsonify({'error': 'Invalid operation or hand already split.'}), 400

    player_hand = game_session.player_hand
    if len(player_hand) != 2 or player_hand[0] != player_hand[1]:
        return jsonify({'error': 'Cannot split. Cards must be identical.'}), 400

    # Split the hand into two and deduct an additional bet
    game_session.split_hand = [player_hand.pop()]  # The second hand starts with one of the pair
    current_user.bankroll -= game_session.bet
    db.session.commit()

    return jsonify({
        'original_hand': player_hand,
        'split_hand': game_session.split_hand,
        'remaining_bankroll': current_user.bankroll
    })
