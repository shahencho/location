from fastapi import APIRouter
from config import MAP_CONFIG, MONITORING_CONFIG

router = APIRouter()

@router.get("/api/config")
async def get_config():
    """Get configuration settings for the frontend"""
    return {
        **MAP_CONFIG,
        "UPDATE_INTERVAL": MONITORING_CONFIG["UPDATE_INTERVAL"]
    } 