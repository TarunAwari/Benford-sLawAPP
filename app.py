import streamlit as st
import math
import re
import os
import csv
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Benford's Law Game", layout="wide")

# ----------------------------
# Constants
# ----------------------------
BENFORD = [0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046]
CSV_FILE = "leaderboard.csv"

# ----------------------------
# Utility Functions
# ----------------------------
def chi_square_score(counts, benford, total):
    """Compute chi-square and convert to a smooth 0-100 score."""
    chi_sq = 0
    for i in range(9):
        O = counts[i]
        E = benford[i] * total
        if E > 0:
            chi_sq += (O - E) ** 2 / E

    # Softer scoring curve for fun gameplay
    k = 0.10      # steepness
    mid = 20      # midpoint of chi-square
    score = 100 / (1 + math.exp(k * (chi_sq - mid)))
    return round(score, 1)

def load_leaderboard():
    """Load leaderboard from CSV file."""
    if not os.path.exists(CSV_FILE):
        return []
    data = []
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            name, score, timestamp = row
            data.append({"name": name, "score": float(score), "timestamp": timestamp})
    return data

def save_leaderboard(board):
    """Save leaderboard to CSV file."""
    with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for entry in board:
            writer.writerow([entry["name"], entry["score"], entry["timestamp"]])

def feedback(score):
    if score >= 85:
        return "🎉 Excellent! Looks very natural!"
    elif score >= 60:
        return "🙂 Good! Could be a real dataset."
    elif score >= 30:
        return "😅 Noticeably biased, still okay for fun."
    else:
        return "😂 Clearly human-made!"

# ----------------------------
# App Initialization
# ----------------------------
st.title("🎯 Benford's Law Game")
st.write("Enter your **name** and a dataset of numbers. We'll check how natural it looks!")

# Username and data input
username = st.text_input("Enter your name:")
data_input = st.text_area("Enter your dataset numbers (space, comma, or newline separated):")

# Load leaderboard
if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = load_leaderboard()

# ----------------------------
# Process Dataset
# ----------------------------
if st.button("Submit"):
    # Validate inputs
    if not username.strip():
        st.error("❗ Please enter your name.")
        st.stop()
    numbers = re.findall(r"\d+", data_input)
    if len(numbers) < 5:
        st.error("❗ Please enter at least 5 numbers.")
        st.stop()

    # Count first digits
    counts = [0]*9
    for n in numbers:
        if n[0] != "0":
            d = int(n[0])
            if 1 <= d <= 9:
                counts[d-1] += 1

    total = sum(counts)
    observed = [c/total for c in counts]

    # Calculate score
    score = chi_square_score(counts, BENFORD, total)

    # Display feedback
    st.subheader(f"{username}, your score: **{score}/100**")
    st.write(feedback(score))

    # Confetti for high scores
    if score >= 85:
        st.balloons()

    # ----------------------------
    # Plot multiple bar chart
    # ----------------------------
    fig = go.Figure(data=[
        go.Bar(name="Observed", x=[str(i) for i in range(1,10)], y=observed),
        go.Bar(name="Benford", x=[str(i) for i in range(1,10)], y=BENFORD)
    ])
    fig.update_layout(
        barmode='group',
        title="First Digit Distribution: Observed vs Benford",
        xaxis_title="Digit",
        yaxis_title="Frequency"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # Update leaderboard
    # ----------------------------
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.leaderboard.append({
        "name": username,
        "score": score,
        "timestamp": timestamp
    })
    # Sort by score descending
    st.session_state.leaderboard = sorted(st.session_state.leaderboard, key=lambda x: x["score"], reverse=True)
    save_leaderboard(st.session_state.leaderboard)

# ----------------------------
# Display Leaderboard
# ----------------------------
st.subheader("🏆 Leaderboard")
if st.session_state.leaderboard:
    df = pd.DataFrame(st.session_state.leaderboard)
    df.index = df.index + 1  # Rank starting at 1
    df = df.rename(columns={"name": "Name", "score": "Score", "timestamp": "Time"})
    st.dataframe(df[["Name","Score","Time"]], height=400)
else:
    st.write("No entries yet. Be the first!")

# ----------------------------
# Admin Controls
# ----------------------------
st.subheader("🛠 Admin Controls")
if st.session_state.leaderboard:
    selected_name = st.selectbox(
        "Select an entry to edit/delete:",
        options=[entry["name"] for entry in st.session_state.leaderboard]
    )
    index = next(i for i, e in enumerate(st.session_state.leaderboard) if e["name"] == selected_name)
    new_name = st.text_input("Change name to:", value=selected_name)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Update Name"):
            st.session_state.leaderboard[index]["name"] = new_name
            save_leaderboard(st.session_state.leaderboard)
            st.success("Name updated!")
            st.experimental_set_query_params(_refresh=int(time.time()))

    with col2:
        if st.button("Delete Entry"):
            st.session_state.leaderboard.pop(index)
            save_leaderboard(st.session_state.leaderboard)
            st.warning("Entry deleted!")
            st.experimental_set_query_params(_refresh=int(time.time()))
            
