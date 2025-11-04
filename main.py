# main.py
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 1) 先載入環境變數（.env）
load_dotenv()

# 2) 讀取 LINE 金鑰（若缺少會立刻丟錯，好比對）
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise RuntimeError("請設定 .env 中的 LINE_CHANNEL_ACCESS_TOKEN / LINE_CHANNEL_SECRET")

# 3) 正確初始化（注意：這兩行 *一定* 要在 @handler.add 之前）
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 4) FastAPI App
app = FastAPI()

# 5) Webhook 入口（LINE 會打這個）
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

# 6) 訊息處理（避免函式名叫 handler 以免覆蓋）
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event: MessageEvent):
    user_text = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你說：{user_text}")
    )
