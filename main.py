from fastapi import FastAPI
from content import MENU_TEXT

# Import 功能模組
from features.uploads import router as uploads_router
from features.claims import router as claims_router
from features.progress import router as progress_router
from features.support import router as support_router

# Import LINE Webhook 模組
from bot import router as line_router

app = FastAPI(title="AI Claim Assistant", version="1.0.0")


# ----------------------------------------------------
# Default 頁面
# ----------------------------------------------------
@app.get("/")
def root():
    return {"message": "Hello! Welcome to AI Claim Assistant."}

@app.get("/menu")
def menu():
    return {"menu": MENU_TEXT}

@app.get("/health")
def health():
    return {"status": "ok"}


# ----------------------------------------------------
# 子路由掛載
# ----------------------------------------------------
app.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
app.include_router(claims_router, prefix="/claims", tags=["claims"])
app.include_router(progress_router, prefix="/progress", tags=["progress"])
app.include_router(support_router, prefix="/support", tags=["support"])

# ✅ LINE webhook 入口（這是新增的）
app.include_router(line_router, prefix="/line", tags=["line"])
