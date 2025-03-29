import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from logger.app_logger import app_logger

IPL_TEAMS = [
    "Chennai Super Kings", "Delhi Capitals", "Gujarat Titans", "Kolkata Knight Riders",
    "Lucknow Super Giants", "Mumbai Indians", "Punjab Kings", "Rajasthan Royals",
    "Royal Challengers Bangalore", "Sunrisers Hyderabad"
]

BASE_URL = "https://www.cricbuzz.com"

# Dynamically get the current IPL year
current_year = datetime.now().year
app_logger.log_info(f"📅 Current year detected: {current_year}")

# Detect team
def detect_team(user_input):
    app_logger.log_info(f"🟢 [DETECT] Input: {user_input}")
    for team in IPL_TEAMS:
        if team.lower() in user_input.lower():
            app_logger.log_info(f"✅ [DETECT] Found team: {team}")
            return team
    app_logger.log_warning("❌ [DETECT] No IPL team found")
    return None

# Get live matches from cricbuzz homepage
def get_live_scores(team_name=None):
    app_logger.log_info("🌐 [LIVE] Fetching live scores page...")
    url = "https://www.cricbuzz.com/cricket-match/live-scores"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    app_logger.log_info(f"✅ [LIVE] Response code: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    matches = soup.find_all("div", class_="cb-col cb-col-100 cb-ltst-wgt-hdr")
    app_logger.log_info(f"🔍 [LIVE] Found {len(matches)} match blocks")

    results = []
    for block in matches:
        text = block.get_text(separator=" ").strip()
        if team_name is None or team_name.lower() in text.lower():
            results.append("🟢 LIVE: " + text)
            app_logger.log_info(f"✅ [LIVE MATCH] {text[:100]}...")

    return results[:5] if results else []

# Get recent results if no live match
def get_recent_results(team_name=None):
    try:
        url = f"{BASE_URL}/cricket-series/9237/Indian-Premier-League-{current_year}/matches"
        app_logger.log_info(f"🌐 Fetching matches from: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        app_logger.log_info(f"✅ Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        all_tags = soup.find_all("a", href=True)
        app_logger.log_info(f"🔍 Total <a> tags: {len(all_tags)}")

        won, lost = [], []

        for i in range(len(all_tags) - 1):
            tag = all_tags[i]
            next_tag = all_tags[i + 1]

            href = tag['href']
            title = tag.get_text().strip()
            result = next_tag.get_text().strip()

            if "cricket-scores" in href and any(t.lower() in title.lower() for t in IPL_TEAMS):
                full_url = BASE_URL + href
                full_text = f"{title} – {result}\n[View Match]({full_url})"

                if team_name and team_name.lower() not in title.lower():
                    continue

                if "won by" in result.lower():
                    app_logger.log_info(f"✅ [WON] {title} => {result}")
                    won.append(full_text)
                elif "lost" in result.lower():
                    app_logger.log_info(f"🟥 [LOST] {title} => {result}")
                    lost.append(full_text)

        top_results = won[:5] + lost[:5]
        app_logger.log_info(f"📊 Total displayed: {len(top_results)}")
        return top_results if top_results else ["No recent match results found."]

    except Exception as e:
        app_logger.log_error(f"❌ [ERROR] Failed recent match fetch: {e}")
        return ["Error loading past matches."]

# Streamlit UI
st.set_page_config(page_title="IPL Chatbot", layout="centered")
st.title("🏏 IPL Chatbot")

user_input = st.text_input("Ask about IPL scores:", placeholder="e.g. Show me Mumbai Indians score")

if user_input:
    app_logger.log_info(user_input)

    team = detect_team(user_input)

    scores = get_live_scores(team)
    if scores:
        st.subheader("🟢 Live Match(es):")
        for s in scores:
            st.markdown(s)
    else:
        st.warning("❌ No live match found. Showing recent results:")
        past = get_recent_results(team)
        for p in past:
            st.markdown(p)

with st.expander("💡 Try examples"):
    st.markdown("""
- Show Mumbai Indians score
- Delhi Capitals recent results
- CSK won?
- RCB vs MI today?
    """)