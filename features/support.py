# features/support.py
from fastapi import APIRouter
from content import SUPPORT_INFO

router = APIRouter()

@router.get("/info")
def support_info():
    """取得客服資訊"""
    return SUPPORT_INFO

