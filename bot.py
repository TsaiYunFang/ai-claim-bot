# bot.py
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

# 讀取 .env（需要 LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN）
load_dotenv()
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not CHANNEL_SECRET or not CHANNEL_ACCESS_TOKEN:
    print("[WARN] LINE 環境變數未設定完整，請確認 .env")

# 初始化 LINE SDK（需為真實金鑰）
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

# ✅ 提供給 main.py 掛載的 router
router = APIRouter()

@router.get("/ping")
def ping():
    return {"ok": True, "service": "line-webhook"}

@router.post("/webhook")
async def line_webhook(request: Request):
    if handler is None:
        raise HTTPException(status_code=500, detail="LINE 金鑰未設定")

    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

# ====== 訊息處理 ======
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event: MessageEvent):
    text = (event.message.text or "").strip()

    if text in ["menu", "Menu", "菜單", "help", "HELP"]:
        from content import MENU_TEXT
        reply = "\n".join(MENU_TEXT)
    elif text in ["客服", "support", "Support"]:
        from content import SUPPORT_INFO
        info = SUPPORT_INFO
        reply = f"服務時間：{info['service_hours']}\n電話：{info['hotline']}\nEmail：{info['email']}"
    else:
        reply = "嗨，我是 AI 理賠小幫手 🤖\n輸入「菜單」看看可以做什麼，或到 /docs 測試 API。"

    if line_bot_api:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
