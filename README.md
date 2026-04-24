# 🎯 Summer Opportunity Agent

Automatically finds and tracks **summer 2026 opportunities** (internships, summer schools, camps, fellowships) for students from Uzbekistan.

**What it does every day at 11:00 AM Uzbekistan time:**
- 🔍 Searches the web for new opportunities using OpenAI's AI + web search
- 📊 Saves everything to a Google Sheet you can view anytime
- 📱 Sends a Telegram notification with new finds
- ⏰ Alerts you when deadlines are approaching (within 14 days)

**Filters applied automatically:**
- ✅ Open to students from Uzbekistan / Central Asia
- ✅ Fully funded OR personal cost under $700
- ✅ Zero application fees — no exceptions
- ✅ Takes place Summer 2026 (June–August)

---

## 🛠 Setup (one-time, ~30 minutes)

### Step 1 — Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** (looks like `7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxx`)
4. Start a chat with your new bot (send it any message like `/start`)
5. Visit this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
6. Find `"chat":{"id":` in the response — copy that number. That's your **Chat ID**.

---

### Step 2 — Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a **new blank spreadsheet**
2. Name it anything (e.g., "Summer Opportunities 2026")
3. Copy the **Sheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit
   ```

---

### Step 3 — Create a Google Service Account

This lets the agent write to your sheet automatically.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable **Google Sheets API**:
   - Go to **APIs & Services → Library**
   - Search "Google Sheets API" → Enable it
   - Also enable **Google Drive API**
4. Create a service account:
   - Go to **APIs & Services → Credentials**
   - Click **Create Credentials → Service Account**
   - Give it any name (e.g., "opportunity-agent")
   - Skip roles for now → Done
5. Click on the new service account → **Keys** tab → **Add Key → JSON**
6. Download the JSON file — keep it safe!
7. **Share your Google Sheet** with the service account email (looks like `name@project.iam.gserviceaccount.com`) with **Editor** access

---

### Step 4 — Set Up GitHub Repository

1. Create a new **private** GitHub repository
2. Upload all project files to the repo (or clone and push)
3. Go to **Settings → Secrets and variables → Actions**
4. Add the following secrets (click "New repository secret" for each):

| Secret Name | Value |
|---|---|
| `GEMINI_API_KEY` | Your free Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID from Step 1 |
| `GOOGLE_SHEETS_ID` | The sheet ID from the URL in Step 2 |
| `GOOGLE_CREDENTIALS_JSON` | The **entire contents** of the JSON file from Step 3 |

> 💡 For `GOOGLE_CREDENTIALS_JSON`: open the downloaded JSON file in a text editor, select all, copy, and paste as the secret value.

---

### Step 5 — Test It Manually

1. Go to your repo on GitHub
2. Click **Actions** tab
3. Click **"🎯 Summer Opportunity Agent"** in the left sidebar
4. Click **"Run workflow"** → **"Run workflow"** (green button)
5. Watch it run — check your Telegram for notifications!

---

## 📅 Schedule

The agent runs automatically at **06:00 UTC = 11:00 AM Uzbekistan time (UTC+5)** every day.

To change the time, edit `.github/workflows/daily_search.yml`:
```yaml
- cron: "0 6 * * *"   # 06:00 UTC
```

Use [crontab.guru](https://crontab.guru) to calculate your preferred UTC time.

---

## 📊 Google Sheet Structure

The sheet is auto-created on first run with these columns:

| Column | Description |
|---|---|
| Name | Program name |
| Type | internship / summer school / summer camp / fellowship |
| Host Organization | University or org running the program |
| Country | Where the program takes place |
| Funding Status | Fully Funded / Partially Funded |
| Est. Cost (USD) | Your estimated personal cost |
| App Fee (USD) | Always $0 (filtered) |
| Deadline | Application deadline |
| Eligibility | Who can apply |
| Application Link | Direct link to apply |
| Description | What the program is about |
| Date Found | When the agent discovered it |
| Status | Active / Expired / Applied |
| Notes | Your personal notes |

---

## 📱 Telegram Notifications

You'll receive 3 types of messages:

**🆕 New Opportunities** — when new programs are found
```
🎯 New Opportunities Found!
📅 May 15, 2026 · 3 new programs
──────────────────────────────

🎓 Oxford Summer School on Global Affairs
   🌍 University of Oxford — United Kingdom
   💚 Fully Funded
   📅 Deadline: June 1, 2026
   🔗 Apply Here
```

**⏰ Deadline Reminders** — when deadlines are coming up
```
⏰ Deadline Reminders
📅 May 15, 2026 · 2 deadlines approaching

🔴 URGENT — 3 days left!
📌 DAAD Summer Research Program
   📅 Deadline: May 18, 2026
   🔗 Apply Now
```

**📊 Daily Summary** — always sent, even on quiet days
```
📊 Daily Agent Report
📅 Wednesday, May 15, 2026

🆕 3 new opportunities found
⏰ 2 deadlines approaching
📋 Total tracked: 47 opportunities

📊 Open Google Sheet →
```

---

## 💰 Cost Estimate

| Service | Cost |
|---|---|
| GitHub Actions | Free (2,000 min/month free tier) |
| Gemini 2.0 Flash API | **Free** (1,500 requests/day, no credit card needed) |
| Google Sheets API | Free |
| Telegram Bot | Free |

**Total: $0/month** 🎉

---

## 🔧 Customization

**Change deadline alert window** — in `agent.py`:
```python
DEADLINE_ALERT_DAYS = 14  # Change to 7, 21, etc.
```

**Add more search queries** — in `search_handler.py`:
```python
SEARCH_QUERIES = [
    ...
    "your custom search query here",
]
```

**Change cost limit** — in `search_handler.py`:
```python
if float(opp.get("estimated_cost_usd", 9999)) > 700:  # Change 700 to your limit
```

---

## 🐛 Troubleshooting

**Agent runs but finds nothing**
- This is normal — not every day has new results
- Check GitHub Actions logs for search output

**Telegram not receiving messages**
- Make sure you sent your bot a message first (`/start`)
- Verify `TELEGRAM_CHAT_ID` — use the getUpdates URL to confirm

**Google Sheets error**
- Confirm you shared the sheet with the service account email
- Verify `GOOGLE_CREDENTIALS_JSON` secret contains the full JSON content

**Gemini API error**
- Get your free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — no billing needed
- Free tier: 1,500 requests/day (the agent uses ~10 per run)
