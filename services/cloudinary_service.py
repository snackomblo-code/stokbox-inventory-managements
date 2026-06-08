"""Model & service Cloudinary untuk mengelola foto barang."""
from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional

from config.cloudinary_client import (
    configure,
    delete_image,
    get_folder,
    is_configured,
    upload_image,
)


def _save_local(file_obj, folder: str, public_id: str, ext: str = "jpg") -> dict:
    """Fallback: simpan file ke static/uploads/<folder>/ dan kembalikan URL lokal."""
    upload_dir = Path(f"static/uploads/{folder}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(file_obj, "read"):
        raw = file_obj.read()
    else:
        raw = bytes(file_obj)
    fname = f"{public_id}.{ext}"
    path = upload_dir / fname
    path.write_bytes(raw)
    return {
        "public_id": None,
        "url": f"/static/uploads/{folder}/{fname}",
        "width": None,
        "height": None,
    }


def _verify_url_accessible(url: str, *, timeout: float = 8.0) -> bool:
    """HEAD request ke URL Cloudinary untuk verifikasi file benar-benar tersimpan.
    Mencegah kasus 'ghost upload' di mana SDK mengembalikan response sukses
    tapi file sebenarnya tidak ada di storage / CDN.
    """
    if not url or not url.startswith(("http://", "https://")):
        return False
    try:
        import urllib.request
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "inventaris-verify/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception as e:
        import sys
        print(f"[VERIFY URL FAIL] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return False


def upload_barang_photo(file_obj, kode_barang: str, *, filename: Optional[str] = None, ext: Optional[str] = None) -> dict:
    """Upload foto barang ke Cloudinary, fallback ke static/uploads/ bila gagal.
    Selalu simpan salinan lokal di static/uploads/ untuk redundansi.
    """
    if ext is None:
        ext = "jpg"
        name_src = filename or getattr(file_obj, "name", None)
        if name_src and "." in name_src:
            ext = name_src.rsplit(".", 1)[-1].lower()
    public_id_name = f"barang_{kode_barang.lower()}"
    if not is_configured():
        return _save_local(file_obj, "barang", public_id_name, ext=ext)
    # Simpan salinan lokal dulu (sebelum Cloudinary berpotensi "memakan" stream)
    try:
        try:
            file_obj.seek(0)
        except Exception:
            pass
        local_info = _save_local(file_obj, "barang", public_id_name, ext=ext)
    except Exception as e:
        import sys
        print(f"[LOCAL SAVE FAIL] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        local_info = None
    # Lalu coba Cloudinary
    try:
        try:
            file_obj.seek(0)
        except Exception:
            pass
        configure()
        folder = "inventaris/barang"
        result = upload_image(file_obj, folder=folder, public_id=public_id_name, overwrite=True)
        url = result.get("secure_url") or result.get("url")
        # Verifikasi file benar-benar ada di Cloudinary — cegah "ghost upload"
        if url and _verify_url_accessible(url):
            return {
                "public_id": result.get("public_id"),
                "url": url,
                "local_url": local_info["url"] if local_info else None,
                "width": result.get("width"),
                "height": result.get("height"),
            }
        # Ghost upload: Cloudinary OK di response tapi file tidak accessible
        import sys
        print(f"[CLOUDINARY GHOST] upload response OK tapi file tidak ada di {url}; pakai local", file=sys.stderr, flush=True)
        if local_info:
            return {
                "public_id": None,
                "url": local_info["url"],
                "local_url": local_info["url"],
                "width": None,
                "height": None,
            }
        raise RuntimeError("Cloudinary ghost + local save gagal")
    except Exception as e:
        import sys
        print(f"[CLOUDINARY ERROR] {type(e).__name__}: {e}; pakai local", file=sys.stderr, flush=True)
        if local_info:
            return {
                "public_id": None,
                "url": local_info["url"],
                "local_url": local_info["url"],
                "width": None,
                "height": None,
            }
        raise


def upload_user_photo(file_obj, email: str) -> dict:
    """Upload foto pengguna."""
    if not is_configured():
        safe_email = email.replace("@", "_at_").replace(".", "_")
        return _save_local(file_obj, "users", f"user_{safe_email}", ext="jpg")
    try:
        configure()
        folder = "inventaris/users"
        safe_email = email.replace("@", "_at_").replace(".", "_")
        public_id = f"user_{safe_email}"
        result = upload_image(file_obj, folder=folder, public_id=public_id, overwrite=True)
        return {
            "public_id": result.get("public_id"),
            "url": result.get("secure_url") or result.get("url"),
        }
    except Exception:
        safe_email = email.replace("@", "_at_").replace(".", "_")
        return _save_local(file_obj, "users", f"user_{safe_email}", ext="jpg")


def upload_app_logo(file_obj, name: str = "logo") -> dict:
    """Upload logo aplikasi."""
    if not is_configured():
        return _save_local(file_obj, "settings", f"app_{name}", ext="png")
    try:
        configure()
        folder = "inventaris/app"
        public_id = f"app_{name}"
        result = upload_image(file_obj, folder=folder, public_id=public_id, overwrite=True)
        return {
            "public_id": result.get("public_id"),
            "url": result.get("secure_url") or result.get("url"),
        }
    except Exception:
        return _save_local(file_obj, "settings", f"app_{name}", ext="png")


def remove_photo(public_id: Optional[str]) -> None:
    """Hapus foto di Cloudinary jika ada."""
    if not public_id or not is_configured():
        return
    try:
        delete_image(public_id)
    except Exception:
        pass
