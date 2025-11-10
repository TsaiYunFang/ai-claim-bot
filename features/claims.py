from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from . import STORE, new_id

router = APIRouter()

class ClaimStart(BaseModel):
    policy_id: str = Field(..., description="上傳完成後取得的 upload_id")
    name: str
    incident_date: date
    summary: str

@router.post("/start")
def start_claim(body: ClaimStart):
    # 確認對應的保單已存在（有先上傳）
    if body.policy_id not in STORE["uploads"]:
        raise HTTPException(status_code=404, detail="policy_id 不存在，請先上傳保單")

    # 生成理賠單號
    claim_id = new_id("clm")

    # 建立理賠紀錄（Demo 先放在記憶體）
    STORE["claims"][claim_id] = {
        "policy_id": body.policy_id,
        "name": body.name,
        "incident_date": str(body.incident_date),
        "summary": body.summary,
        "status": "RECEIVED",  # 初始狀態
        "next_steps": ["資料檢核", "理賠初審", "複核/補件", "核賠", "撥款"],
    }

    return {
        "claim_id": claim_id,
        "status": "RECEIVED",
        "next_steps": STORE["claims"][claim_id]["next_steps"],
    }
