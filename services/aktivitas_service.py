"""Service untuk mencatat aktivitas / audit trail."""
from __future__ import annotations

from datetime import datetime

from models import aktivitas as aktivitas_col
from utils.helpers import serialize_doc, serialize_docs


def log(
    user_id: str,
    user_name: str,
    user_role: str,
    aksi: str,
    entitas: str,
    entitas_id: str,
    deskripsi: str,
    detail: dict | None = None,
    ip_address: str = "",
) -> None:
    aktivitas_col().insert_one({
        "user_id": user_id,
        "user_name": user_name,
        "user_role": user_role,
        "aksi": aksi,
        "entitas": entitas,
        "entitas_id": entitas_id,
        "deskripsi": deskripsi,
        "detail": detail,
        "ip_address": ip_address,
        "created_at": datetime.now().isoformat(),
    })


def list_aktivitas(limit: int = 100, entitas: str = "", aksi: str = "") -> list[dict]:
    query: dict = {}
    if entitas:
        query["entitas"] = entitas
    if aksi:
        query["aksi"] = aksi
    cursor = aktivitas_col().find(query).sort("created_at", -1).limit(limit)
    return serialize_docs(list(cursor))


def get_aktivitas(id: str) -> dict | None:
    from utils.helpers import parse_object_id
    oid = parse_object_id(id)
    if oid is None:
        return None
    doc = aktivitas_col().find_one({"_id": oid})
    return serialize_doc(doc) if doc else None
