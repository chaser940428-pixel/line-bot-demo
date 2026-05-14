"""
Intent detection and FAQ answering via Groq LLM.
"""

import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

RESERVATION_KEYWORDS = ["預約", "訂位", "reserve", "booking", "訂餐", "預訂"]
CANCEL_KEYWORDS = ["取消", "cancel", "不要了", "算了"]

FAQ_CONTEXT = """
你是一間台式餐廳「稻香園」的 AI 客服助理。以下是常見資訊：

營業時間：週一至週五 11:30–14:00、17:30–21:00；週末 11:00–21:00
地址：台北市大安區和平東路一段 100 號
電話：02-1234-5678
停車：附近有大安森林公園停車場，步行約 5 分鐘
訂位規則：4 人以下當天可直接來，5 人以上需事先預約
菜單：台式家常菜為主，招牌菜有控肉飯、三杯雞、蛤蠣湯
素食：有素食選項，請預約時告知
"""


def detect_intent(text: str) -> str:
    text_lower = text.lower()

    if any(k in text_lower for k in RESERVATION_KEYWORDS):
        return "reservation"
    if any(k in text_lower for k in CANCEL_KEYWORDS):
        return "cancel"

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    f"用戶訊息：「{text}」\n\n"
                    "判斷這則訊息的意圖，只回答一個詞：\n"
                    "- reservation（預約訂位相關）\n"
                    "- faq（詢問餐廳資訊、菜單、停車等）\n"
                    "- cancel（取消操作）\n"
                    "- other（其他）"
                ),
            }],
            max_tokens=10,
            temperature=0,
        )
        result = response.choices[0].message.content.strip().lower()
        for intent in ("reservation", "faq", "cancel"):
            if intent in result:
                return intent
        return "other"
    except Exception:
        return "other"


def answer_faq(question: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    f"{FAQ_CONTEXT}\n\n"
                    f"用戶問題：{question}\n\n"
                    "請用繁體中文簡短回答（2-3句），只根據以上資訊回答。"
                    "如果資訊裡沒有答案，請說「這個問題請致電 02-1234-5678 詢問」。"
                ),
            }],
            max_tokens=200,
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "抱歉，目前系統忙碌，請致電 02-1234-5678 詢問。"
