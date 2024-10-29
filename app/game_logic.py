import random

# Card values dictionary
card_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

# Returns a shuffled deck
def create_deck():
    deck = [rank for rank in card_values.keys()] * 4
    random.shuffle(deck)
    return deck

def deal_card(deck):
    return deck.pop()

def calculate_hand_value(hand):
    value = sum(card_values[card] for card in hand)
    # Adjust for aces (count them as 1 instead of 11 if needed)
    aces = hand.count('A')
    while value > 21 and aces:
        value -= 10  # Count ace as 1 instead of 11
        aces -= 1
    return value

def is_bust(hand):
    return calculate_hand_value(hand) > 21

def is_blackjack(hand):
    """Return True if hand is a blackjack (an ace and a 10-value card)."""
    return calculate_hand_value(hand) == 21 and len(hand) == 2

def start_game(user, bet_amount):
    # Check if user has enough bankroll
    if user.bankroll < bet_amount:
        raise ValueError("Insufficient bankroll for this bet.")

    # Deduct bet from user’s bankroll and create a new game session
    user.bankroll -= bet_amount
    game_session = GameSession(user_id=user.id, bet=bet_amount, final_bankroll=user.bankroll)

    # Initialize deck and hands
    deck = create_deck()
    player_hand = [deal_card(deck), deal_card(deck)]
    dealer_hand = [deal_card(deck), deal_card(deck)]

    return deck, player_hand, dealer_hand, game_session

def play_turn(player_hand, deck):
    player_hand.append(deal_card(deck))
    return player_hand

def determine_outcome(player_hand, dealer_hand, user, game_session):
    """Determine the outcome of the game and update bankroll accordingly."""
    player_value = calculate_hand_value(player_hand)
    dealer_value = calculate_hand_value(dealer_hand)
    
    if player_value > 21:
        outcome = "lose"
    elif dealer_value > 21 or player_value > dealer_value:
        outcome = "win"
        user.bankroll += game_session.bet * 2
    elif player_value < dealer_value:
        outcome = "lose"
    else:
        outcome = "tie"
        user.bankroll += game_session.bet

    # Record outcome in game session and save final bankroll
    game_session.record_outcome(outcome, user)
    return outcome
