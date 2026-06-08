"""Service untuk penyesuaian stok."""
from __future__ import annotations

from typing import Optional

from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from models import barang, stok_penyesuaian
from utils.helpers import (
    parse_date,
    parse_object_id,
    serialize_doc,
    serialize_docs,
    utcnow,
)
from utils.security import generate_no_transaksi


def list_penyesuaian(barang_id: str = "", status: str = "") -> list[dict]:
    query: dict = {}
    if barang_id:
        oid = parse_object_id(barang_id)
        if oid is not None:
            query["barang_id"] = oid
    if status:
        query["status"] = status
    pipeline = [
        {"$match": query},
        {"$sort": {"tanggal_penyesuaian": DESCENDING, "created_at": DESCENDING}},
    ]
    return serialize_docs(list(stok_penyesuaian().aggregate(pipeline)))


def get_penyesuaian(penyesuaian_id: str) -> Optional[dict]:
    oid = parse_object_id(penyesuaian_id)
    if oid is None:
        return None
    pipeline = [
        {"$match": {"_id": oid}},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user_info",
            }
        },
        {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "users",
                "localField": "dibatalkan_oleh",
                "foreignField": "_id",
                "as": "user_batal_info",
            }
        },
        {"$unwind": {"path": "$user_batal_info", "preserveNullAndEmptyArrays": True}},
        {
            "$addFields": {
                "nama_user": "$user_info.name",
                "nama_user_batal": "$user_batal_info.name",
            }
        },
        {"$project": {"user_info": 0, "user_batal_info": 0}},
    ]
    docs = list(stok_penyesuaian().aggregate(pipeline))
    return serialize_doc(docs[0]) if docs else None


def create_penyesuaian(payload: dict) -> dict:
    barang_id = parse_object_id(payload.get("barang_id"))
    if barang_id is None:
        raise ValueError("Barang wajib dipilih.")
    barang_doc = barang().find_one({"_id": barang_id})
    if not barang_doc:
        raise ValueError("Barang tidak ditemukan.")

    tanggal = parse_date(payload.get("tanggal_penyesuaian"))
    if tanggal is None:
        raise ValueError("Tanggal penyesuaian wajib diisi.")

    stok_sistem = int(barang_doc.get("stok", 0))
    stok_fisik = int(payload.get("stok_fisik", 0) or 0)
    if stok_fisik < 0:
        raise ValueError("Stok fisik tidak boleh negatif.")
    selisih = stok_fisik - stok_sistem

    doc = {
        "no_penyesuaian": generate_no_transaksi("SP"),
        "tanggal_penyesuaian": tanggal.isoformat(),
        "barang_id": barang_id,
        "kode_barang": barang_doc["kode_barang"],
        "nama_barang": barang_doc["nama_barang"],
        "satuan": barang_doc.get("satuan", ""),
        "stok_sistem": stok_sistem,
        "stok_fisik": stok_fisik,
        "selisih": selisih,
        "jenis": "tambah" if selisih >= 0 else "kurang",
        "alasan": (payload.get("alasan") or "").strip(),
        "catatan": (payload.get("catatan") or "").strip(),
        "user_id": parse_object_id(payload.get("user_id")),
        "status": "selesai",
        "dibatalkan_oleh": None,
        "dibatalkan_pada": None,
        "catatan_pembatalan": None,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    try:
        result = stok_penyesuaian().insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("Nomor penyesuaian bentrok, coba lagi.") from None

    barang().update_one(
        {"_id": barang_id},
        {"$set": {"stok": stok_fisik, "updated_at": utcnow()}},
    )

    result_id = str(result.inserted_id)
    from fenrir import session
    from services import aktivitas_service, barang_service
    userId = session.get("userId", "")
    userName = session.get("userName", "")
    userRole = session.get("userRole", "")
    aktivitas_service.log(userId, userName, userRole, "create", "stok_penyesuaian", result_id,
        f"Membuat penyesuaian stok {barang_doc.get('kode_barang', '')} - {barang_doc.get('nama_barang', '')} (selisih {selisih})")

    barang_service.catat_riwayat_stok(str(barang_id), barang_doc.get("kode_barang", ""),
        barang_doc.get("nama_barang", ""), stok_sistem, stok_fisik, selisih, "penyesuaian",
        ref_id=result_id, ref_no=doc.get("no_penyesuaian", ""))

    return get_penyesuaian(result_id) or {}


def batal_penyesuaian(penyesuaian_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(penyesuaian_id)
    if oid is None:
        return None
    current = stok_penyesuaian().find_one({"_id": oid})
    if not current:
        return None
    if current.get("status") == "dibatalkan":
        raise ValueError("Penyesuaian sudah pernah dibatalkan.")

    barang_id = current["barang_id"]
    stok_sebelumnya = int(current.get("stok_sistem", 0))
    barang().update_one(
        {"_id": barang_id},
        {"$set": {"stok": stok_sebelumnya, "updated_at": utcnow()}},
    )

    from fenrir import session
    from services import aktivitas_service, barang_service
    userId = session.get("userId", "")
    userName = session.get("userName", "")
    userRole = session.get("userRole", "")
    aktivitas_service.log(userId, userName, userRole, "cancel", "stok_penyesuaian", penyesuaian_id,
        f"Membatalkan penyesuaian stok {current.get('kode_barang', '')} - {current.get('nama_barang', '')}")

    barang_service.catat_riwayat_stok(str(barang_id), current.get("kode_barang", ""),
        current.get("nama_barang", ""), current.get("stok_fisik", 0), stok_sebelumnya,
        -(current.get("selisih", 0)), "batal_penyesuaian",
        ref_id=penyesuaian_id, ref_no=current.get("no_penyesuaian", ""),
        keterangan=payload.get("catatan_pembatalan", ""))

    update: dict = {
        "status": "dibatalkan",
        "dibatalkan_oleh": parse_object_id(payload.get("user_id")),
        "dibatalkan_pada": utcnow(),
        "catatan_pembatalan": (payload.get("catatan_pembatalan") or "").strip(),
        "updated_at": utcnow(),
    }
    stok_penyesuaian().update_one({"_id": oid}, {"$set": update})
    return get_penyesuaian(penyesuaian_id)


def delete_penyesuaian(penyesuaian_id: str) -> bool:
    oid = parse_object_id(penyesuaian_id)
    if oid is None:
        return False
    current = stok_penyesuaian().find_one({"_id": oid})
    if not current:
        return False
    if current.get("status") != "dibatalkan":
        raise ValueError("Hanya penyesuaian yang dibatalkan yang dapat dihapus.")
    if current:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "delete", "stok_penyesuaian", penyesuaian_id,
            f"Menghapus penyesuaian stok {current.get('kode_barang', '')} - {current.get('nama_barang', '')}")
    result = stok_penyesuaian().delete_one({"_id": oid})
    return result.deleted_count > 0
