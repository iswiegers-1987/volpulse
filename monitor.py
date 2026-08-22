"""
VolPulse watchdog — runs on a schedule, checks CoinGecko for coins where:
  * market cap >= MIN_MCAP
  * 24h volume >= MIN_RATIO of market cap
  * (optional) price within NEAR_ATH_PCT of its all-time high

Sends a Telegram push notification for every coin that NEWLY crosses
the threshold, and remembers previous qualifiers in state.json so you
don't get the same alert every 10 minutes.

Uses only the Python standard library — nothing to install.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

# ── your criteria ────────────────────────────────────────────────
MIN_MCAP = 100_000_000   # $100M minimum market cap
MIN_RATIO = 0.20         # 24h volume must be >= 20% of market cap

# Near-ATH filter: set to True to ONLY alert on coins trading within
# NEAR_ATH_PCT percent of their all-time high. Set to False to disable.
NEAR_ATH_FILTER = True
NEAR_ATH_PCT = 20        # e.g. 20 = price no more than 20% below its ATH

PAGES = 3                # scan top 750 coins by market cap
STATE_FILE = "state.json"

API = ("https://api.coingecko.com/api/v3/coins/markets"
       "?vs_currency=usd&order=market_cap_desc&per_page=250"
       "&price_change_percentage=24h&page={page}")


def http_get_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "volpulse/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(10 * (attempt + 1))  # back off, CoinGecko rate-limits


def fmt_usd(n):
    if n >= 1e9:
        return f"${n / 1e9:.2f}B"
    if n >= 1e6:
        return f"${n / 1e6:.1f}M"
    return f"${n:,.0f}"


def send_telegram(token, chat_ids, text):
    """Sends to one or more chat IDs (comma-separated), e.g. '123,456' or '-100987...'"""
    for chat_id in [c.strip() for c in chat_ids.split(",") if c.strip()]:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }).encode()
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=30) as r:
                json.load(r)
        except Exception as e:
            print(f"Failed to message {chat_id}: {e}")


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_ids = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_ids:
        sys.exit("Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables.")

    # previous qualifiers
    try:
        with open(STATE_FILE) as f:
            prev = set(json.load(f).get("qualifying", []))
        first_run = False
    except FileNotFoundError:
        prev = set()
        first_run = True

    # fetch market data
    coins = []
    for page in range(1, PAGES + 1):
        batch = http_get_json(API.format(page=page))
        coins.extend(batch)
        if len(batch) < 250:
            break
        time.sleep(2)  # be polite to the free API

    # apply criteria
    qualifiers = []
    for c in coins:
        mcap = c.get("market_cap") or 0
        vol = c.get("total_volume") or 0
        if mcap < MIN_MCAP or vol < MIN_RATIO * mcap:
            continue
        if NEAR_ATH_FILTER:
            ath_chg = c.get("ath_change_percentage")
            # ath_change_percentage is negative: -12.5 means 12.5% below ATH
            if ath_chg is None or ath_chg < -NEAR_ATH_PCT:
                continue
        qualifiers.append(c)

    current = {c["id"] for c in qualifiers}
    fresh = [c for c in qualifiers if c["id"] not in prev]

    ath_note = f" and within {NEAR_ATH_PCT}% of their all-time high" if NEAR_ATH_FILTER else ""

    if first_run:
        send_telegram(token, chat_ids,
                      f"✅ <b>VolPulse is live.</b> Scanned {len(coins)} coins; "
                      f"{len(qualifiers)} currently meet your criteria{ath_note}. "
                      f"You'll be pinged when a NEW coin crosses the line.")
    else:
        for c in fresh:
            ratio = c["total_volume"] / c["market_cap"] * 100
            chg = c.get("price_change_percentage_24h") or 0
            ath_chg = c.get("ath_change_percentage")
            ath_line = (f"\ndistance from ATH: <b>{abs(ath_chg):.1f}%</b>"
                        if ath_chg is not None else "")
            send_telegram(token, chat_ids,
                          f"🔔 <b>{c['symbol'].upper()}</b> ({c['name']}) crossed your threshold\n"
                          f"vol/mcap: <b>{ratio:.1f}%</b>\n"
                          f"market cap: {fmt_usd(c['market_cap'])}\n"
                          f"24h volume: {fmt_usd(c['total_volume'])}\n"
                          f"price: ${c['current_price']:,} ({chg:+.1f}% 24h)"
                          f"{ath_line}")
            time.sleep(1)

    # save state so repeats aren't re-alerted (coins that drop out can re-alert later)
    with open(STATE_FILE, "w") as f:
        json.dump({"qualifying": sorted(current)}, f, indent=1)

    print(f"Scanned {len(coins)} coins | {len(qualifiers)} qualifying | {len(fresh)} new alerts")


if __name__ == "__main__":
    main()
