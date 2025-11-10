from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from . import STORE

router = APIRouter()

# ✅ 使用者：查詢理賠進度
@router.get("/{claim_id}")
def get_progress(claim_id: str):
    claim = STORE["claims"].get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="claim_id 不存在")
    return {
        "claim_id": claim_id,
        "status": claim["status"],
        "next_steps": claim["next_steps"]
    }

# ✅ 開發者測試用：更新理賠狀態
class UpdateBody(BaseModel):
    status: Literal["RECEIVED", "CHECKING", "REVIEW", "NEED_MORE_INFO", "APPROVED", "REJECTED"]

@router.patch("/{claim_id}")
def update_progress(claim_id: str, body: UpdateBody):
    claim = STORE["claims"].get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="claim_id 不存在")

    claim["status"] = body.status

    return {
        "claim_id": claim_id,
        "status": claim["status"]
    }
