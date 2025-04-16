import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import pandas as pd

# -------------------- CONFIG --------------------
st.set_page_config(page_title="IPL Score Stream", layout="centered")

# -------------------- CONSTANTS --------------------
BASE_URL = "https://www.cricbuzz.com"
current_year = datetime.now().year

IPL_TEAMS_MAP = {
    "CSK": "Chennai Super Kings", "DC": "Delhi Capitals", "GT": "Gujarat Titans",
    "KKR": "Kolkata Knight Riders", "LSG": "Lucknow Super Giants", "MI": "Mumbai Indians",
    "PBKS": "Punjab Kings", "RR": "Rajasthan Royals", "RCB": "Royal Challengers Bangalore",
    "SRH": "Sunrisers Hyderabad"
}
IPL_TEAMS = set(IPL_TEAMS_MAP.keys()) | set(IPL_TEAMS_MAP.values())

# -------------------- LIVE MATCHES --------------------
def fetch_live_ipl_matches():
    url = f"{BASE_URL}/cricket-match/live-scores"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    pattern = re.compile(fr"/live-cricket-scores/.+-match-indian-premier-league-{current_year}")
    matches = [a['href'] for a in soup.find_all('a', href=True) if pattern.search(a['href'])]
    pattern_4_score = re.compile(r'(\d+)(?:th|st|nd|rd)-match')

    final_matches = sorted(
        [(link, int(pattern_4_score.search(link).group(1))) for link in matches if pattern_4_score.search(link)],
        key=lambda x: x[1],
        reverse=True
    )

    results = []
    seen = set()

    for match_url, _ in final_matches[:2]:
        response = requests.get(BASE_URL + match_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        score_blocks = soup.select("div.cb-col.cb-col-100.cb-min-tm")
        team1_score = score_blocks[0].text.strip() if len(score_blocks) > 0 else "N/A"
        team2_score = score_blocks[1].text.strip() if len(score_blocks) > 1 else "N/A"

        result_block = soup.select_one("div.cb-min-stts")
        result = result_block.text.strip() if result_block else "Result unavailable"

        mom_block = soup.select_one("div.cb-mom-itm a.cb-link-undrln")
        mom = mom_block.text.strip() if mom_block else "Unknown"

        commentary_blocks = soup.find_all("p", class_="cb-com-ln", limit=3)
        commentary = " ".join(c.get_text(strip=True) for c in commentary_blocks)

        match_id = f"{team1_score}|{team2_score}|{result}"
        if match_id in seen:
            continue
        seen.add(match_id)

        results.append({
            "1st Team Score": team1_score,
            "2nd Team Score": team2_score,
            "Result": result,
            "Player of the Match": mom,
            "Latest Commentary": commentary[:100]
        })

    # Check if any commentary mentions "needs X runs" (indicates it's still live)
    live_matches = [
        r for r in results
        if re.search(r"needs\s+\d+\s+runs", r["Latest Commentary"].lower())
    ]
    return live_matches, results

# -------------------- RECENT MATCHES --------------------
def get_recent_results():
    url = f"{BASE_URL}/cricket-series/9237/Indian-Premier-League-{current_year}/matches"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    all_tags = soup.find_all("a", href=True)
    results, seen = [], set()

    for i in range(len(all_tags) - 1):
        tag, next_tag = all_tags[i], all_tags[i + 1]
        href = tag['href']
        title = tag.get_text().strip()
        result = next_tag.get_text().strip()

        if "cricket-scores" not in href:
            continue

        if not any(team.lower() in title.lower() for team in IPL_TEAMS):
            continue

        match_id = f"{title}-{result}"
        if match_id in seen:
            continue
        seen.add(match_id)

        results.append(f"{title} – {result}")

    return results[:20]

# -------------------- UI --------------------
st.title("🏏 IPL Score Stream")
st.markdown("---")

# LIVE
live_matches, last_two_matches = fetch_live_ipl_matches()
if live_matches:
    st.subheader("🟢 Live Match Score")
    df = pd.DataFrame(live_matches)
    df.index += 1
    st.table(df)
else:
    st.warning("❌ No live IPL matches currently.")

st.markdown("---")

# LAST 2 MATCHES
if last_two_matches:
    st.subheader("📊 Past 2 Matches")
    df2 = pd.DataFrame(last_two_matches)
    df2.index += 1
    st.table(df2)

st.markdown("---")

# WON MATCHES
recent_results = get_recent_results()
won_matches = [r for r in recent_results if "won by" in r.lower()]
if won_matches:
    st.subheader("✅ Won Matches")
    for win in won_matches:
        st.markdown(f"- {win}")
    st.markdown("---")

# ALL RESULTS
if recent_results:
    st.subheader("📋 All Recent IPL Results")
    for res in recent_results:
        st.markdown(f"- {res}")
else:
    st.warning("❌ No recent results found.")
