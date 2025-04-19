import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Dynamically get the current year
CURRENT_YEAR = datetime.now().year

# Define the unique code for the year (e.g., 2025 -> 9237)
YEAR_CODE_MAPPING = {
    2025: "9237",
}

# Get the unique code for the current year
YEAR_CODE = YEAR_CODE_MAPPING.get(CURRENT_YEAR, "default_code")

# Construct URLs
BASE_URL = "https://www.cricbuzz.com"
IPL_SERIES_URL = f"{BASE_URL}/cricket-series/{YEAR_CODE}/indian-premier-league-{CURRENT_YEAR}"
IPL_MATCHES_URL = f"{IPL_SERIES_URL}/matches"
LIVE_KEYWORDS = ["won the toss", "opt", "elect", "need", "needs", "chose to", "innings", "innings Break"]


st.markdown("""
    <style>
        .main > div { max-width: 100%; padding-left: 1rem; padding-right: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <h1 style='text-align: center;'>🏏 IPL Score Stream</h1>
    <p style='text-align: center; font-size: 16px; color: gray;'>
        ⏱️ Last updated: {datetime.now().strftime('%H:%M:%S')}
    </p>
""", unsafe_allow_html=True)

st_autorefresh(interval=5000, limit=None, key="ipl_autorefresh")

def fetch_live_ipl_matches():
    url = f"{BASE_URL}/cricket-match/live-scores"
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    live_matches = []
    sections = soup.find_all("div", class_="cb-col cb-col-100 cb-plyr-tbody cb-rank-hdr cb-lv-main")
    for section in sections:
        header = section.find("h2", class_="cb-lv-grn-strip")
        if not header or not header.find("span", class_="cb-plus-ico cb-ico-live-stream"):
            continue

        match_blocks = section.find_all("div", class_="cb-mtch-lst")
        for block in match_blocks:
            title_tag = block.find("h3", class_="cb-lv-scr-mtch-hdr")
            match_title = title_tag.get_text(strip=True).rstrip(',') if title_tag else "N/A"

            team1 = block.find("div", class_="cb-hmscg-bwl-txt")
            score1 = team1.find_all("div", class_="cb-ovr-flo")[1].text.strip() if team1 else "N/A"

            team2 = block.find("div", class_="cb-hmscg-bat-txt")
            score2 = team2.find_all("div", class_="cb-ovr-flo")[1].text.strip() if team2 else "N/A"

            status_tag = block.find("div", class_="cb-text-live")
            status = status_tag.text.strip() if status_tag else ""

            if any(k in status.lower() for k in LIVE_KEYWORDS):
                live_matches.append({
                    "Match Title": match_title,
                    "Batting Score": score2,
                    "Bowling Score": score1,
                    "Status": status
                })
    return live_matches

def get_recent_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(IPL_SERIES_URL, headers=headers).text, "html.parser")
    tags = soup.find_all("a", class_="cb-nws-hdln-ancr")
    return [(tag.text.strip(), BASE_URL + tag["href"]) for tag in tags[:10]]

def get_recent_match_results():
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(IPL_MATCHES_URL, headers=headers).text, "html.parser")
    result_blocks = soup.find_all("a", href=True)

    results = []
    for tag in result_blocks:
        if "won by" in tag.text.lower():
            desc = tag.text.strip()
            link = BASE_URL + tag["href"]
            parent = tag.find_parent("div", class_="cb-col-100 cb-col")
            date_tag = parent.find("div", class_="schedule-date") if parent else None
            date = date_tag.text.strip() if date_tag else "—"
            results.append((date, desc, link))

    return results[-5:][::-1] if results else []

def get_upcoming_matches():
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(IPL_MATCHES_URL, headers=headers).text, "html.parser")
    matches = []

    for block in soup.select("div.cb-series-matches"):
        title_tag = block.select_one("a.text-hvr-underline")
        venue_tag = block.select_one("div.text-gray")
        time_tag = block.select_one("a.cb-text-upcoming")

        if title_tag and venue_tag and time_tag:
            title = title_tag.text.strip()
            venue = venue_tag.text.strip()
            start = time_tag.text.strip()
            link = BASE_URL + title_tag["href"]
            matches.append(f"- [{title} at {venue}]({link})")

    return matches[:5]

def left_panel():
    st.subheader("🟢 Live Matches")
    matches = fetch_live_ipl_matches()
    if matches:
        for match in matches:
            st.markdown(f"#### 🔥 {match['Match Title']}")
            st.markdown(f"🏏 **Batting Side**: {match['Batting Score']}")
            st.markdown(f"🎯 **Bowling Side**: {match['Bowling Score']}")
            st.markdown(f"📣 **Status**: {match['Status']}")
            st.markdown("---")
    else:
        st.warning("❌ No live IPL matches currently.")
        st.markdown("---")

    st.subheader("📰 Latest IPL News")
    for title, link in get_recent_news():
        st.markdown(f"- [{title}]({link})")

def right_panel():
    st.subheader("📅 Recent Match Results")
    for _, desc, link in get_recent_match_results():
        st.markdown(f"- [{desc}]({link})")

    st.divider()
    st.subheader("🗓️ Upcoming Matches")
    for line in get_upcoming_matches():
        st.markdown(line)

left_col, right_col = st.columns([5, 5])
with left_col: left_panel()
with right_col: right_panel()
