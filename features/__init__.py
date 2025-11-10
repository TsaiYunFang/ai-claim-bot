from typing import Dict, Any
from uuid import uuid4

# Demo 用的 in-memory 儲存（重啟會清空）
STORE: Dict[str, Dict[str, Any]] = {
    "uploads": {},  # upload_id -> {...}
    "claims": {},   # claim_id  -> {...}
}

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"
