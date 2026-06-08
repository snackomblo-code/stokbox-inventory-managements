"""API untuk aktivitas / audit trail."""
from __future__ import annotations

from fenrir import Blueprint, Query

from services import aktivitas_service
from utils.decorators import api_login_required

aktivitas_bp = Blueprint("api-aktivitas", url_prefix="/api/aktivitas")


@aktivitas_bp.get("")
@api_login_required
async def list_aktivitas(
    limit: int = Query(100),
    entitas: str = Query(""),
    aksi: str = Query(""),
):
    items = aktivitas_service.list_aktivitas(limit=limit, entitas=entitas, aksi=aksi)
    return {"data": items}
