# VolPulse on your iPhone — setup guide

Two things, both free:

- **The app on your home screen** — the VolPulse dashboard, installed via Safari.
- **Push notifications** — a bot that runs on GitHub's servers every ~10 minutes and
  sends you a Telegram notification the moment a coin crosses your criteria
  (market cap ≥ $100M, 24h volume ≥ 20% of market cap), even when your phone is locked.

Total setup time: about 15 minutes. You need a free GitHub account and Telegram installed
on your iPhone.

---

## Part 1 — Create your Telegram alert bot (5 min, on your phone)

1. Open Telegram and search for **@BotFather** (the official bot with a blue check).
2. Send it: `/newbot` — give your bot a name (e.g. `VolPulse Alerts`) and a username
   ending in `bot` (e.g. `myvolpulse_bot`).
3. BotFather replies with an **HTTP API token** like `7123456789:AAH...`. Copy it —
   this is your `TELEGRAM_TOKEN`.
4. Open a chat with your new bot and press **Start** (this is required — bots can't
   message you first).
5. Now get your chat ID: search for **@userinfobot**, press Start, and it replies with
   your numeric **Id**. That's your `TELEGRAM_CHAT_ID`.

## Part 2 — Put the kit on GitHub (5 min)

1. Sign in at github.com → **New repository** → name it `volpulse` → **Public** → Create.
   (Public is required for free GitHub Pages; the code contains no secrets.)
2. On the repo page: **Add file → Upload files** → drag in everything from this kit:
   `index.html`, `manifest.webmanifest`, `icon-180.png`, `icon-512.png`, `monitor.py`,
   and the `.github` folder (if drag-and-drop won't take the folder, create the file
   manually: **Add file → Create new file**, type `.github/workflows/scan.yml` as the
   name, and paste in the contents of that file). Commit.
3. Add your Telegram secrets: **Settings → Secrets and variables → Actions →
   New repository secret**. Create two:
   - `TELEGRAM_TOKEN` = the token from BotFather
   - `TELEGRAM_CHAT_ID` = your numeric ID
4. Turn on the scanner: **Actions** tab → enable workflows if prompted →
   click **VolPulse scan** → **Run workflow**. Within a minute your bot should message
   you: "VolPulse is live." From now on it runs itself every ~10 minutes.

## Part 3 — Install the app on your home screen (2 min)

1. In the repo: **Settings → Pages → Source: Deploy from a branch → Branch: main /(root)
   → Save**. After a minute your app is live at
   `https://YOURUSERNAME.github.io/volpulse/`.
2. Open that link in **Safari** on your iPhone.
3. Tap the **Share** button → **Add to Home Screen** → Add.

VolPulse now opens full-screen from its own icon. The dashboard alerts (sound + list)
work while it's open; the Telegram bot covers you the rest of the time.

---

## Tweaking

- **Change the criteria for push alerts**: edit `MIN_MCAP` and `MIN_RATIO` at the top
  of `monitor.py` (right in GitHub — pencil icon).
- **Change how often it checks**: edit the cron line in `.github/workflows/scan.yml`.
  `*/5 * * * *` = every 5 min (GitHub's minimum; real-world timing can lag a few minutes).
- **Dashboard criteria**: adjustable inside the app itself.

## Good to know

- Everything here is free: GitHub Actions (public repos), GitHub Pages, Telegram, and
  CoinGecko's public API.
- GitHub's scheduler is not to-the-second precise — expect alerts within roughly
  5–15 minutes of a coin crossing the line.
- A high volume/market-cap ratio flags unusual activity. It can mean genuine momentum,
  but also wash trading or a sell-off — always check the news before trading on an alert.
