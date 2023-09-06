import tkinter as tk
from random import shuffle
from PIL import Image, ImageTk
import csv
import os
from datetime import datetime
import copy

now = datetime.now()
date_string = now.strftime("%Y-%m-%d")

csv_filename = f'game_data_{date_string}.csv'

headers = [
    'bin_1_cards',
    'bin_2_cards',
    'bin_3_cards',
    'bin_4_cards',
    'bin_1_total',
    'bin_2_total',
    'bin_3_total',
    'bin_4_total',
    'stash_card',
    'flipped_card',
    'score',
    'remaining_time',
    'streak_counter',
    'stash_usage_counter',
    'action',
    'time_left',
    'cards_left_in_deck',
    'score_change',
    'streak_counter_change'
    'remaining_cards'
]

# Check if the CSV file already exists
if not os.path.isfile(csv_filename):
    # Create the CSV file and write the headers
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

def log_game_state(action, time_left, cards_left_in_deck, score_change, streak_counter_change):
    with open(csv_filename, 'a', newline='') as f:
        writer = csv.writer(f)
        # Create a list of the current game state
        game_state = [
            str(bin_cards[bin_positions[0]]),
            str(bin_cards[bin_positions[1]]),
            str(bin_cards[bin_positions[2]]),
            str(bin_cards[bin_positions[3]]),
            str(sum([card_value(card['value']) for card in bin_cards[bin_positions[0]]])),
            str(sum([card_value(card['value']) for card in bin_cards[bin_positions[1]]])),
            str(sum([card_value(card['value']) for card in bin_cards[bin_positions[2]]])),
            str(sum([card_value(card['value']) for card in bin_cards[bin_positions[3]]])),
            str(card_map[stashed_card] if stashed_card else None),
            str(card_map[flipped_card] if flipped_card else None),
            str(total_score),
            str(remaining_time),
            str(streak_counter),
            str(stash_usage_counter),
            action,
            time_left,
            cards_left_in_deck,
            score_change,
            streak_counter_change,
             ','.join([f"{card['suit']}_{card['value']}" for card in deck])  # Add remaining cards as a single string
        ]
        # Write the game state to the CSV file
        writer.writerow(game_state)

# Define the cards
suits = ['H', 'D', 'C', 'S']
values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# Create a shuffled deck
jokers = [{'suit': 'joker', 'value': 'joker'}, {'suit': 'joker_2', 'value': 'joker_2'}]
deck = [{'suit': suit, 'value': value} for suit in suits for value in values] + jokers
shuffle(deck)
card_map = {}

# Create the game window
root = tk.Tk()
root.title("Bringing Cash")
canvas = tk.Canvas(root, bg="green", width=800, height=600)
canvas.pack(pady=20)

# Load card images
card_images = {}
for card in deck:
    card_key = f"{card['suit']}_{card['value']}" if card['value'] != "joker" and card['value'] != "joker_2" else card['value']
    image = Image.open(f"{card_key}.png")
    image = image.resize((80, 120), Image.LANCZOS)
    card_images[card_key] = ImageTk.PhotoImage(image)

# Load the deck's backside image
deck_back_image = Image.open("AI-GEN-WOMEN.jpg")
deck_back_image = deck_back_image.resize((80, 120), Image.LANCZOS)
deck_back_image = ImageTk.PhotoImage(deck_back_image)

# Display the deck
deck_position = (300, 480)
canvas.create_image(*deck_position, image=deck_back_image)

# Create 4 bins across the center of the screen
bin_positions = [(150, 300), (300, 300), (450, 300), (600, 300)]
bins = [canvas.create_rectangle(pos[0]-40, pos[1]-75, pos[0]+40, pos[1]+75, fill="gray") for pos in bin_positions]

# Display the score on the canvas
score_text = canvas.create_text(400, 20, text="Score: 0", font=('Arial', 16, 'bold'))

# Dictionary to track cards in each bin
bin_cards = {pos: [] for pos in bin_positions}
bin_card_objects = {pos: [] for pos in bin_positions}
sum_texts = {pos: canvas.create_text(pos[0], pos[1]-100, text="", font=('Arial', 12, 'bold')) for pos in bin_positions}

# Streak counter and total score initialization
streak_counter = 0
total_score = 0
stash_usage_counter = 0

# Create a stash bin
stash_position = (680, 480)
canvas.create_rectangle(stash_position[0]-40, stash_position[1]-75, stash_position[0]+40, stash_position[1]+75, fill="gray")
stashed_card = None

streak_text = canvas.create_text(700, 20, text=f"Streak: {streak_counter}", font=('Arial', 16, 'bold'))

# Timer Initialization
remaining_time = 180  # 3 minutes in seconds
timer_text = canvas.create_text(60, 20, text="3:00", font=('Arial', 16, 'bold'))
game_over = False

def update_timer():
    global remaining_time, total_score, game_over

    if game_over:
        return

    if remaining_time > 0:
        remaining_time -= 1
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        canvas.itemconfig(timer_text, text=f"{minutes}:{seconds:02}")
        root.after(1000, update_timer)
    else:
        game_over = True
        canvas.create_text(400, 300, text="Round Over!", font=('Arial', 24, 'bold'), fill="red")
        writer.writerow("NEW GAME")
        # Check for no-bust bonus
        if all(determine_ace_value(cards) <= 21 for cards in bin_cards.values()):
            total_score += 250  # Bonus for no busts
            canvas.itemconfig(score_text, text=f"Score: {total_score}")

    if remaining_time == 0 or (not deck and not flipped_card and not stashed_card):
        game_over = True
        canvas.create_text(400, 300, text="Round Over!", font=('Arial', 24, 'bold'), fill="red")

# Start the timer
update_timer()

def card_value(value):
    """Returns the numerical value of a card."""
    if value in ["J", "Q", "K"]:
        return 10
    elif value == "A":
        return 1  # Consider Ace as 1 for simplicity
    elif value in ["joker", "joker_2"]:
        return 0
    else:
        return int(value)

def determine_ace_value(card_list):
    """Determine the best value for Ace in the card list."""
    total_without_ace = sum([card_value(card["value"]) for card in card_list if card["value"] != "A"])
    number_of_aces = len([card for card in card_list if card["value"] == "A"])
    
    # Start by considering all Aces as 11
    total_with_aces_as_11 = total_without_ace + (number_of_aces * 11)
    
    while total_with_aces_as_11 > 21 and number_of_aces > 0:
        # Convert one Ace from 11 to 1
        total_with_aces_as_11 -= 10
        number_of_aces -= 1

    return total_with_aces_as_11

def clear_bin(bin_position):
    """Clear the bin (discard the cards and reset the sum display)"""
    for card_obj in bin_card_objects[bin_position]:
        canvas.delete(card_obj)
    bin_card_objects[bin_position] = []  # Reset the list of card objects for the bin
    bin_cards[bin_position] = []
    canvas.itemconfig(sum_texts[bin_position], text="")

def update_streak_display():
    """Update the streak counter display on the canvas."""
    canvas.itemconfig(streak_text, text=f"Streak: {streak_counter}")

def calculate_bin_score(bin_position):
    global total_score, streak_counter, scored_this_turn

    card_list = bin_cards[bin_position]

    # Handle Joker cards: they should always score and clear the bin
    if any([card for card in card_list if card["value"] in ["joker", "joker_2"]]):
        total_score += 500  # Joker bonus + bin clearing bonus
        streak_counter += 1  # Increment the streak counter for jokers
        clear_bin(bin_position)
        scored_this_turn = True  # Set the flag to True when a joker card is played
        canvas.itemconfig(score_text, text=f"Score: {total_score}")
        return  # Exit the function early to ensure no further processing occurs for this bin

    contains_ace = any([card for card in card_list if card["value"] == "A"])
    total_value = determine_ace_value(card_list)

    # Update the bin total
    if contains_ace and total_value + 10 <= 21:
        canvas.itemconfig(sum_texts[bin_position], text=f"{total_value-10}/{total_value}")
    else:
        canvas.itemconfig(sum_texts[bin_position], text=str(total_value))

    # If the bin scores or 5 card charlie
    if total_value == 21 or (len(card_list) == 5 and total_value <= 21):
        streak_counter += 1  # Increment by one only
        scored_this_turn = True
        clear_bin(bin_position)

        # Adjust the score accordingly
        total_score += 250
        if len(card_list) == 5 and total_value == 21:
            total_score += 750  # Bonus for 21 with 5 cards

        # Streak bonus scoring
        if streak_counter == 2:
            total_score += 300
        elif streak_counter == 3:
            total_score += 600
        elif streak_counter == 4:
            total_score += 900
        elif streak_counter == 5:
            total_score += 1200
        elif streak_counter >= 6:
            total_score += 1500
    elif total_value > 21:  # If bin busts
        total_score = max(total_score - 250, 0)  # Score can't go below 0
        streak_counter = 0  # Reset streak counter on bust
        scored_this_turn = False
        clear_bin(bin_position)
    else:
        scored_this_turn = False

    canvas.itemconfig(score_text, text=f"Score: {total_score}")

# Undo action related variables
undo_counter = 0
previous_actions = []



 
# Display the stash usage on the canvas
stash_usage_text = canvas.create_text(700, 390, text=f"Stash usage: {stash_usage_counter}", font=('Arial', 14, 'bold'))

flipped_card = None
if deck:
    card = deck.pop()
    card_key = f"{card['suit']}_{card['value']}" if card['value'] != "joker" and card['value'] != "joker_2" else card['value']
    flipped_card = canvas.create_image(deck_position[0] + 90, deck_position[1], image=card_images[card_key])
    card_map[flipped_card] = card

temp_holding_card = None

reverse_card_counter_text = canvas.create_text(60, 40, text=f"Cards Left: {len(deck)}", font=('Arial', 14, 'bold'))

# Create an array of all available cards (including jokers)
all_cards = [{'suit': suit, 'value': value} for suit in suits for value in values] + jokers


def on_canvas_click(event):
    global flipped_card, stashed_card, streak_counter, temp_holding_card, scored_this_turn, stash_usage_counter, previous_actions, total_score

    # Save the current game state before any action is taken
    previous_actions.append([flipped_card, stashed_card, stash_usage_counter, copy.deepcopy(bin_cards), copy.deepcopy(bin_card_objects), streak_counter, total_score])

    if game_over:
        return
    
    scored_this_turn = None
    action = ''
    score_before_action = total_score
    streak_counter_before_action = streak_counter

    canvas.itemconfig(reverse_card_counter_text, text=f"Cards Left: {len(deck)}")

    # Save the current game state for undo action
    if flipped_card or stashed_card or any(bin_cards.values()):  # Don't save state if no action has been taken
        previous_actions.append([flipped_card, stashed_card, stash_usage_counter, copy.deepcopy(bin_cards), copy.deepcopy(bin_card_objects), streak_counter, total_score])
    # Check if stash bin is clicked
    if stash_position[0] - 40 < event.x < stash_position[0] + 40 and stash_position[1] - 75 < event.y < stash_position[1] + 75:
        # If there's no stashed card and there's an active card
        if not stashed_card and flipped_card:
            stash_usage_counter += 1
            canvas.itemconfig(stash_usage_text, text=f"Stash usage: {stash_usage_counter}")
            # Move active card to stash
            canvas.move(flipped_card, stash_position[0] - canvas.coords(flipped_card)[0], stash_position[1] - canvas.coords(flipped_card)[1])
            if card_map[flipped_card] in all_cards:  # Check if the card exists in the list before removing
                all_cards.remove(card_map[flipped_card])
            stashed_card, flipped_card = flipped_card, None
            
            action = 'Move active card to stash'
            
        if not deck and stashed_card and not flipped_card:
            # Move the stashed card to the active position
            canvas.move(stashed_card, deck_position[0] + 90 - canvas.coords(stashed_card)[0], deck_position[1] - canvas.coords(stashed_card)[1])
            flipped_card, stashed_card = stashed_card, None
            all_cards.append(card_map[flipped_card])
        # If there's a stashed card and there's an active card
        elif stashed_card and flipped_card and stash_usage_counter < 3:
            
            # Move active card off-screen
            canvas.move(flipped_card, -1000, 0)  # Move the active card off-screen
            temp_holding_card = flipped_card
            
            # Move the stashed card to the active position
            canvas.move(stashed_card, deck_position[0] + 90 - canvas.coords(stashed_card)[0], deck_position[1] - canvas.coords(stashed_card)[1])
            if card_map[stashed_card] not in all_cards:  # Add the card back to all_cards if it's not already there
                all_cards.append(card_map[stashed_card])
            flipped_card, stashed_card = stashed_card, None
            action = 'play stash card'
            # Add the card back to all_cards
            all_cards.append(card_map[flipped_card])
    else:
        # If any bin is clicked and there's an active card
        for bx, by in bin_positions:
            if bx - 40 < event.x < bx + 40 and by - 75 < event.y < by + 75 and flipped_card:
                # Remove the card from all_cards
                all_cards.remove(card_map[flipped_card])
                # Handle the logic related to placing card in the bins
                card = card_map[flipped_card]
                bin_cards[(bx, by)].append(card)
                cy = by + (len(bin_cards[(bx, by)]) - 1) * 30
                # Move the card to the bin and adjust its position based on existing cards
                canvas.move(flipped_card, bx - canvas.coords(flipped_card)[0], cy - canvas.coords(flipped_card)[1])
                bin_card_objects[(bx, by)].append(flipped_card)
                flipped_card = None
                calculate_bin_score((bx, by))
                action = 'stash active card'
                break

    # If there's a card in the temporary holding area, bring it back to the active spot
    if temp_holding_card and not flipped_card:
        canvas.move(temp_holding_card, deck_position[0] + 90 - canvas.coords(temp_holding_card)[0], deck_position[1] - canvas.coords(temp_holding_card)[1])
        flipped_card = temp_holding_card
        temp_holding_card = None
        action = 'retrieve card from holding'
    # If the active card spot is empty and there are cards left in the deck, draw a new card
    elif not flipped_card and deck:
        card = deck.pop()
        card_key = f"{card['suit']}_{card['value']}" if card['value'] != "joker" and card['value'] != "joker_2" else card['value']
        flipped_card = canvas.create_image(deck_position[0] + 90, deck_position[1], image=card_images[card_key])
        card_map[flipped_card] = card
        action = 'Draw new card'

    # Check if a scoring move was made this turn and adjust the streak counter
    if scored_this_turn is not None:
        if not scored_this_turn:
            streak_counter = 0  # Reset streak counter on non-scoring move
        update_streak_display()
    log_game_state(
        action,  # The action taken
        remaining_time,  # The remaining time
        len(deck),  # The number of cards left in the deck
        total_score - score_before_action,  # The change in score
        streak_counter - streak_counter_before_action  # The change in streak counter
    )
    

canvas.bind("<Button-1>", on_canvas_click)
root.mainloop()
