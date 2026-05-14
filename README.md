# LINE Bot Business Automation Demo

A production-ready LINE Bot showcasing AI-powered customer service automation for traditional businesses. Built to demonstrate how SMBs can replace manual message handling with intelligent automation.

**Live demo**: Scan the QR code on the [project page](https://github.com/chaser940428-pixel/line-bot-demo) to chat with the bot directly.

## What it does

This bot simulates a full-service front desk for a restaurant (稻香園), handling three common scenarios without any human intervention:

| Scenario | How it works |
|----------|-------------|
| **Table reservations** | Guides customers through a 5-step conversational flow (name → date → time → guests → confirm), then saves the record |
| **FAQ answering** | Answers questions about hours, location, parking, and menu using LLM-powered responses |
| **Intent fallback** | For unclear messages, provides a friendly menu of options |

## Architecture

```
LINE App → LINE Messaging API → Webhook (FastAPI)
                                     │
                          ┌──────────┴──────────┐
                          │   Intent Detection   │
                          │  (keyword + Groq LLM)│
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
             Reservation          FAQ Answer      Default
               Flow               (Groq LLM)     Message
           (SessionStore)
```

**Stack**: FastAPI · LINE Messaging API · Groq (llama-3.1-8b-instant) · Python 3.11 · Render

## Key design decisions

- **Keyword-first intent detection**: Common patterns (預約, 訂位, 取消) are matched instantly without an LLM call — reduces latency and API cost
- **In-memory SessionStore**: Per-user conversation state held in a plain dict; suitable for demo scale, swappable for Redis in production
- **Groq for ambiguous intents**: LLM is only invoked when keyword matching fails, keeping the happy path fast
- **Signature verification**: Every webhook request is verified against `LINE_CHANNEL_SECRET` via HMAC-SHA256 before processing

## Running locally

```bash
# 1. Clone and install
git clone https://github.com/chaser940428-pixel/line-bot-demo
cd line-bot-demo
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Fill in GROQ_API_KEY, LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN

# 3. Start the server
uvicorn main:app --reload --port 8000

# 4. Expose to the internet (for LINE webhook)
ngrok http 8000
# Set the ngrok URL as webhook in LINE Developers Console
```

## Conversation flow

```
User: 我想訂位
Bot:  您好！歡迎預約 🍽️  請問您的大名是？
User: 王小明
Bot:  請問預約日期？（例如：5/20、明天）
User: 明天
Bot:  請問用餐時間？（例如：18:30）
User: 19:00
Bot:  請問幾位用餐？
User: 4
Bot:  請確認您的預約資訊：
      👤 姓名：王小明
      📅 日期：明天
      🕐 時間：19:00
      👥 人數：4 位
      確認請回覆「確認」，重新填寫請回覆「取消」
User: 確認
Bot:  ✅ 預約成功！...
```

## Business impact

This pattern is directly applicable to:
- **餐廳 / 診所 / 美容院**: Replace WhatsApp/LINE manual booking with automated flow
- **房仲 / 補習班**: Qualify leads automatically before human follow-up
- **電商客服**: Handle common order-status and return-policy questions 24/7

A typical SMB spends 2–4 hours/day on repetitive message handling. This bot eliminates that entirely for the 80% of messages that follow predictable patterns.

## Environment variables

| Variable | Description |
|----------|-------------|
| `LINE_CHANNEL_SECRET` | From LINE Developers Console → Basic settings |
| `LINE_CHANNEL_ACCESS_TOKEN` | From LINE Developers Console → Messaging API |
| `GROQ_API_KEY` | From console.groq.com |
