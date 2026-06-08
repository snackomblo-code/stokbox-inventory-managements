# InventarisKu

Sistem manajemen inventaris barang modern berbasis **Fenrir Framework** + **MongoDB Atlas**.

- **Backend**: [Fenrir Web Framework](https://pypi.org/project/fenrir-framework/) (Python async)
- **Database**: MongoDB Atlas (NoSQL)
- **Media Storage**: Cloudinary (foto barang) + local untuk profil user & logo
- **Frontend**: Jinja2 templates + Vanilla JS (no build step)

## Fitur

- **Autentikasi** — Login multi-role (admin & staff), session-based
- **Dashboard** — Statistik real-time: 8 kartu ringkasan, 3 grafik (baris masuk/keluar, donat kategori, batang top 5), 4 tabel
- **Manajemen Barang** — CRUD + upload foto ke Cloudinary + QR/barcode + riwayat stok
- **Manajemen Kategori** — CRUD, filter barang per kategori
- **Manajemen Suplier** — CRUD
- **Transaksi Barang Masuk** — Multi-item, validasi stok, cetak stok minimum
- **Transaksi Barang Keluar** — Multi-item, validasi stok mencukupi
- **Penyesuaian Stok** — Stock opname + pembatalan dengan audit trail
- **Manajemen Pengguna** — CRUD, upload foto profil (admin only)
- **Pengaturan Aplikasi** — Nama, tagline, logo, favicon
- **Catatan Aktivitas** — Audit trail untuk semua operasi CRUD + import
- **Riwayat Stok** — Riwayat perubahan stok per barang (masuk, keluar, penyesuaian)
- **Backup & Restore** — Ekspor/impor database JSON + download otomatis
- **Import/Export Excel** — Template dinamis, import barang via XLSX

## Persyaratan

- Python 3.10+
- Akun MongoDB Atlas (cluster gratis cukup)
- Akun Cloudinary (free tier cukup, opsional — fallback ke local storage)

## Instalasi

1. **Clone atau masuk ke direktori proyek**

   ```bash
   cd inventaris
   ```

2. **Buat virtual environment (opsional tapi direkomendasikan)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Linux/Mac
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi environment**

   Salin `.env.example` menjadi `.env` dan isi nilainya:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   ```env
   MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/inventaris?retryWrites=true&w=majority
   MONGO_DB_NAME=inventaris

   CLOUDINARY_URL=cloudinary://your_api_key:your_api_secret@your_cloud_name
   CLOUDINARY_FOLDER=inventaris

   APP_SECRET_KEY=ganti-dengan-string-random-yang-panjang
   ```

5. **Jalankan aplikasi**

   ```bash
   fenrir run app.py --dev
   ```

   Lalu buka <http://localhost:8000> di browser.

   > Railway users: skip step ini — lihat section **Deployment ke Railway** di bawah.

## Akun Default

| Role  | Email                      | Password   |
| ----- | -------------------------- | ---------- |
| admin | `admin@inventaris.local`   | `admin123` |

Akun admin otomatis dibuat saat pertama kali aplikasi dijalankan dan tidak ada user di database.

## Struktur Direktori

```
inventaris/
├── app.py                    # Entry point aplikasi
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── config/                   # Konfigurasi DB & Cloudinary
│   ├── database.py
│   └── cloudinary_client.py
├── models/                   # Koleksi MongoDB (minimal, inline di service)
├── services/                 # Business logic
│   ├── auth_service.py
│   ├── barang_service.py          # CRUD barang + riwayat stok
│   ├── kategori_service.py
│   ├── suplier_service.py
│   ├── barang_masuk_service.py
│   ├── barang_keluar_service.py
│   ├── stok_penyesuaian_service.py
│   ├── setting_service.py
│   ├── cloudinary_service.py
│   ├── aktivitas_service.py        # Audit trail
│   └── laporan_backup_service.py   # Backup & restore
├── routes/                   # Blueprints (routing)
│   ├── page.py               # Halaman HTML
│   ├── auth.py
│   ├── api_kategori.py
│   ├── api_barang.py
│   ├── api_suplier.py
│   ├── api_barang_masuk.py
│   ├── api_barang_keluar.py
│   ├── api_stok_penyesuaian.py
│   ├── api_user.py
│   ├── api_setting.py
│   ├── api_aktivitas.py           # Endpoint audit trail
│   ├── api_dashboard.py           # Endpoint dashboard stats
│   └── api_laporan_backup.py      # Endpoint backup/restore
├── utils/                    # Utilitas
│   ├── security.py
│   ├── helpers.py
│   └── decorators.py
├── templates/                # Jinja2 templates
│   ├── base.html
│   ├── partials/             # sidebar, topbar, footer
│   ├── auth/                 # login
│   ├── barang/               # list, form, detail
│   ├── kategori/
│   ├── suplier/
│   ├── barang_masuk/
│   ├── barang_keluar/
│   ├── stok_penyesuaian/
│   ├── user/
│   ├── setting/
│   ├── dashboard/
│   ├── aktivitas/            # catatan aktivitas
│   └── backup/               # backup & restore
└── static/                   # File statis
    ├── css/
    │   ├── bootstrap-icons.css  # Bootstrap Icons lokal
    │   └── style.css
    ├── js/
    ├── vendor/                # jQuery, DataTables lokal
    └── uploads/               # Foto user & logo (gitignored)
        ├── barang/
        ├── users/
        └── settings/
```

## API Endpoint

Semua endpoint JSON berada di bawah prefix `/api/`. Endpoint halaman HTML berada di root (`/`, `/dashboard`, `/barang`, dst).

### Autentikasi
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| POST | `/auth/login` | Login | public |
| GET | `/auth/logout` | Logout | auth |
| GET | `/auth/me` | Info user aktif | auth |

### Dashboard
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/dashboard/stats` | Statistik dashboard | auth |

### Kategori
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/kategori` | List kategori | auth |
| POST | `/api/kategori` | Tambah kategori | admin |
| PUT | `/api/kategori/{id}` | Update kategori | admin |
| DELETE | `/api/kategori/{id}` | Hapus kategori | admin |

### Barang
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/barang` | List barang | auth |
| POST | `/api/barang` | Tambah barang | admin |
| PUT | `/api/barang/{id}` | Update barang | admin |
| DELETE | `/api/barang/{id}` | Hapus barang | admin |
| POST | `/api/barang/upload-foto` | Upload foto barang | admin |
| GET | `/api/barang/{id}/riwayat-stok` | Riwayat stok barang | auth |
| GET | `/api/barang/export` | Export Excel barang | auth |
| POST | `/api/barang/import` | Import Excel barang | admin |
| GET | `/api/barang/import-template` | Download template import | auth |

### Suplier
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/suplier` | List suplier | auth |
| POST | `/api/suplier` | Tambah suplier | admin |
| PUT | `/api/suplier/{id}` | Update suplier | admin |
| DELETE | `/api/suplier/{id}` | Hapus suplier | admin |

### Barang Masuk
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/barang-masuk` | List barang masuk | auth |
| POST | `/api/barang-masuk` | Catat barang masuk | admin/staff |
| PUT | `/api/barang-masuk/{id}` | Edit barang masuk | admin/staff |
| DELETE | `/api/barang-masuk/{id}` | Hapus barang masuk | admin |

### Barang Keluar
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/barang-keluar` | List barang keluar | auth |
| POST | `/api/barang-keluar` | Catat barang keluar | admin/staff |
| PUT | `/api/barang-keluar/{id}` | Edit barang keluar | admin/staff |
| DELETE | `/api/barang-keluar/{id}` | Hapus barang keluar | admin |

### Stok Penyesuaian
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/stok-penyesuaian` | List penyesuaian | auth |
| POST | `/api/stok-penyesuaian` | Buat penyesuaian | admin/staff |
| POST | `/api/stok-penyesuaian/{id}/batal` | Batalkan penyesuaian | admin/staff |
| DELETE | `/api/stok-penyesuaian/{id}` | Hapus penyesuaian | admin |

### Pengguna
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/user` | List pengguna | admin |
| POST | `/api/user` | Tambah pengguna | admin |
| PUT | `/api/user/{id}` | Update pengguna | admin |
| DELETE | `/api/user/{id}` | Hapus pengguna | admin |

### Pengaturan
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/setting` | Ambil pengaturan | auth |
| PUT | `/api/setting` | Update pengaturan | admin |

### Aktivitas
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/aktivitas` | List catatan aktivitas | auth |

### Backup
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/backup/export` | Download backup JSON | admin |
| POST | `/api/backup/restore` | Restore dari file backup | admin |

Dokumentasi otomatis tersedia di `/docs` (Swagger UI) dan `/redoc` ketika server berjalan.

## Deployment ke Railway

1. **Push ke GitHub** — buat repo dan push kode (pastikan `Procfile` dan `runtime.txt` ikut).

2. **Buat project di Railway** — hubungkan repo GitHub.

3. **Set Environment Variables** di Railway Dashboard:

   | Variable | Contoh |
   | -------- | ------ |
   | `MONGO_URI` | `mongodb+srv://user:pass@cluster.mongodb.net/inventaris?retryWrites=true&w=majority` |
   | `MONGO_DB_NAME` | `inventaris` |
   | `CLOUDINARY_URL` | `cloudinary://key:secret@cloud_name` |
   | `CLOUDINARY_FOLDER` | `inventaris` |
   | `APP_SECRET_KEY` | `random-string-panjang-untuk-session` |
   | `APP_ENV` | `production` |
   | `DEBUG` | `false` |

4. **Deploy** — Railway auto-detect `requirements.txt` → install dependencies, lalu jalankan `Procfile`.

5. **Domain** — Railway kasih domain `.railway.app`. Static files (CSS, JS, uploads) bisa bermasalah karena Railway punya filesystem ephemeral — foto barang tetap aman di Cloudinary, tapi foto profil user & logo akan hilang tiap deploy ulang. Untuk production, tambahkan CDN/file storage eksternal.

Catatan: Fenrir berjalan di port `$PORT` (otomatis dari Railway). App jadi _ephemeral_ — data di MongoDB aman, tapi file upload lokal hilang saat service restart.
