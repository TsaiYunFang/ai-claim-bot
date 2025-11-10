from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from . import STORE, new_id

router = APIRouter()

@router.post("/policy")
async def upload_policy(policy: UploadFile = File(...)):
    """
    上傳保單檔案（任何副檔名皆可；Demo不做MIME驗證）
    會自動建立資料夾 data/uploads 並儲存檔案
    回傳 upload_id 供後續理賠流程使用
    """
    try:
        upload_id = new_id("upl")

        # 建立存檔資料夾
        save_dir = Path("data/uploads")
        save_dir.mkdir(parents=True, exist_ok=True)

        # 儲存檔案
        save_path = save_dir / f"{upload_id}_{policy.filename}"
        with save_path.open("wb") as f:
            f.write(await policy.read())

        # 記錄於 in-memory store
        STORE["uploads"][upload_id] = {
            "filename": policy.filename,
            "path": str(save_path),
        }

        return {"upload_id": upload_id, "saved_as": str(save_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
