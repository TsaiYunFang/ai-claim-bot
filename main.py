# main.py — minimal FastAPI + LINE Bot on Render
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 1) 讀環境變數（Render 會從「Environment Variables」提供）
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    # 在 Render logs 會清楚看到這個錯誤，方便排查
    raise RuntimeError("Missing LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET")

# 2) 先初始化（務必在裝飾器 @handler.add 之前）
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 3) 建立 FastAPI 應用（這個變數名必須是 app，給 gunicorn 找）
app = FastAPI()

# 4) 健康檢查（方便測試 Render 是否活著）
@app.get("/health")
def health():
    return {"ok": True}

# 5) LINE Webhook 入口
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_str = body.decode("utf-8")
    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature.")
    return PlainTextResponse("OK")

# 6) 訊息處理（echo）
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event: MessageEvent):
    user_text = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你說：{user_text}")
    )

# 不需要 if __name__ == "__main__"；Render 用 gunicorn 啟動 main:app
