# main.py
import os
import traceback
from typing import Dict, Set

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
)

# -----------------------------
# 基本設定
# -----------------------------
load_dotenv()  # 讀取 .env

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    # 沒設定金鑰時，直接丟錯，避免 NoneType 物件造成 handler.add 出錯
    raise RuntimeError(
        "LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET 未設定。"
        "請確認 .env 與 Render 環境變數。"
    )

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

app = FastAPI(title="AI Claim Bot", version="0.1.0")


# -----------------------------
# 健康檢查 / 根路由
# -----------------------------
@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)

@app.get("/")
async def index():
    return JSONResponse(
        content={
            "service": "AI Claim Bot",
            "message": "Hello! Service is running.",
            "docs": "/openapi.json",
        },
        status_code=200,
    )


# -----------------------------
# 關鍵字與文案（可集中維護）
# -----------------------------
def normalize(s: str) -> str:
    return (s or "").strip().lower().replace("　", "").replace(" ", "")

# 同義詞/別名
ALIASES: Dict[str, Set[str]] = {
    "menu": {"menu", "help", "選單", "主選單"},
    "理賠": {"理賠", "理賠流程", "申請理賠", "賠償"},
    "上傳": {"上傳", "傳檔", "文件上傳", "傳照片"},
    "進度": {"進度", "查進度", "查件", "進度查詢"},
    "客服": {"客服", "聯絡", "電話", "email", "服務人員"},
    "qa": {"qa", "常見問題", "faq", "問題"},
}

REPLIES: Dict[str, str] = {
    "menu": (
        "📋 功能選單：\n"
        "1) 理賠  2) 上傳  3) 進度  4) 客服  5) QA\n"
        "（可直接按下方按鈕，或輸入關鍵字）"
    ),
    "理賠": (
        "🧾 理賠流程（3 步）：\n"
        "① 準備：保單號/被保人/事故日期地點說明\n"
        "② 憑證：收據/診斷書/航班延誤證明（清晰四角入鏡）\n"
        "③ 送件：輸入「上傳」查看檔案規格與命名建議"
    ),
    "上傳": (
        "📤 上傳規格：\n"
        "• 檔案：JPG/PNG/PDF（≤ 10MB）\n"
        "• 命名：保單號_文件類型_頁碼（例：A123456_發票_1）\n"
        "• 影像：四角入鏡、避免反光與模糊\n"
        "• 補件：7 日內補齊，逾期可能需重啟流程"
    ),
    "進度": (
        "⏳ 查進度：\n"
        "請輸入「進度 查 A123456」（A123456 為保單號）。\n"
        "狀態包含：審核中/待補件/核定/匯款中/結案。"
    ),
    "客服": (
        "👩‍💼 客服資訊：\n"
        "專線：0800-000-000（平日 09:00–18:00）\n"
        "Email：service@example.com（附保單號）"
    ),
    "qa": (
        "❓ 常見問題：\n"
        "• 退件常因影像反光/缺角/金額模糊\n"
        "• 航班延誤需附官方證明或正規截圖\n"
        "• 海外醫療需附英文/當地語言單據"
    ),
}

def quick_menu_message(text: str = None) -> TextSendMessage:
    """Quick Reply 主選單"""
    return TextSendMessage(
        text=text or REPLIES["menu"],
        quick_reply=QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="理賠流程", text="理賠")),
            QuickReplyButton(action=MessageAction(label="上傳規格", text="上傳")),
            QuickReplyButton(action=MessageAction(label="進度查詢", text="進度")),
            QuickReplyButton(action=MessageAction(label="客服資訊", text="客服")),
            QuickReplyButton(action=MessageAction(label="常見問題", text="QA")),
        ])
    )

def resolve_intent(raw_text: str) -> str | None:
    """規範化 + 同義詞比對"""
    t = normalize(raw_text)
    for intent, words in ALIASES.items():
        if t in words:
            return intent
    return None


# -----------------------------
# LINE Webhook
# -----------------------------
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("x-line-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature")

    body = await request.body()
    body_str = body.decode("utf-8")
    # 可觀測性
    print(f"[CALLBACK] raw body: {body_str[:200]}...")

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        # 簽章錯誤（通常是 secret/token 設錯）
        print("[ERROR] Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    return PlainTextResponse("OK")


# -----------------------------
# 文字訊息處理
# -----------------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event: MessageEvent):
    try:
        raw = event.message.text or ""
        intent = resolve_intent(raw)
        print(f"[INTENT] '{raw}' -> {intent}")

        # 1) 明確意圖：回對應文案
        if intent in REPLIES:
            reply = REPLIES[intent]
            # menu/未知 → 帶 Quick Reply
            if intent == "menu":
                line_bot_api.reply_message(event.reply_token, quick_menu_message(reply))
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply, quick_reply=quick_menu_message().quick_reply)
                )
            print("[REPLY] OK")
            return

        # 2) 未命中：友善 fallback + Quick Reply
        fallback = (
            "🤖 我懂你的意思，但目前支援：理賠 / 上傳 / 進度 / 客服 / QA。\n"
            "可直接輸入關鍵字，或點選下方按鈕。"
        )
        line_bot_api.reply_message(event.reply_token, quick_menu_message(fallback))
        print("[FALLBACK] menu shown")

    except Exception as e:
        print(f"[ERROR] reply failed: {e}")
        traceback.print_exc()
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="系統忙線中，請稍後再試 🙏")
            )
        except Exception:
            pass
