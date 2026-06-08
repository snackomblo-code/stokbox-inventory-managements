"""Service untuk kategori barang."""
from __future__ import annotations

from typing import Optional

from pymongo.errors import DuplicateKeyError

from models import kategori
from utils.helpers import parse_object_id, serialize_doc, serialize_docs, utcnow


def list_kategori(keyword: str = "") -> list[dict]:
    query: dict = {}
    if keyword:
        query["nama_kategori"] = {"$regex": keyword, "$options": "i"}
    return serialize_docs(list(kategori().find(query).sort("nama_kategori", 1)))


def get_kategori(kategori_id: str) -> Optional[dict]:
    oid = parse_object_id(kategori_id)
    if oid is None:
        return None
    return serialize_doc(kategori().find_one({"_id": oid}))


def create_kategori(payload: dict) -> dict:
    name = (payload.get("nama_kategori") or "").strip()
    if not name:
        raise ValueError("Nama kategori wajib diisi.")
    doc = {
        "nama_kategori": name,
        "icon_kategori": (payload.get("icon_kategori") or "bi-box").strip(),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    try:
        result = kategori().insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("Nama kategori sudah digunakan.") from None
    created = serialize_doc(kategori().find_one({"_id": result.inserted_id}))
    if created:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "create", "kategori", str(result.inserted_id),
            f"Membuat kategori {created.get('nama_kategori', '')}")
    return created


def update_kategori(kategori_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(kategori_id)
    if oid is None:
        return None
    update: dict = {"updated_at": utcnow()}
    if "nama_kategori" in payload:
        name = (payload.get("nama_kategori") or "").strip()
        if not name:
            raise ValueError("Nama kategori wajib diisi.")
        update["nama_kategori"] = name
    if "icon_kategori" in payload:
        update["icon_kategori"] = (payload.get("icon_kategori") or "bi-box").strip()
    try:
        kategori().update_one({"_id": oid}, {"$set": update})
    except DuplicateKeyError:
        raise ValueError("Nama kategori sudah digunakan.") from None
    updated = serialize_doc(kategori().find_one({"_id": oid}))
    if updated:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "update", "kategori", kategori_id,
            f"Memperbarui kategori {updated.get('nama_kategori', '')}")
    return updated


def delete_kategori(kategori_id: str) -> bool:
    oid = parse_object_id(kategori_id)
    if oid is None:
        return False
    from models import barang

    if barang().count_documents({"kategori_id": oid}) > 0:
        raise ValueError("Kategori masih digunakan oleh barang.")
    current = kategori().find_one({"_id": oid})
    if current:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "delete", "kategori", kategori_id,
            f"Menghapus kategori {current.get('nama_kategori', '')}")
    result = kategori().delete_one({"_id": oid})
    return result.deleted_count > 0
