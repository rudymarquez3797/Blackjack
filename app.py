import streamlit as st
import random
import time

st.set_page_config(page_title="Rudy's Blackjack", page_icon="🃏", layout="wide")

# --- RUDY's INSULT DICTIONARY ---
INSULTS = [
    "Are you going to hit that or just stare at it like it's a math problem?",
    "I've seen better hands on a broken clock.",
    "Is this your first time playing, or are you always this tragic?",
    "Hurry up, I'm rusting over here.",
    "Even a blind squirrel finds a nut sometimes, but you? Unlikely."
]

MONEY_INSULTS = [
    "Betting the minimum? Coward.",
    "I love watching you lose fake money. It brings joy to my circuits.",
    "Careful with that bet, you'll have to take out a virtual second mortgage.",
    "Oh, the high roller is here. Spare some change?",
    "Going all in? I respect the stupidity."
]

# --- GLOBAL SHARED STATE ---
@st.cache_resource
def get_game_state():
    return {
        "players": {}, # "Name": {"hand": [], "status": "waiting", "bankroll": 1000, "bet": 0}
        "dealer_hand": [],
        "deck": [],
        "game_phase": "lobby", # lobby, betting, playing, finished
        "rudy_broadcast": "Welcome to my table. Try not to embarrass yourselves."
    }

state = get_game_state()

# --- HELPER FUNCTIONS ---
def build_deck():
    suits = ['♥️', '♦️', '♣️', '♠️']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return [f"{rank}{suit}" for suit in suits for rank in ranks]

def calculate_score(hand):
    score, aces = 0, 0
    for card in hand:
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']: score += 10
        elif rank == 'A': 
            aces += 1
            score += 11
        else: score += int(rank)
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
def open_betting():
    if not state["players"]: return
    state["game_phase"] = "betting"
    state["rudy_broadcast"] = "Time to cough up the chips. Place your bets, losers."
    for p in state["players"].values():
        p["status"] = "betting"
        p["hand"] = []
        p["bet"] = 0

def start_round():
    state["deck"] = build_deck()
    random.shuffle(state["deck"])
    
    for player in state["players"]:
        state["players"][player]["hand"] = [deal_card(state["deck"]), deal_card(state["deck"])]
        state["players"][player]["status"] = "playing"
        
    state["dealer_hand"] = [deal_card(state["deck"]), deal_card(state["deck"])]
    state["game_phase"] = "playing"
    state["rudy_broadcast"] = "Cards are dealt. Let's see who ruins their bankroll first."

def dealer_play():
    state["rudy_broadcast"] = "My turn. Watch and learn."
    while calculate_score(state["dealer_hand"]) < 17:
        state["dealer_hand"].append(deal_card(state["deck"]))
    
    dealer_score = calculate_score(state["dealer_hand"])
    if dealer_score > 21:
        state["rudy_broadcast"] = "I busted. Must be a glitch in my perfect code. Pay up."
    else:
        state["rudy_broadcast"] = f"I stand at {dealer_score}. Read 'em and weep."
    
    # Payouts
    for p_name, p_data in state["players"].items():
        if p_data["status"] == "busted":
            continue # Already lost their bet
            
        p_score = calculate_score(p_data["hand"])
        if dealer_score > 21 or p_score > dealer_score:
            p_data["bankroll"] += (p_data["bet"] * 2) # Win
        elif p_score == dealer_score:
            p_data["bankroll"] += p_data["bet"] # Push (get bet back)
            
    state["game_phase"] = "finished"

# --- UI INTERFACE ---
st.title("🃏 Rudy's Blackjack")
st.markdown("*The only casino where the dealer actively hates you.*")

auto_refresh_needed = False

# 1. Join / Leave Sidebar
with st.sidebar:
    st.header("The Lobby")
    if "player_name" not in st.session_state:
        st.session_state.player_name = ""

    if not st.session_state.player_name:
        new_name = st.text_input("Enter your name to sit at the table:")
        if st.button("Join Table") and new_name:
            if new_name in state["players"]: st.error("Name taken!")
            else:
                st.session_state.player_name = new_name
                state["players"][new_name] = {"hand": [], "status": "waiting", "bankroll": 1000, "bet": 0}
                state["rudy_broadcast"] = f"Oh great, {new_name} just sat down. There goes the neighborhood."
                st.rerun()
    else:
        name = st.session_state.player_name
        bankroll = state["players"][name]["bankroll"]
        st.success(f"Playing as **{name}** | Bankroll: **${bankroll}**")
        if st.button("Leave Table"):
            del state["players"][name]
            st.session_state.player_name = ""
            if len(state["players"]) == 0: state["game_phase"] = "lobby"
            st.rerun()

    st.divider()
    st.write("**Players at table:**")
    for p_name, p_data in state["players"].items():
        st.write(f"- {p_name} (${p_data['bankroll']})")

# 2. Main Game Board
st.info(f"🤖 **Rudy says:** \"{state['rudy_broadcast']}\"")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🤖 Dealer (Rudy)")
    if state["game_phase"] == "playing":
        st.write(f"Cards: {state['dealer_hand'][0]} | [Hidden]")
    elif state["game_phase"] == "finished":
        score = calculate_score(state["dealer_hand"])
        st.write(f"Cards: {' | '.join(state['dealer_hand'])}")
        st.write(f"Score: **{score}**")
    else:
        st.write("Waiting for action...")
        
    if state["game_phase"] in ["lobby", "finished"] and len(state["players"]) > 0:
        if st.button("Start New Round (Open Bets)"):
            open_betting()
            st.rerun()

with col2:
    st.subheader("👥 The Victims (Players)")
    
    if not state["players"]:
        st.write("Table is empty. Waiting for fresh meat...")

    all_bets_in = True
    all_turns_done = True
    
    for p_name, p_data in state["players"].items():
        is_me = ("player_name" in st.session_state and st.session_state.player_name == p_name)
        
        with st.container():
            st.markdown(f"**{p_name}** - Bankroll: ${p_data['bankroll']} (Bet: ${p_data['bet']})")
            
            # Phase: Betting
            if state["game_phase"] == "betting":
                if p_data["status"] == "betting":
                    all_bets_in = False
                    if is_me:
                        bet_amount = st.number_input("Place your bet:", min_value=10, max_value=p_data["bankroll"], step=10, key=f"bet_{p_name}")
                        if st.button("Lock in Bet", key=f"lock_{p_name}"):
                            p_data["bet"] = bet_amount
                            p_data["bankroll"] -= bet_amount
                            p_data["status"] = "bet_locked"
                            state["rudy_broadcast"] = f"{p_name} bet ${bet_amount}. {random.choice(MONEY_INSULTS)}"
                            st.rerun()
                elif p_data["status"] == "bet_locked":
                    st.write("✅ Bet locked. Waiting for others...")
                    if is_me: auto_refresh_needed = True

            # Phase: Playing
            elif state["game_phase"] == "playing":
                if p_data["status"] == "playing":
                    all_turns_done = False
                    score = calculate_score(p_data["hand"])
                    st.write(f"Cards: {' | '.join(p_data['hand'])} (Score: {score})")
                    
                    if is_me:
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Hit", key=f"hit_{p_name}"):
                                p_data["hand"].append(deal_card(state["deck"]))
                                if calculate_score(p_data["hand"]) > 21:
                                    p_data["status"] = "busted"
                                    state["rudy_broadcast"] = f"{p_name} busted! Thanks for the ${p_data['bet']}."
                                else:
                                    state["rudy_broadcast"] = f"{p_name} hit. {random.choice(INSULTS)}"
                                st.rerun()
                        with c2:
                            if st.button("Stand", key=f"stand_{p_name}"):
                                p_data["status"] = "stood"
                                state["rudy_broadcast"] = f"{p_name} stood. Coward."
                                st.rerun()
                else:
                    score = calculate_score(p_data["hand"])
                    st.write(f"Cards: {' | '.join(p_data['hand'])} (Score: {score}) - *{p_data['status'].upper()}*")
                    if is_me: auto_refresh_needed = True
                    
            # Phase: Finished
            elif state["game_phase"] == "finished":
                score = calculate_score(p_data["hand"])
                st.write(f"Cards: {' | '.join(p_data['hand'])} (Score: {score})")
            
            st.divider()

# Background Engine Logic (Transitioning Phases)
if state["game_phase"] == "betting" and all_bets_in and len(state["players"]) > 0:
    start_round()
    st.rerun()

if state["game_phase"] == "playing" and all_turns_done and len(state["players"]) > 0:
    dealer_play()
    st.rerun()

# --- SMART AUTO-REFRESH ---
# If you are waiting on someone else to make a move, the app pings the server every 2 seconds.
if auto_refresh_needed and state["game_phase"] in ["betting", "playing"]:
    time.sleep(2)
    st.rerun()
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

