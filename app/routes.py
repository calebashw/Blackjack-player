from flask import Blueprint, request, jsonify, session
from .game_logic import create_deck, deal_card, calculate_hand_value, is_bust, is_blackjack, start_game, play_turn, determine_outcome

# Define the main blueprint
main = Blueprint('main', __name__)

# Needs full database for actual use
session_data = {}

# Define a simple route for testing
@main.route('/start-game', methods=['POST'])
def start_game_route():
    deck, player_hand, dealer_hand = start_game()

    # Tracking the sesssion data so far
    session_data['deck'] = deck
    session_data['player_hand'] = player_hand
    session_data['dealer_hand'] = dealer_hand

    return jsonify({
        'message': 'Game started!',
        'player_hand': player_hand,
        'dealer_upcard': dealer_hand[0]  # Only reveal dealer's upcard
    })


# Hitting route
@main.route('/hit', methods=['POST'])
def hit():
    deck = session_data.get('deck')
    player_hand = session_data.get('player_hand')

    # Check to make sure, send error if bad
    if not deck or not player_hand:
        return jsonify({'error': 'Game not started. Please start a new game.'}), 400

    # Deal card to player
    player_hand = play_turn(player_hand, deck)
    session_data['player_hand'] = player_hand

    if is_bust(player_hand):
        return jsonify({
            'player_hand': player_hand,
            'player_value': calculate_hand_value(player_hand),
            'outcome': 'bust'
        })
    # If not bust, return updated hand
    return jsonify({
        'player_hand': player_hand,
        'player_value': calculate_hand_value(player_hand)
    })

@main.route('/stand', methods=['POST'])
def stand():
    """Player chooses to stand; let dealer play and determine outcome."""
    deck = session_data.get('deck')
    player_hand = session_data.get('player_hand')
    dealer_hand = session_data.get('dealer_hand')
    bet = session_data.get('bet', 0)  # Retrieve the current bet

    if not deck or not player_hand or not dealer_hand:
        return jsonify({'error': 'Game not started. Please start a new game.'}), 400

    # Dealer's turn - dealer hits until reaching 17 or more
    while calculate_hand_value(dealer_hand) < 17:
        dealer_hand.append(deal_card(deck))

    session_data['dealer_hand'] = dealer_hand  # Update session data

    # Determine outcome
    outcome = determine_outcome(player_hand, dealer_hand)

    # Update bankroll based on outcome
    if outcome == "win":
        session_data['bankroll'] += bet * 2  # Player gets back twice the bet
    elif outcome == "tie":
        session_data['bankroll'] += bet  # Player gets the bet back

    return jsonify({
        'player_hand': player_hand,
        'player_value': calculate_hand_value(player_hand),
        'dealer_hand': dealer_hand,
        'dealer_value': calculate_hand_value(dealer_hand),
        'outcome': outcome,
        'remaining_bankroll': session_data['bankroll']
    })

@main.route('/place-bet', methods=['POST'])
def place_bet():
    data = request.get_json()
    bet_amount = data.get('bet')

    # Add a bankroll default 1000
    if 'bankroll' not in session_data:
        session_data['bankroll'] = 1000

    if not isinstance(bet_amount, int) or bet_amount < 10 or bet_amount > 100:
        return jsonify({'error': 'Invalid bet amount. Bet must be between 10 and 100.'}), 400

    if session_data['bankroll'] < bet_amount:
        return jsonify({'error': 'Insufficient bankroll for this bet.'}), 400

    session_data['bankroll'] -= bet_amount
    session_data['bet'] = bet_amount

    return jsonify({
        'message': f'Bet of ${bet_amount} placed.',
        'remaining_bankroll': session_data['bankroll']
    })