"""Decorator untuk otentikasi & otorisasi."""
from __future__ import annotations

from functools import wraps
from typing import Callable

from fenrir import HTTPUnauthorized, HTTPForbidden, session, redirect


def login_required(view: Callable) -> Callable:
    """Pastikan pengguna sudah login."""

    @wraps(view)
    async def wrapper(*args, **kwargs):
        if not session.get("isLoggedIn"):
            return redirect("/login")
        return await view(*args, **kwargs)

    return wrapper


def api_login_required(view: Callable) -> Callable:
    """Pastikan pengguna sudah login untuk endpoint JSON API."""

    @wraps(view)
    async def wrapper(*args, **kwargs):
        if not session.get("isLoggedIn"):
            raise HTTPUnauthorized("Sesi telah berakhir, silakan login kembali.")
        return await view(*args, **kwargs)

    return wrapper


def role_required(*roles: str) -> Callable:
    """Pastikan role pengguna termasuk dalam daftar role yang diizinkan."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        async def wrapper(*args, **kwargs):
            if not session.get("isLoggedIn"):
                raise HTTPUnauthorized("Sesi telah berakhir, silakan login kembali.")
            user_role = session.get("userRole")
            if user_role not in roles:
                raise HTTPForbidden("Anda tidak memiliki akses untuk tindakan ini.")
            return await view(*args, **kwargs)

        return wrapper

    return decorator
