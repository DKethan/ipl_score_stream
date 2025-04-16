import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# Set page config FIRST
st.set_page_config(page_title="🏏 IPL Score Stream", layout="centered")

# Base settings
BASE_URL = "https://www.cricbuzz.com"
current_year = datetime.now().year

# -------------------- LIVE MATCHES --------------------
@st.cache_data(ttl=60)
def fetch_live_ipl_matches():
    url = f"{BASE_URL}/cricket-match/live-scores"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    matches = []
    sections = soup.find_all("div", class_="cb-col cb-col-100 cb-plyr-tbody cb-rank-hdr cb-lv-main")

    for section in sections:
        header = section.find("h2", class_="cb-lv-grn-strip")
        if not header or not header.find("span", class_="cb-plus-ico cb-ico-live-stream"):
            continue

        blocks = section.find_all("div", class_="cb-mtch-lst")
        for block in blocks:
            title = block.find("h3", class_="cb-lv-scr-mtch-hdr")
            title_text = title.get_text(strip=True).rstrip(',') if title else "N/A"

            # Team 1 score
            team1 = block.find("div", class_="cb-hmscg-bwl-txt")
            team1_score = team1.find_all("div", class_="cb-ovr-flo")[1].text.strip() if team1 and len(team1.find_all("div", class_="cb-ovr-flo")) > 1 else "N/A"

            # Team 2 score
            team2 = block.find("div", class_="cb-hmscg-bat-txt")
            team2_score = team2.find_all("div", class_="cb-ovr-flo")[1].text.strip() if team2 and len(team2.find_all("div", class_="cb-ovr-flo")) > 1 else "N/A"

            # Commentary
            status = block.find("div", class_="cb-text-live")
            status_text = status.text.strip() if status else "Live match ongoing"

            # Check if match is truly live (commentary says "needs X runs")
            if "need" not in status_text.lower():
                continue  # Not live

            matches.append({
                "Match Title": title_text,
                "Batting Side Score": team2_score,
                "Bowling Side Score": team1_score,
                "Status": status_text
            })

    return matches

# -------------------- RECENT RESULTS --------------------
@st.cache_data(ttl=600)
def get_recent_results():
    try:
        url = f"{BASE_URL}/cricket-series/9237/Indian-Premier-League-{current_year}/matches"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        all_tags = soup.find_all("a", href=True)

        results, seen = [], set()
        for i in range(len(all_tags) - 1):
            tag, next_tag = all_tags[i], all_tags[i + 1]
            href, title, result = tag['href'], tag.get_text(strip=True), next_tag.get_text(strip=True)

            if "cricket-scores" in href:
                match_id = f"{title}-{result}"
                if match_id not in seen:
                    seen.add(match_id)
                    results.append(f"{title} – {result}")

        return results[:10]
    except Exception:
        return ["Error loading past matches."]

# -------------------- UI START --------------------
st.title("🏏 IPL Score Stream")
st.markdown("—")

# 🔴 Live Section
st.subheader("🟢 Live Matches")
live_scores = fetch_live_ipl_matches()

if live_scores:
    for match in live_scores:
        st.markdown(f"#### 🔥 {match['Match Title']}")
        st.markdown(f"✍️ **Batting Side Score**: {match['Batting Side Score']}")
        st.markdown(f"🧤 **Bowling Side Score**: {match['Bowling Side Score']}")
        st.markdown(f"📣 **Status**: {match['Status']}")
        st.markdown("---")
else:
    st.warning("✅ No live IPL matches right now. All matches have ended or haven't started.")

# 📊 Last 2 Match Summary
if live_scores:
    st.subheader("🧾 Last 2 Matches Summary")
    df = pd.DataFrame(live_scores[:2])
    df.index += 1
    st.table(df)
    st.markdown("---")

# 📋 Results
recent_results = get_recent_results()
if recent_results:
    won_matches = [r for r in recent_results if "won" in r.lower()]
    st.subheader("✅ Won Matches")
    for result in won_matches:
        st.markdown(f"- {result}")
    st.markdown("---")

    st.subheader("📋 All Recent Results")
    for result in recent_results:
        st.markdown(f"- {result}")
else:
    st.warning("❌ No recent results found.")
