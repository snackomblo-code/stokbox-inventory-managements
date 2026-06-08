"""Service untuk autentikasi & manajemen pengguna."""
from __future__ import annotations

import re
from typing import Optional

from pymongo.errors import DuplicateKeyError

from config.database import get_db
from models import users
from utils.helpers import parse_object_id, serialize_doc, serialize_docs, utcnow
from utils.security import hash_password, verify_password


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("Email wajib diisi.")
    if not EMAIL_RE.match(email):
        raise ValueError("Format email tidak valid.")
    return email


def _ensure_admin_exists() -> None:
    """Seed akun admin default jika belum ada user sama sekali."""
    if users().count_documents({}) > 0:
        return
    users().insert_one({
        "name": "Administrator",
        "email": "admin@inventaris.local",
        "password": hash_password("admin123"),
        "role": "admin",
        "photo": None,
        "is_active": True,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    })


def authenticate(email: str, password: str) -> Optional[dict]:
    """Verifikasi kredensial login. Mengembalikan user dict jika berhasil."""
    _ensure_admin_exists()
    email = (email or "").strip().lower()
    if not email or not password:
        return None
    user = users().find_one({"email": email})
    if not user:
        return None
    if not user.get("is_active", True):
        return None
    if not verify_password(password, user.get("password", "")):
        return None
    return user


def list_users() -> list[dict]:
    return serialize_docs(list(users().find().sort("created_at", -1)))


def get_user(user_id: str) -> Optional[dict]:
    oid = parse_object_id(user_id)
    if oid is None:
        return None
    return serialize_doc(users().find_one({"_id": oid}))


def create_user(payload: dict) -> dict:
    name = (payload.get("name") or "").strip()
    email = _validate_email(payload.get("email", ""))
    password = payload.get("password") or ""
    role = (payload.get("role") or "staff").strip().lower()
    if role not in {"admin", "staff"}:
        raise ValueError("Role harus admin atau staff.")
    if not name:
        raise ValueError("Nama wajib diisi.")
    if len(password) < 6:
        raise ValueError("Password minimal 6 karakter.")

    doc = {
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": role,
        "photo": payload.get("photo"),
        "is_active": bool(payload.get("is_active", True)),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    try:
        result = users().insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("Email sudah digunakan.") from None
    created = serialize_doc(users().find_one({"_id": result.inserted_id}))
    if created:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "create", "user", str(result.inserted_id),
            f"Membuat user {created.get('name', '')} ({created.get('email', '')})")
    return created


def update_user(user_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(user_id)
    if oid is None:
        return None
    update: dict = {"updated_at": utcnow()}

    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("Nama wajib diisi.")
        update["name"] = name
    if "email" in payload:
        update["email"] = _validate_email(payload.get("email", ""))
    if "role" in payload:
        role = (payload.get("role") or "").strip().lower()
        if role not in {"admin", "staff"}:
            raise ValueError("Role harus admin atau staff.")
        update["role"] = role
    if "is_active" in payload:
        update["is_active"] = bool(payload.get("is_active"))
    if payload.get("password"):
        if len(payload["password"]) < 6:
            raise ValueError("Password minimal 6 karakter.")
        update["password"] = hash_password(payload["password"])
    if "photo" in payload:
        update["photo"] = payload.get("photo")

    try:
        users().update_one({"_id": oid}, {"$set": update})
    except DuplicateKeyError:
        raise ValueError("Email sudah digunakan.") from None
    updated = serialize_doc(users().find_one({"_id": oid}))
    if updated:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "update", "user", user_id,
            f"Memperbarui user {updated.get('name', '')} ({updated.get('email', '')})")
    return updated


def delete_user(user_id: str) -> bool:
    oid = parse_object_id(user_id)
    if oid is None:
        return False
    current = users().find_one({"_id": oid})
    if current:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aktivitas_service.log(userId, userName, userRole, "delete", "user", user_id,
            f"Menghapus user {current.get('name', '')} ({current.get('email', '')})")
    result = users().delete_one({"_id": oid})
    return result.deleted_count > 0


def toggle_active(user_id: str) -> Optional[dict]:
    oid = parse_object_id(user_id)
    if oid is None:
        return None
    user = users().find_one({"_id": oid})
    if not user:
        return None
    new_state = not user.get("is_active", True)
    users().update_one({"_id": oid}, {"$set": {"is_active": new_state, "updated_at": utcnow()}})
    updated = serialize_doc(users().find_one({"_id": oid}))
    if updated:
        from fenrir import session
        from services import aktivitas_service
        userId = session.get("userId", "")
        userName = session.get("userName", "")
        userRole = session.get("userRole", "")
        aksi = "update"
        status = "aktif" if new_state else "nonaktif"
        aktivitas_service.log(userId, userName, userRole, aksi, "user", user_id,
            f"{'Mengaktifkan' if new_state else 'Menonaktifkan'} user {updated.get('name', '')} ({updated.get('email', '')})")
    return updated


def update_profile(user_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(user_id)
    if oid is None:
        return None
    update: dict = {"updated_at": utcnow()}
    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValueError("Nama wajib diisi.")
        update["name"] = name
    if "email" in payload:
        update["email"] = _validate_email(payload.get("email", ""))
    if "photo" in payload:
        update["photo"] = payload.get("photo")
    if not users().find_one({"_id": oid}):
        return None
    try:
        users().update_one({"_id": oid}, {"$set": update})
    except DuplicateKeyError:
        raise ValueError("Email sudah digunakan.") from None
    return serialize_doc(users().find_one({"_id": oid}))


def change_password(user_id: str, payload: dict) -> Optional[dict]:
    oid = parse_object_id(user_id)
    if oid is None:
        return None
    user = users().find_one({"_id": oid})
    if not user:
        return None
    old_pw = payload.get("old_password") or ""
    new_pw = payload.get("new_password") or ""
    confirm = payload.get("confirm_password") or ""
    if not verify_password(old_pw, user.get("password", "")):
        raise ValueError("Password lama salah.")
    if not new_pw or len(new_pw) < 6:
        raise ValueError("Password baru minimal 6 karakter.")
    if new_pw != confirm:
        raise ValueError("Konfirmasi password tidak cocok.")
    users().update_one({"_id": oid}, {"$set": {"password": hash_password(new_pw), "updated_at": utcnow()}})
    return serialize_doc(users().find_one({"_id": oid}))


def upload_photo(user_id: str, raw: bytes, filename: str, content_type: str) -> Optional[dict]:
    oid = parse_object_id(user_id)
    if oid is None:
        return None
    if not users().find_one({"_id": oid}):
        return None
    try:
        from config.cloudinary_client import upload_file
        result = upload_file(raw, folder="users", resource_type="image", public_id=f"user_{user_id}")
        url = result.get("secure_url") or result.get("url")
        public_id = result.get("public_id")
    except Exception:
        # Fallback: simpan di static/uploads
        import os
        from pathlib import Path
        upload_dir = Path("static/uploads/users")
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = (filename.rsplit(".", 1)[-1] if "." in filename else "jpg").lower()
        fname = f"user_{user_id}.{ext}"
        path = upload_dir / fname
        path.write_bytes(raw)
        url = f"/static/uploads/users/{fname}"
        public_id = None
    users().update_one({"_id": oid}, {"$set": {"photo": url, "photo_public_id": public_id, "updated_at": utcnow()}})
    return serialize_doc(users().find_one({"_id": oid}))

