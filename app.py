import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 🔧 Page config must be first
st.set_page_config(page_title="IPL Score Stream", layout="centered")

# 🔄 Auto-refresh every 5 seconds
st_autorefresh(interval=5000, limit=None, key="ipl_autorefresh")

BASE_URL = "https://www.cricbuzz.com"
current_year = datetime.now().year

# 🔍 Keywords that indicate a live match status
LIVE_KEYWORDS = ["won the toss", "opt", "elect", "need", "needs", "chose to"]

# -------------------- LIVE IPL FUNCTION --------------------
def fetch_live_ipl_matches():
    url = f"{BASE_URL}/cricket-match/live-scores"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    live_matches = []
    match_sections = soup.find_all("div", class_="cb-col cb-col-100 cb-plyr-tbody cb-rank-hdr cb-lv-main")

    for section in match_sections:
        header = section.find("h2", class_="cb-lv-grn-strip")
        if not header or not header.find("span", class_="cb-plus-ico cb-ico-live-stream"):
            continue

        match_blocks = section.find_all("div", class_="cb-mtch-lst")
        for block in match_blocks:
            title_tag = block.find("h3", class_="cb-lv-scr-mtch-hdr")
            match_title = title_tag.get_text(strip=True).rstrip(',') if title_tag else "N/A"

            team1_block = block.find("div", class_="cb-hmscg-bwl-txt")
            team1_score = team1_block.find_all("div", class_="cb-ovr-flo")[1].text.strip() if team1_block else "N/A"

            team2_block = block.find("div", class_="cb-hmscg-bat-txt")
            team2_score = team2_block.find_all("div", class_="cb-ovr-flo")[1].text.strip() if team2_block else "N/A"

            status_tag = block.find("div", class_="cb-text-live")
            match_status = status_tag.text.strip() if status_tag else ""

            # 🧠 Partial match logic
            match_status_lower = match_status.lower()
            if any(keyword in match_status_lower for keyword in LIVE_KEYWORDS):
                live_matches.append({
                    "Match Title": match_title,
                    "Batting Score": team2_score,
                    "Bowling Score": team1_score,
                    "Status": match_status
                })

    return live_matches

# -------------------- UI --------------------
st.title("🏏 IPL Score Stream")
st.markdown(f"⏱️ Last updated: {datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# 🔴 LIVE MATCHES
live_scores = fetch_live_ipl_matches()
st.subheader("🟢 Live Matches")

if live_scores:
    for match in live_scores:
        st.markdown(f"#### 🔥 {match['Match Title']}")
        st.markdown(f"🏏 **Batting Side**: {match['Batting Score']}")
        st.markdown(f"🎯 **Bowling Side**: {match['Bowling Score']}")
        st.markdown(f"📣 **Status**: {match['Status']}")
        st.markdown("---")
else:
    st.warning("❌ No live IPL matches currently.")
