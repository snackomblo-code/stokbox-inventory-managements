"""Dokumen MongoDB yang digunakan aplikasi."""
from config.database import collection


def users() -> collection:
    return collection("users")


def kategori() -> collection:
    return collection("kategori")


def barang() -> collection:
    return collection("barang")


def suplier() -> collection:
    return collection("suplier")


def barang_masuk() -> collection:
    return collection("barang_masuk")


def barang_keluar() -> collection:
    return collection("barang_keluar")


def stok_penyesuaian() -> collection:
    return collection("stok_penyesuaian")


def setting() -> collection:
    return collection("setting")


def aktivitas() -> collection:
    return collection("aktivitas")


def riwayat_stok() -> collection:
    return collection("riwayat_stok")
