import streamlit as st
import random
import time

st.set_page_config(page_title="Rudy's Blackjack", page_icon="🃏", layout="wide")

# --- RUDY's INSULT DICTIONARY ---
INSULTS = [
    "Are you going to hit that or just stare at it like it's a math problem?",
    "I've seen better hands on a broken clock.",
    "You're playing like you want to lose your house.",
    "Is this your first time playing, or are you always this tragic?",
    "I'd insult your strategy, but I don't think you have one.",
    "Hurry up, I'm rusting over here.",
    "Even a blind squirrel finds a nut sometimes, but you? Unlikely.",
    "I'm a bot and I still have more soul than your gameplay.",
    "Did you learn to play blackjack from a cereal box?"
]

# --- GLOBAL SHARED STATE ---
# @st.cache_resource keeps this dictionary alive across ALL active sessions
@st.cache_resource
def get_game_state():
    return {
        "players": {}, # format: "Name": {"hand": [], "status": "joined"}
        "dealer_hand": [],
        "deck": [],
        "game_active": False,
        "rudy_broadcast": "Welcome to my table. Try not to embarrass yourselves."
    }

state = get_game_state()

# --- HELPER FUNCTIONS ---
def build_deck():
    suits = ['♥️', '♦️', '♣️', '♠️']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return [f"{rank}{suit}" for suit in suits for rank in ranks]

def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        rank = card[:-1] # Remove the suit
        if rank in ['J', 'Q', 'K']:
            score += 10
        elif rank == 'A':
            aces += 1
            score += 11
        else:
            score += int(rank)
    
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

def deal_card(deck):
    if not deck:
        deck.extend(build_deck())
        random.shuffle(deck)
    return deck.pop()

# --- GAME LOGIC ---
def start_game():
    if len(state["players"]) == 0:
        st.warning("Need at least one player to start!")
        return
    
    state["deck"] = build_deck()
    random.shuffle(state["deck"])
    
    # Deal 2 cards to everyone
    for player in state["players"]:
        state["players"][player]["hand"] = [deal_card(state["deck"]), deal_card(state["deck"])]
        state["players"][player]["status"] = "playing"
        
    state["dealer_hand"] = [deal_card(state["deck"]), deal_card(state["deck"])]
    state["game_active"] = True
    state["rudy_broadcast"] = "Alright, cards are out. Let's see how fast you all ruin this."

def dealer_play():
    state["rudy_broadcast"] = "My turn. Watch and learn."
    while calculate_score(state["dealer_hand"]) < 17:
        state["dealer_hand"].append(deal_card(state["deck"]))
    
    dealer_score = calculate_score(state["dealer_hand"])
    if dealer_score > 21:
        state["rudy_broadcast"] = "I busted. Must be a glitch in my perfect code. You all got lucky."
    else:
        state["rudy_broadcast"] = f"I stand at {dealer_score}. Read 'em and weep."
    
    # Reset game state for next round but keep players at table
    state["game_active"] = False

# --- UI INTERFACE ---
st.title("🃏 Rudy's Blackjack")
st.markdown("*The only casino where the dealer actively hates you.*")

# 1. Join / Leave Sidebar
with st.sidebar:
    st.header("The Lobby")
    
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    # Login system
    if not st.session_state.player_name:
        new_name = st.text_input("Enter your name to sit at the table:")
        if st.button("Join Table") and new_name:
            if new_name in state["players"]:
                st.error("Name already taken at this table!")
            else:
                st.session_state.player_name = new_name
                state["players"][new_name] = {"hand": [], "status": "waiting"}
                state["rudy_broadcast"] = f"Oh great, {new_name} just sat down. There goes the neighborhood."
                st.rerun()
    else:
        name = st.session_state.player_name
        st.success(f"You are sitting at the table as **{name}**")
        if st.button("Leave Table"):
            del state["players"][name]
            st.session_state.player_name = ""
            state["rudy_broadcast"] = f"Finally, {name} left. I was getting a digital headache."
            st.rerun()

    st.divider()
    st.write("**Players at table:**")
    for p in state["players"]:
        st.write(f"- {p}")

# 2. Main Game Board
st.info(f"🤖 **Rudy says:** \"{state['rudy_broadcast']}\"")

# Manual refresh to see other players' moves
if st.button("🔄 Refresh Table"):
    st.rerun()

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🤖 Dealer (Rudy)")
    if state["game_active"]:
        # Hide Rudy's second card while game is ongoing
        first_card = state["dealer_hand"][0]
        st.write(f"Cards: {first_card} | [Hidden]")
    elif state["dealer_hand"]:
        # Reveal all if round is over
        cards_str = " | ".join(state["dealer_hand"])
        score = calculate_score(state["dealer_hand"])
        st.write(f"Cards: {cards_str}")
        st.write(f"Score: **{score}**")
    else:
        st.write("Waiting for game to start...")
        
    if not state["game_active"] and len(state["players"]) > 0:
        if st.button("Deal New Round"):
            start_game()
            st.rerun()

with col2:
    st.subheader("👥 The Victims (Players)")
    
    if not state["players"]:
        st.write("Table is empty. Waiting for fresh meat...")
    
    for p_name, p_data in state["players"].items():
        with st.container():
            st.markdown(f"**{p_name}** ({p_data['status']})")
            if p_data["hand"]:
                score = calculate_score(p_data["hand"])
                st.write(f"Cards: {' | '.join(p_data['hand'])} (Score: {score})")
                
                # Show action buttons only to the player who owns this hand
                if "player_name" in st.session_state and st.session_state.player_name == p_name:
                    if p_data["status"] == "playing":
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Hit", key=f"hit_{p_name}"):
                                p_data["hand"].append(deal_card(state["deck"]))
                                new_score = calculate_score(p_data["hand"])
                                if new_score > 21:
                                    p_data["status"] = "busted"
                                    state["rudy_broadcast"] = f"{p_name} busted with {new_score}. Shocking. Simply shocking. 😂"
                                else:
                                    state["rudy_broadcast"] = f"Hey {p_name}, {random.choice(INSULTS)}"
                                st.rerun()
                        with c2:
                            if st.button("Stand", key=f"stand_{p_name}"):
                                p_data["status"] = "stood"
                                state["rudy_broadcast"] = f"{p_name} is too scared to hit. Typical."
                                st.rerun()
            st.divider()

# Check if it's Rudy's turn (all players have acted)
if state["game_active"]:
    all_done = True
    for p in state["players"].values():
        if p["status"] == "playing":
            all_done = False
            break
            
    if all_done:
        dealer_play()
        st.rerun()

