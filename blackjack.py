import random

# Define card values
card_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

def create_deck():
    """Create a standard 52-card deck."""
    return [rank for rank in card_values.keys()] * 4

def deal_card(deck):
    """Deal a card from the deck."""
    return deck.pop(random.randint(0, len(deck) - 1))

def calculate_hand_value(hand):
    """Calculate the total value of a hand."""
    value = sum(card_values[card] for card in hand)
    # Adjust for aces
    aces = hand.count('A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

def basic_strategy(player_hand, dealer_upcard):
    """Provide basic strategy advice based on the player's hand and dealer's upcard."""
    player_value = calculate_hand_value(player_hand)
    dealer_value = card_values[dealer_upcard]

    if player_value >= 17:
        return "Stand"
    elif 13 <= player_value <= 16 and dealer_value < 7:
        return "Stand"
    elif 12 <= player_value <= 16 and dealer_value >= 7:
        return "Hit"
    elif player_value == 11:
        return "Double down (if possible), otherwise Hit"
    elif player_value == 10 and dealer_value < 10:
        return "Double down (if possible), otherwise Hit"
    elif player_value == 9 and 3 <= dealer_value <= 6:
        return "Double down (if possible), otherwise Hit"
    elif player_value <= 8:
        return "Hit"
    else:
        return "Stand"

def play_blackjack():
    bankroll = 1000  # Starting bankroll
    print("Welcome to Blackjack! You start with $1000.")
    
    while bankroll > 0:
        # Show current bankroll
        print(f"\nYour current bankroll: ${bankroll}")
        
        # Get the player's bet
        while True:
            try:
                bet = int(input("Place your bet ($10, $20, $50, $100): "))
                if bet in [10, 20, 50, 100] and bet <= bankroll:
                    break
                else:
                    print("Invalid bet. Make sure it's one of the allowed amounts and within your bankroll.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Create and shuffle the deck
        deck = create_deck()
        random.shuffle(deck)

        # Deal initial hands
        player_hand = [deal_card(deck), deal_card(deck)]
        dealer_hand = [deal_card(deck), deal_card(deck)]

        print(f"Your hand: {player_hand} (Value: {calculate_hand_value(player_hand)})")
        print(f"Dealer's upcard: {dealer_hand[0]}")

        # Play the player's hand
        outcome = play_single_hand(player_hand, dealer_hand, deck, bet)

        # Update bankroll based on outcome
        if outcome[0] == "win":
            bankroll += outcome[1]
            print(f"You won ${outcome[1]}! Your new bankroll is ${bankroll}.")
        elif outcome[0] == "lose":
            bankroll -= outcome[1]
            print(f"You lost ${outcome[1]}. Your new bankroll is ${bankroll}.")
        elif outcome[0] == "tie":
            print("It's a tie. Your bankroll remains the same.")

        # Ask if the player wants to continue
        if bankroll <= 0:
            print("You ran out of money! Game over.")
            break
        else:
            continue_playing = input("Do you want to keep playing? (yes/no): ").lower()
            if continue_playing != "yes":
                print(f"You left the game with ${bankroll}.")
                break

def play_single_hand(player_hand, dealer_hand, deck, bet):
    """Play a single hand of blackjack."""
    # Player's turn
    while True:
        # Give strategy advice
        advice = basic_strategy(player_hand, dealer_hand[0])
        print(f"Strategy advice: {advice}")

        # Get player's action
        action = input("Choose action: Hit, Stand, or Double Down: ").lower()
        if action == 'hit':
            player_hand.append(deal_card(deck))
            print(f"Your hand: {player_hand} (Value: {calculate_hand_value(player_hand)})")
            if calculate_hand_value(player_hand) > 21:
                print("You bust! Dealer wins.")
                return ["lose", bet]
        elif action == 'stand':
            break
        elif action == 'double down':
            if len(player_hand) == 2:
                player_hand.append(deal_card(deck))
                bet *= 2
                print(f"Your hand: {player_hand} (Value: {calculate_hand_value(player_hand)})")
                if calculate_hand_value(player_hand) > 21:
                    print("You bust! Dealer wins.")
                    return ["lose", bet]
                
            break

    # Dealer's turn
    print(f"Dealer's hand: {dealer_hand} (Value: {calculate_hand_value(dealer_hand)})")
    while calculate_hand_value(dealer_hand) < 17:
        dealer_hand.append(deal_card(deck))
        print(f"Dealer's hand: {dealer_hand} (Value: {calculate_hand_value(dealer_hand)})")

    # Determine winner
    player_value = calculate_hand_value(player_hand)
    dealer_value = calculate_hand_value(dealer_hand)

    rlist = []

    if dealer_value > 21 or player_value > dealer_value:
        return ["win", bet]
    elif player_value < dealer_value:
        return ["lose", bet]
    else:
        return ["tie", 0]



# Run the game
play_blackjack()
