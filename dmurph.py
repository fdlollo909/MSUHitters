import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from PIL import Image


MASTER_PASSWORD = "beast"
USER_MAP = {
    "fishing": "Bright, Noah",
    "bsb": "Broski, Adam",
    "sofi": "Seymour, Randy",
    "mini": "McKay, Ryan",
    "illinois": "Murphy, Dayton",
    "ccc": "Deckinga, CJ",
    "mafia": "Williams, Nick",
    "movies": "Sturgess, Isaac",
    "dude": "Picot, Parker",
    "vmart": "Rice, Trent",
    "fours": "Domey, Isaiah",
    "chicago": "Thomas, Khamaree",
    "barber": "Elezaj, Anthony",
}

st.set_page_config(layout="wide")


# ========================
# LOAD DATA
# ========================
DATA_FOLDER = "data"
files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

dfs = []
for f in files:
    df = pd.read_csv(os.path.join(DATA_FOLDER, f))
    df["Game"] = f
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

# ========================
# DROPDOWNS
# ========================
msu_df = df[df["BatterTeam"] == "MIC_SPA"]
hitters = msu_df["Batter"].dropna().unique()
selected_hitter = "Murphy, Dayton"

# ✅ MASTER: can choose hitter

# ✅ PLAYER: locked hitter (no dropdown)
df_hitter = msu_df[msu_df["Batter"] == "Murphy, Dayton"]
st.title("Dayton Murphy Dashboard (TURN ON LIGHT MODE)")
games = df_hitter["Game"].unique()
selected_game = st.selectbox("Select Game", games)

df_game = df_hitter[df_hitter["Game"] == selected_game].copy()

# ========================
# FIX AT BATS (CRITICAL)
# ========================
df_game = df_game.sort_values(["Inning", "PAofInning", "PitchofPA"])

df_game["AB_ID"] = (
    df_game["PitchofPA"] == 1
).cumsum()

# ========================
# SUMMARY
# ========================
ab_ends = df_game.groupby("AB_ID").tail(1)
hits = df_game["PlayResult"].isin(["Single","Double","Triple","HomeRun"]).sum()
ab = df_game["AB_ID"].nunique()

hits = ab_ends["PlayResult"].isin(["Single","Double","Triple","HomeRun"]).sum()

official_ab = ab_ends[
    (~ab_ends["KorBB"].isin(["Walk"])) &
    (ab_ends["PitchCall"] != "HitByPitch")
].shape[0]

avg = hits / official_ab if official_ab else 0

walks = (ab_ends["KorBB"] == "Walk").sum()
hbp = (ab_ends["PitchCall"] == "HitByPitch").sum()

pa = len(ab_ends)

obp = (hits + walks + hbp) / pa if pa else 0

whiffs = (df_game["PitchCall"] == "StrikeSwinging").sum()
swings = df_game["PitchCall"].isin([
    "StrikeSwinging","FoulBall","FoulBallNotFieldable","InPlay"
]).sum()

whiff_rate = (whiffs / swings * 100) if swings else 0

# ========================
# BIP AVG (Batting Avg on Balls In Play)
# ========================

bip_df = df_game[df_game["PitchCall"] == "InPlay"]

bip = len(bip_df)

bip_hits = bip_df["PlayResult"].isin([
    "Single","Double","Triple","HomeRun"
]).sum()

bip_avg = (bip_hits / bip) if bip else 0

# ========================
# AVG EXIT VELO
# ========================

ev_df = df_game[df_game["PitchCall"] == "InPlay"]

avg_ev = ev_df["ExitSpeed"].mean() if len(ev_df) else 0
# ========================
# HARD HIT (FINAL CORRECT)
# ========================

bip_df = df_game[df_game["PitchCall"] == "InPlay"]

bip = len(bip_df)

hard_hit = (bip_df["ExitSpeed"] >= 95).sum()

hard_hit_rate = (hard_hit / bip * 100) if bip else 0

pitches = len(df_game)
pitches_per_ab = len(df_game) / ab if ab else 0
st.subheader("Summary")

c1, c2, c3 = st.columns(3)
c1.metric("AVG", f"{avg:.3f}")
c2.metric("PA", ab)
c3.metric("Hard Hit%", f"{hard_hit_rate:.1f}%")

c4, c5, c6 = st.columns(3)
c4.metric("OBP", f"{obp:.3f}")
c5.metric("Whiff Rate", f"{whiff_rate:.1f}%")
c6.metric("AVG Pitches/AB", f"{pitches_per_ab:.1f}")
c7, c8, c9 = st.columns(3)
c7.metric("BIP AVG", f"{bip_avg:.3f}")
c8.metric("Avg EV", f"{avg_ev:.1f}")
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Legend")

legend_cols = st.columns(6)

legend_cols[0].markdown("🔴 Strike Called")
legend_cols[1].markdown("🔵 Ball")
legend_cols[2].markdown("🟣 Strike Swinging")
legend_cols[3].markdown("🟠 In Play")
legend_cols[4].markdown("🟢 Foul")
legend_cols[5].markdown("⚫ HBP")
st.markdown("<br>", unsafe_allow_html=True)
# ========================
# MAPPINGS
# ========================
pitch_map = {
    "FourSeamFastBall": "4FB",
    "Fastball": "4FB",
    "TwoSeamFastBall": "2FB",
    "Sinker": "2FB",
    "Slider": "SL",
    "Curveball": "CB",
    "ChangeUp": "CH",
    "Splitter": "SPL",
    "Cutter": "CUT",
    "Sweeper": "SW",
    "Knuckleball": "KN"
}

pitch_full = {
    "4FB": "4-Seam",
    "2FB": "2-Seam",
    "SL": "Slider",
    "CB": "Curveball",
    "CH": "ChangeUp",
    "SPL": "Splitter",
    "CUT": "Cutter",
    "SW": "Sweeper",
    "KN": "Knuckleball"
}



# ========================
# STRIKEZONE
# ========================
ZONE_TOP = 3.5
ZONE_BOTTOM = 1.5
ZONE_LEFT = -0.83
ZONE_RIGHT = 0.83

BUFFER = 0.2

# ========================
# LEGEND
# ========================
def color_map(x):
    x = str(x)
    if "StrikeCalled" in x: return "red"
    if "BallCalled" in x: return "blue"
    if "StrikeSwinging" in x: return "purple"
    if "InPlay" in x: return "orange"
    if "Foul" in x: return "green"
    if "HitByPitch" in x: return "black"
    return "gray"

# ========================
# AT BATS
# ========================

st.markdown("<br>", unsafe_allow_html=True)
at_bats = sorted(df_game["AB_ID"].unique())

cols = st.columns(2)
def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1:"st",2:"nd",3:"rd"}.get(n % 10, "th")
    return str(n) + suffix
for i, ab_id in enumerate(at_bats):

    ab = df_game[df_game["AB_ID"] == ab_id]

    with cols[i % 2]:

        inning = ab["Inning"].iloc[0]
        st.markdown(f"### {ordinal(inning)} Inning")

        fig = go.Figure()

        # STRIKEZONE
        fig.add_shape(type="rect",
            x0=ZONE_LEFT, x1=ZONE_RIGHT,
            y0=ZONE_BOTTOM, y1=ZONE_TOP,
            line=dict(color="rgba(0,0,0,0.5)", width=2)
        )

        # FRINGE
        fig.add_shape(type="rect",
            x0=ZONE_LEFT-0.15, x1=ZONE_RIGHT+0.15,
            y0=ZONE_BOTTOM-0.15, y1=ZONE_TOP+0.15,
            line=dict(color="gray", width=1, dash="dash")
        )

        # AXES (THIS IS THE KEY)
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(range=[-2.0, 2.0], visible=False),
            yaxis=dict(range=[0.5, 4.5], visible=False),
        )

        # KEEP PROPORTIONS NORMAL
        fig.update_yaxes(scaleanchor="x", scaleratio=1)

        # plot pitches
        for _, row in ab.iterrows():

            x = -row["PlateLocSide"]
            y = row["PlateLocHeight"]

            pitch_num = int(row["PitchofPA"])
            ptype = pitch_map.get(row["TaggedPitchType"], "")

            label = f"<b>{pitch_num}) {ptype}</b>"

            fig.add_trace(go.Scatter(
                showlegend=False,
                x=[x],
                y=[y],
                mode="markers+text",
                text=[label],
                textposition="top center",
                marker=dict(color=color_map(row["PitchCall"]), size=12),
                textfont=dict(color="black", size=10)
            ))


        st.plotly_chart(fig, use_container_width=True)

        # ========================
        # TABLE (LAST PITCH)
        # ========================
        last = ab.iloc[-1]

        pitch_abbr = pitch_map.get(last["TaggedPitchType"], "")
        pitch_name = pitch_full.get(pitch_abbr, "")

        count = f"{last['Balls']}-{last['Strikes']}"

        speed = round(last["RelSpeed"],1) if not pd.isna(last["RelSpeed"]) else ""

        result = last["PlayResult"]

        # override with strikeout/walk
        if last["KorBB"] == "Strikeout":
            result = "Strikeout"
        elif last["KorBB"] == "Walk":
            result = "Walk"
        elif result == "Undefined":
            result = ""

        hit_type = last["TaggedHitType"]
        if hit_type == "Undefined":
            hit_type = ""
        else:
            hit_type = hit_type.replace("GroundBall","Ground Ball") \
                               .replace("FlyBall","Fly Ball") \
                               .replace("LineDrive","Line Drive") \
                               .replace("PopUp","Pop Up")

        exit_velo = round(last["ExitSpeed"]) if not pd.isna(last["ExitSpeed"]) else ""
        distance = f"{round(last['Distance'])} ft" if not pd.isna(last["Distance"]) else ""

        table_df = pd.DataFrame([{
            "Pitch": pitch_name,
            "Count": count,
            "Pitch Speed": speed,
            "Result": result,
            "Hit Type": hit_type,
            "Exit Velo": exit_velo,
            "Distance": distance
        }])

        st.dataframe(table_df, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

