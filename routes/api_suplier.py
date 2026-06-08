"""API CRUD suplier."""
from __future__ import annotations

from fenrir import Body, Blueprint, HTTPBadRequest, HTTPNotFound, Query

from services import suplier_service
from utils.decorators import api_login_required, role_required

suplier_bp = Blueprint("api-suplier", url_prefix="/api/suplier")


@suplier_bp.get("")
@api_login_required
async def index(keyword: str = Query("")):
    return {"data": suplier_service.list_suplier(keyword)}


@suplier_bp.get("/<suplier_id>")
@api_login_required
async def show(suplier_id: str):
    doc = suplier_service.get_suplier(suplier_id)
    if not doc:
        raise HTTPNotFound("Suplier tidak ditemukan.")
    return doc


@suplier_bp.post("")
@role_required("admin")
async def create(payload: dict = Body(...)):
    try:
        return suplier_service.create_suplier(payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@suplier_bp.put("/<suplier_id>")
@role_required("admin")
async def update(suplier_id: str, payload: dict = Body(...)):
    try:
        result = suplier_service.update_suplier(suplier_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not result:
        raise HTTPNotFound("Suplier tidak ditemukan.")
    return result


@suplier_bp.delete("/<suplier_id>")
@role_required("admin")
async def destroy(suplier_id: str):
    try:
        deleted = suplier_service.delete_suplier(suplier_id)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not deleted:
        raise HTTPNotFound("Suplier tidak ditemukan.")
    return {"message": "Suplier berhasil dihapus."}
