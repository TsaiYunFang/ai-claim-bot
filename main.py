from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import os, traceback

load_dotenv()

app = FastAPI()

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# === Health check endpoints ===
@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok"}, status_code=200)

@app.head("/health")
async def health_check_head():
    # Render 與 UptimeRobot 常用 HEAD，直接回 200 即可
    return Response(status_code=200)

@app.get("/")
async def root():
    return JSONResponse({"message": "AI Claim Bot is running!"})

# === LINE Webhook ===
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("x-line-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return PlainTextResponse("OK")

# === Handle user messages ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    reply_text = f"你說：{user_text}"

    # Quick Reply 選單
    quick_reply = QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="理賠流程", text="理賠")),
        QuickReplyButton(action=MessageAction(label="上傳文件", text="上傳")),
        QuickReplyButton(action=MessageAction(label="進度查詢", text="進度")),
        QuickReplyButton(action=MessageAction(label="客服資訊", text="客服")),
    ])

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text, quick_reply=quick_reply)
    )
