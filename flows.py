"""
Conversation flow management for multi-step interactions.
SessionStore keeps per-user state in memory.
"""

from datetime import datetime


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


STEPS = ["name", "date", "time", "guests", "confirm"]

PROMPTS = {
    "name":    "請問預約的姓名？",
    "date":    "請問預約日期？（例如：5/20、明天）",
    "time":    "請問用餐時間？（例如：18:30）",
    "guests":  "請問幾位用餐？",
    "confirm": None,  # 動態產生
}


def text(msg: str) -> dict:
    return {"type": "text", "text": msg}


def handle_reservation_flow(
    session: dict,
    user_text: str,
    user_id: str,
    store: SessionStore,
) -> list[dict]:
    step = session.get("step", "name")

    # 收集當前步驟的回答
    if step == "name":
        store.update(user_id, {"name": user_text, "step": "date"})
        return [text(PROMPTS["date"])]

    elif step == "date":
        store.update(user_id, {"date": user_text, "step": "time"})
        return [text(PROMPTS["time"])]

    elif step == "time":
        store.update(user_id, {"time": user_text, "step": "guests"})
        return [text(PROMPTS["guests"])]

    elif step == "guests":
        store.update(user_id, {"guests": user_text, "step": "confirm"})
        session = store.get(user_id)
        summary = (
            f"請確認您的預約資訊：\n\n"
            f"👤 姓名：{session['name']}\n"
            f"📅 日期：{session['date']}\n"
            f"🕐 時間：{session['time']}\n"
            f"👥 人數：{session['guests']} 位\n\n"
            f"確認請回覆「確認」，重新填寫請回覆「取消」"
        )
        return [text(summary)]

    elif step == "confirm":
        if "確認" in user_text or "yes" in user_text.lower() or "ok" in user_text.lower():
            session = store.get(user_id)
            record = {
                "name":   session.get("name"),
                "date":   session.get("date"),
                "time":   session.get("time"),
                "guests": session.get("guests"),
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
    """Save reservation to local CSV log."""
    import csv
    import os
    log_path = "reservations.csv"
    file_exists = os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)
