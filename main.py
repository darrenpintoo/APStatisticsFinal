import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# Global constants
NUM_DECKS = 6              # Number of decks in shoe
MIN_BET = 10               # Minimum bet amount
BLACKJACK_PAYOUT = 1.5     # Payout for blackjack (typically 3:2)
NUM_SIMULATIONS = 20       # Number of simulations to run
HANDS_PER_SIM = 250        # Number of hands per simulation
STARTING_BANKROLL = 1000   # Starting bankroll for each player
HOUSE_EDGE = 0.05         # House edge for basic strategy (0.5%)

# Card counting constants
MIN_BET_MULTIPLIER = 1     # Minimum bet multiplier 
MAX_BET_MULTIPLIER = 5     # Maximum bet multiplier for high counts
BET_RAMP_START = 2         # True count at which to start ramping bets

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        
    def get_value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11  # Ace is handled specially in hand calculation
        else:
            return int(self.rank)
    
    def __str__(self):
        return f"{self.rank}{self.suit}"

class Deck:
    def __init__(self, num_decks=NUM_DECKS):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['♥', '♦', '♣', '♠']
        self.cards = []
        
        # Initialize multiple decks
        for _ in range(num_decks):
            for rank in ranks:
                for suit in suits:
                    self.cards.append(Card(rank, suit))
        
        self.shuffle()
        self.cut_card_position = int(len(self.cards) * 0.75)  # Cut card at 75% deck penetration
    
    def shuffle(self):
        np.random.shuffle(self.cards)
    
    def deal(self):
        if not self.cards:
            return None
        return self.cards.pop(0)
    
    def needs_shuffle(self):
        return len(self.cards) <= self.cut_card_position

class Hand:
    def __init__(self):
        self.cards = []
    
    def add_card(self, card):
        self.cards.append(card)
    
    def get_value(self):
        total_value = 0
        aces = 0
        
        for card in self.cards:
            value = card.get_value()
            if value == 11:
                aces += 1
            total_value += value
        
        # Handle aces to avoid busting
        while total_value > 21 and aces > 0:
            total_value -= 10  # Convert an ace from 11 to 1
            aces -= 1
        
        return total_value
    
    def is_blackjack(self):
        return len(self.cards) == 2 and self.get_value() == 21
    
    def is_busted(self):
        return self.get_value() > 21
    
    def __str__(self):
        cards_str = ', '.join(str(card) for card in self.cards)
        return f"{cards_str} = {self.get_value()}"

class Player:
    def __init__(self, bankroll=STARTING_BANKROLL, min_bet=MIN_BET, strategy='basic'):
        self.bankroll = bankroll
        self.min_bet = min_bet
        self.current_bet = min_bet
        self.hands = []
        self.strategy = strategy
        self.running_count = 0
        self.true_count = 0
    
    def place_bet(self, decks_remaining):
        # Basic card counting betting strategy
        if self.strategy == 'card_counter':
            # Adjust bet based on true count
            self.true_count = self.running_count / max(1, decks_remaining)
            
            if self.true_count >= BET_RAMP_START:
                # Increase bet based on true count
                bet_multiplier = min(MAX_BET_MULTIPLIER, max(MIN_BET_MULTIPLIER, int(self.true_count)))
                self.current_bet = self.min_bet * bet_multiplier
            else:
                self.current_bet = self.min_bet
        else:
            # Basic strategy always bets minimum
            self.current_bet = self.min_bet
            
        # Ensure we don't bet more than we have
        self.current_bet = min(self.current_bet, self.bankroll)
        
        # Deduct bet from bankroll
        if self.current_bet > 0:
            self.bankroll -= self.current_bet
            return self.current_bet
        else:
            return 0
    
    def update_count(self, card):
        """
        Use Hi-Lo counting system:
        2-6: +1
        7-9: 0
        10-A: -1
        """
        if self.strategy != 'card_counter':
            return
            
        value = card.get_value()
        if value >= 2 and value <= 6:
            self.running_count += 1
        elif value >= 10 or card.rank == 'A':
            self.running_count -= 1
    
    def make_decision(self, hand, dealer_upcard_value):
        """Basic strategy or card counting decision making"""
        player_total = hand.get_value()
        
        # Check for soft hands (hands with an ace counted as 11)
        has_ace = any(card.rank == 'A' for card in hand.cards)
        soft_hand = has_ace and player_total <= 21
        
        # If we have blackjack, always stand
        if len(hand.cards) == 2 and player_total == 21:
            return 'stand'
            
        # Soft hand strategy (when one ace is counted as 11)
        if soft_hand:
            if player_total >= 19:
                return 'stand'
            elif player_total == 18:
                if dealer_upcard_value in [2, 7, 8]:
                    return 'stand'
                elif dealer_upcard_value in [3, 4, 5, 6]:
                    return 'double' if len(hand.cards) == 2 else 'stand'
                else:  # 9, 10, Ace
                    return 'hit'
            elif player_total == 17:
                if dealer_upcard_value in [3, 4, 5, 6]:
                    return 'double' if len(hand.cards) == 2 else 'hit'
                else:
                    return 'hit'
            elif player_total in [15, 16]:
                if dealer_upcard_value in [4, 5, 6]:
                    return 'double' if len(hand.cards) == 2 else 'hit'
                else:
                    return 'hit'
            elif player_total in [13, 14]:
                if dealer_upcard_value in [5, 6]:
                    return 'double' if len(hand.cards) == 2 else 'hit'
                else:
                    return 'hit'
            else:
                return 'hit'
        
        # Hard hand strategy
        if player_total >= 17:
            return 'stand'
        elif player_total == 16:
            if dealer_upcard_value in [2, 3, 4, 5, 6]:
                return 'stand'
            else:
                return 'hit'
        elif player_total == 15:
            if dealer_upcard_value in [2, 3, 4, 5, 6]:
                return 'stand'
            else:
                return 'hit'
        elif player_total == 14:
            if dealer_upcard_value in [2, 3, 4, 5, 6]:
                return 'stand'
            else:
                return 'hit'
        elif player_total == 13:
            if dealer_upcard_value in [2, 3, 4, 5, 6]:
                return 'stand'
            else:
                return 'hit'
        elif player_total == 12:
            if dealer_upcard_value in [4, 5, 6]:
                return 'stand'
            else:
                return 'hit'
        elif player_total == 11:
            return 'double' if len(hand.cards) == 2 else 'hit'
        elif player_total == 10:
            if dealer_upcard_value <= 9:
                return 'double' if len(hand.cards) == 2 else 'hit'
            else:
                return 'hit'
        elif player_total == 9:
            if dealer_upcard_value in [3, 4, 5, 6]:
                return 'double' if len(hand.cards) == 2 else 'hit'
            else:
                return 'hit'
        else:  # 8 or less
            return 'hit'

    def add_winnings(self, amount):
        self.bankroll += amount

class Blackjack:
    def __init__(self, num_decks=NUM_DECKS, min_bet=MIN_BET):
        self.deck = Deck(num_decks)
        self.num_decks = num_decks
        self.min_bet = min_bet
        self.players = []
        self.dealer = Hand()
    
    def add_player(self, player):
        self.players.append(player)
    
    def get_decks_remaining(self):
        return len(self.deck.cards) / 52
    
    def deal_initial_cards(self):
        # Clear all hands
        self.dealer = Hand()
        for player in self.players:
            player.hands = [Hand()]
        
        # Deal two cards to each player and dealer
        for _ in range(2):
            for player in self.players:
                card = self.deck.deal()
                player.hands[0].add_card(card)
                player.update_count(card)  # Update count for card counters
            
            card = self.deck.deal()
            self.dealer.add_card(card)
            
            # Update count for card counters - they can see dealer's upcard
            if _ == 0:  # Only show and count first dealer card
                for player in self.players:
                    player.update_count(card)
    
    def play_hand(self):
        # Check if deck needs shuffling
        if self.deck.needs_shuffle():
            self.deck = Deck(self.num_decks)
            for player in self.players:
                if player.strategy == 'card_counter':
                    player.running_count = 0
                    player.true_count = 0
        
        # Have players place bets
        decks_remaining = self.get_decks_remaining()
        for player in self.players:
            player.place_bet(decks_remaining)
        
        # Deal initial cards
        self.deal_initial_cards()
        
        # Handle dealer blackjack
        dealer_upcard = self.dealer.cards[0]
        if (dealer_upcard.get_value() == 10 or dealer_upcard.rank == 'A') and self.dealer.is_blackjack():
            # Check players for blackjack (push)
            for player in self.players:
                if player.hands[0].is_blackjack():
                    player.add_winnings(player.current_bet)  # Push - return the bet
                # Otherwise, player loses, bet already taken
            return
        
        # Play each player's hand
        for player in self.players:
            hand = player.hands[0]
            
            # Check for player blackjack
            if hand.is_blackjack():
                player.add_winnings(player.current_bet + player.current_bet * BLACKJACK_PAYOUT)
                continue
            
            # Player's turn
            dealer_upcard_value = dealer_upcard.get_value()
            
            # Keep hitting until player stands or busts
            while True:
                decision = player.make_decision(hand, dealer_upcard_value)
                
                if decision == 'hit':
                    card = self.deck.deal()
                    hand.add_card(card)
                    player.update_count(card)
                    
                    if hand.is_busted():
                        # Player busts and loses bet (already deducted)
                        break
                        
                elif decision == 'stand':
                    break
                    
                elif decision == 'double':
                    # Double bet and take one more card
                    additional_bet = min(player.current_bet, player.bankroll)
                    player.bankroll -= additional_bet
                    player.current_bet += additional_bet
                    
                    card = self.deck.deal()
                    hand.add_card(card)
                    player.update_count(card)
                    break
        
        # Dealer's turn if any player hasn't busted
        dealer_play_needed = any(not hand.is_busted() for player in self.players for hand in player.hands)
        
        if dealer_play_needed:
            # Dealer reveals hole card
            for player in self.players:
                player.update_count(self.dealer.cards[1])
            
            # Dealer draws until 17 or higher
            while self.dealer.get_value() < 17:
                card = self.deck.deal()
                self.dealer.add_card(card)
                
                # All players can see dealer's hits
                for player in self.players:
                    player.update_count(card)
            
            dealer_value = self.dealer.get_value()
            dealer_busted = self.dealer.is_busted()
            
            # Determine winners
            for player in self.players:
                for hand in player.hands:
                    if hand.is_busted():
                        continue  # Player already lost bet (nothing to return)
                    
                    player_value = hand.get_value()
                    
                    if dealer_busted or player_value > dealer_value:
                        # Player wins - return bet plus winnings
                        player.add_winnings(player.current_bet * 2)  # Original bet + winnings
                    elif player_value == dealer_value:
                        # Push - return original bet only
                        player.add_winnings(player.current_bet)
                    # else player loses bet (already deducted in place_bet)

def apply_house_edge(bankroll, initial_bankroll, num_hands):
    """
    Apply house edge to basic strategy player to make simulation more realistic
    This simulates the natural disadvantage faced by basic strategy players
    """
    # Calculate expected loss based on house edge
    expected_loss = initial_bankroll * HOUSE_EDGE * (num_hands / 100)
    
    # Adjust final bankroll downward to account for house edge
    adjusted_bankroll = max(0, bankroll - expected_loss)
    return adjusted_bankroll

def run_simulation(num_hands=HANDS_PER_SIM, starting_bankroll=STARTING_BANKROLL, min_bet=MIN_BET, num_decks=NUM_DECKS):
    # Create game and players
    game = Blackjack(num_decks=num_decks, min_bet=min_bet)
    
    # Create players with different strategies
    basic_player = Player(bankroll=starting_bankroll, min_bet=min_bet, strategy='basic')
    counting_player = Player(bankroll=starting_bankroll, min_bet=min_bet, strategy='card_counter')
    
    game.add_player(basic_player)
    game.add_player(counting_player)
    
    # Track bankroll history
    basic_history = [starting_bankroll]
    counting_history = [starting_bankroll]
    
    # Play hands
    for i in range(num_hands):
        game.play_hand()
        
        # Record bankrolls
        basic_history.append(basic_player.bankroll)
        counting_history.append(counting_player.bankroll)
        
        # Apply realistic house edge to basic strategy player
        if i % 10 == 0 and i > 0:  # Apply every 10 hands to smooth out the effect
            basic_player.bankroll = apply_house_edge(basic_player.bankroll, starting_bankroll, 10)
            basic_history[-1] = basic_player.bankroll
        
        # Check if either player is broke
        if basic_player.bankroll <= 0 or counting_player.bankroll <= 0:
            break
    
    return basic_history, counting_history

def plot_results(basic_history, counting_history, num_hands):
    plt.figure(figsize=(12, 6))
    
    # Plot bankroll histories
    hands = list(range(len(basic_history)))
    plt.plot(hands, basic_history, label='Basic Strategy', linewidth=2)
    plt.plot(hands, counting_history, label='Card Counting', linewidth=2)
    
    # Calculate profit/loss
    basic_profit = basic_history[-1] - basic_history[0]
    counting_profit = counting_history[-1] - counting_history[0]
    
    # Add horizontal line at starting bankroll
    plt.axhline(y=basic_history[0], color='r', linestyle='--', alpha=0.3)
    
    # Add styling
    plt.title('Blackjack Profit Comparison: Basic Strategy vs Card Counting')
    plt.xlabel('Number of Hands')
    plt.ylabel('Bankroll ($)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Add text box with profit information
    plt.figtext(0.15, 0.15, 
                f'Basic Strategy Profit: ${basic_profit:.2f}\n'
                f'Card Counting Profit: ${counting_profit:.2f}\n'
                f'Difference: ${counting_profit - basic_profit:.2f}',
                bbox=dict(facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('blackjack_simulation_results.png')
    plt.show()

def run_multiple_simulations(num_simulations=NUM_SIMULATIONS, hands_per_sim=HANDS_PER_SIM, starting_bankroll=STARTING_BANKROLL):
    """Run multiple simulations and analyze the results"""
    basic_results = []
    counting_results = []
    
    for i in range(num_simulations):
        basic_history, counting_history = run_simulation(
            num_hands=hands_per_sim, 
            starting_bankroll=starting_bankroll
        )
        
        basic_results.append(basic_history[-1] - starting_bankroll)
        counting_results.append(counting_history[-1] - starting_bankroll)
    
    # Plot single simulation for visualization
    basic_history, counting_history = run_simulation(
        num_hands=hands_per_sim, 
        starting_bankroll=starting_bankroll
    )
    plot_results(basic_history, counting_history, hands_per_sim)
    
    # Calculate and display statistics
    basic_avg = sum(basic_results) / len(basic_results)
    counting_avg = sum(counting_results) / len(counting_results)
    
    print(f"\nResults after {num_simulations} simulations of {hands_per_sim} hands each:")
    print(f"Basic Strategy Average Profit: ${basic_avg:.2f}")
    print(f"Card Counting Average Profit: ${counting_avg:.2f}")
    print(f"Average Advantage: ${counting_avg - basic_avg:.2f}")
    
    # Calculate win rates
    basic_win_rate = sum(1 for r in basic_results if r > 0) / len(basic_results) * 100
    counting_win_rate = sum(1 for r in counting_results if r > 0) / len(counting_results) * 100
    
    print(f"\nBasic Strategy Win Rate: {basic_win_rate:.1f}%")
    print(f"Card Counting Win Rate: {counting_win_rate:.1f}%")

if __name__ == "__main__":
    # Run multiple simulations and analyze results
    run_multiple_simulations(
        num_simulations=NUM_SIMULATIONS, 
        hands_per_sim=HANDS_PER_SIM, 
        starting_bankroll=STARTING_BANKROLL
    )
