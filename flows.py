"""
Conversation flow management for multi-step interactions.
SessionStore keeps per-user state in memory.
"""

import re
from datetime import datetime

CANCEL_KEYWORDS = ["取消", "cancel", "不要了", "算了", "離開", "結束"]
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


class SessionStore:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def get(self, user_id: str) -> dict:
        return self._store.get(user_id, {})

    def set(self, user_id: str, data: dict):
        self._store[user_id] = data

    def update(self, user_id: str, data: dict):
        session = self.get(user_id)
        session.update(data)
        self._store[user_id] = session

    def clear(self, user_id: str):
        self._store.pop(user_id, None)


PROMPTS = {
    "name":    "請問預約的姓名？",
    "date":    "請問預約日期？（例如：5/20、明天）",
    "time":    "請問用餐時間？（例如：18:30）",
    "guests":  "請問幾位用餐？（例如：2、4）",
}


def text(msg: str) -> dict:
    return {"type": "text", "text": msg}


def _is_cancel(user_text: str) -> bool:
    t = user_text.strip().lower()
    return any(k in t for k in CANCEL_KEYWORDS)


def handle_reservation_flow(
    session: dict,
    user_text: str,
    user_id: str,
    store: SessionStore,
) -> list[dict]:
    # 任何步驟都可以取消
    if _is_cancel(user_text):
        store.clear(user_id)
        return [text("好的，已取消預約。如需重新預約請輸入「預約」😊")]

    step = session.get("step", "name")

    if step == "name":
        store.update(user_id, {"name": user_text, "step": "date"})
        return [text(PROMPTS["date"])]

    elif step == "date":
        store.update(user_id, {"date": user_text, "step": "time"})
        return [text(PROMPTS["time"])]

    elif step == "time":
        if not TIME_RE.match(user_text.strip()):
            return [text("請用 HH:MM 格式輸入時間，例如：18:30")]
        store.update(user_id, {"time": user_text.strip(), "step": "guests"})
        return [text(PROMPTS["guests"])]

    elif step == "guests":
        if not user_text.strip().isdigit() or not (1 <= int(user_text.strip()) <= 20):
            return [text("請輸入 1–20 的數字，例如：4")]
        store.update(user_id, {"guests": user_text.strip(), "step": "confirm"})
        session = store.get(user_id)
        summary = (
            f"請確認您的預約資訊：\n\n"
            f"👤 姓名：{session['name']}\n"
            f"📅 日期：{session['date']}\n"
            f"🕐 時間：{session['time']}\n"
            f"👥 人數：{session['guests']} 位\n\n"
            f"確認請回覆「確認」，取消請回覆「取消」"
        )
        return [text(summary)]

    elif step == "confirm":
        if "確認" in user_text or "yes" in user_text.lower() or "ok" in user_text.lower():
            session = store.get(user_id)
            record = {
                "name":       session.get("name"),
                "date":       session.get("date"),
                "time":       session.get("time"),
                "guests":     session.get("guests"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            _save_reservation(record)
            store.clear(user_id)
            return [text(
                f"✅ 預約成功！\n\n"
                f"我們已記錄您的預約：\n"
                f"📅 {record['date']} {record['time']}\n"
                f"👤 {record['name']} 共 {record['guests']} 位\n\n"
                f"期待您的光臨！如需更改請致電 02-1234-5678 😊"
            )]
        else:
            store.clear(user_id)
            return [text("好的，已取消此次預約。如需重新預約請輸入「預約」。")]

    store.clear(user_id)
    return [text("抱歉，發生錯誤，請重新輸入「預約」開始。")]


def _save_reservation(record: dict):
    import csv
    import os
    log_path = "reservations.csv"
    file_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)
