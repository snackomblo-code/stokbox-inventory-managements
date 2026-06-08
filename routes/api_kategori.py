"""API CRUD kategori."""
from __future__ import annotations

from fenrir import Blueprint, Body, HTTPBadRequest, HTTPNotFound, Query, request

from services import kategori_service
from utils.decorators import api_login_required, role_required

kategori_bp = Blueprint("api-kategori", url_prefix="/api/kategori")


def _payload() -> dict:
    try:
        return request.json or {}
    except Exception:
        raise HTTPBadRequest("Body harus berupa JSON valid.")


@kategori_bp.get("")
@api_login_required
async def index(keyword: str = Query("")):
    return {"data": kategori_service.list_kategori(keyword)}


@kategori_bp.get("/<kategori_id>")
@api_login_required
async def show(kategori_id: str):
    doc = kategori_service.get_kategori(kategori_id)
    if not doc:
        raise HTTPNotFound("Kategori tidak ditemukan.")
    return doc


@kategori_bp.post("")
@role_required("admin")
async def create(payload: dict = Body(...)):
    try:
        return kategori_service.create_kategori(payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))


@kategori_bp.put("/<kategori_id>")
@role_required("admin")
async def update(kategori_id: str, payload: dict = Body(...)):
    try:
        result = kategori_service.update_kategori(kategori_id, payload)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not result:
        raise HTTPNotFound("Kategori tidak ditemukan.")
    return result


@kategori_bp.delete("/<kategori_id>")
@role_required("admin")
async def destroy(kategori_id: str):
    try:
        deleted = kategori_service.delete_kategori(kategori_id)
    except ValueError as exc:
        raise HTTPBadRequest(str(exc))
    if not deleted:
        raise HTTPNotFound("Kategori tidak ditemukan.")
    return {"message": "Kategori berhasil dihapus."}
