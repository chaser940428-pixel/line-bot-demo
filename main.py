"""
LINE Bot - 餐飲/服務業自動化 Demo
Webhook server built with FastAPI + LINE Messaging API + Groq LLM
"""

import os
import hashlib
import hmac
import base64

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv

from intent import detect_intent, answer_faq
from flows import SessionStore, handle_reservation_flow

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

app = FastAPI()
store = SessionStore()


def verify_signature(body: bytes, signature: str) -> bool:
    mac = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    )
    expected = base64.b64encode(mac.digest()).decode("utf-8")
    return hmac.compare_digest(expected, signature)


async def reply(reply_token: str, messages: list[dict]):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"replyToken": reply_token, "messages": messages}
    async with httpx.AsyncClient() as client:
        await client.post(LINE_REPLY_URL, json=payload, headers=headers)


def text(msg: str) -> dict:
    return {"type": "text", "text": msg}


@app.get("/")
async def health():
    return {"status": "ok", "service": "LINE Bot Demo"}


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()

    for event in data.get("events", []):
        if event.get("type") != "message":
            continue
        if event["message"].get("type") != "text":
            continue

        user_id = event["source"]["userId"]
        user_text = event["message"]["text"].strip()
        reply_token = event["replyToken"]
        session = store.get(user_id)

        # 如果用戶在預約流程中
        if session.get("flow") == "reservation":
            messages = handle_reservation_flow(session, user_text, user_id, store)
            await reply(reply_token, messages)
            continue

        # 判斷意圖
        intent = detect_intent(user_text)

        if intent == "reservation":
            store.set(user_id, {"flow": "reservation", "step": "name"})
            await reply(reply_token, [text(
                "您好！歡迎預約 🍽️\n\n請問您的大名是？"
            )])

        elif intent == "faq":
            answer = answer_faq(user_text)
            await reply(reply_token, [text(answer)])

        elif intent == "cancel":
            store.clear(user_id)
            await reply(reply_token, [text(
                "好的，已為您取消操作。\n如需其他協助請隨時告訴我 😊"
            )])

        else:
            await reply(reply_token, [text(
                "您好！我可以幫您：\n\n"
                "📅 【預約】輸入「預約」或「訂位」\n"
                "❓ 【查詢】輸入您的問題\n"
                "❌ 【取消】輸入「取消」\n\n"
                "請問需要什麼協助呢？"
            )])

    return JSONResponse(content={"status": "ok"})
