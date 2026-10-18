# Product Requirements Document (PRD)

**Sistem Pendeteksi Pesan Penipuan Online Menggunakan Metode Multinomial Naive Bayes**
Platform: Web

| Item | Keterangan |
|---|---|
| Nama Produk | Sistem Pendeteksi Pesan Penipuan Online |
| Metode | TF-IDF + Multinomial Naive Bayes |
| Platform | Web (browser-based, responsif) |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Database | PostgreSQL (production), SQLite (development) |
| Penulis | Naufal Faiz Mutawally / 232290 |
| Versi Dokumen | 1.1 |
| Tanggal | 17 Oktober 2026 |

## 1. Latar Belakang

Penipuan online melalui pesan teks (SMS, WhatsApp, email) semakin marak dan sulit dibedakan dari pesan sah. Dibutuhkan sistem berbasis web yang dapat diakses tanpa instalasi untuk memverifikasi sebuah pesan secara otomatis dengan machine learning.

## 2. Tujuan Produk

1. Mendeteksi pesan penipuan secara real-time (< 2 detik).
2. Mengimplementasikan TF-IDF + Multinomial Naive Bayes yang dapat direproduksi.
3. Menyediakan API terdokumentasi (OpenAPI/Swagger) antara frontend dan model.
4. Menampilkan hasil beserta probabilitas tiap kelas dan rekomendasi tindakan.
5. Menyimpan riwayat deteksi per pengguna di server.

## 3. Target Pengguna

- **Pengguna umum** — masyarakat yang ingin memverifikasi pesan yang diterima.
- **Admin** — mengelola model, dataset, dan pengguna.
- **Peneliti/mahasiswa** — membutuhkan metrik evaluasi dan data eksperimen yang dapat diaudit.

## 4. Keputusan Cakupan (v1.1)

Empat keputusan berikut menutup kontradiksi pada v1.0. Keputusan ini **mengikat** untuk implementasi MVP.

### 4.1 Dataset: Inggris (UCI) sebagai basis, Indonesia sebagai ekstensi

Model v1 dilatih pada **UCI SMS Spam Collection** (bahasa Inggris, 5.574 baris) sesuai pipeline pada §7. Konsekuensinya:

- **Seluruh contoh payload di dokumen dan demo harus berbahasa Inggris.** Contoh v1.0 (`"Selamat! Anda menang undian…"` → `prob_spam: 0.97`) tidak mungkin benar untuk vocabulary Inggris dan dihapus.
- Dataset Indonesia (mis. korpus pesan penipuan berbahasa Indonesia) dicatat sebagai **ekstensi opsional Fase 8**, bukan bagian MVP. Jika dikerjakan, dataset tersebut didokumentasikan terpisah dan menghasilkan versi model `2.0.0`.

**Alasan:** seluruh milestone, target akurasi, dan pipeline v1.0 dibangun di atas UCI. Mengganti dataset di tengah jalan mengubah semua metrik pada bab pengujian.

### 4.2 Riwayat disimpan otomatis, tanpa tombol simpan

`POST /predict` langsung menyimpan hasil dan mengembalikan `id_history`. Tombol "Simpan ke Riwayat" pada FR v1.0 **dihapus** — nilainya nol (satu klik tambahan) dan menjadi sumber kebingungan, karena endpoint simpan tidak pernah ada di daftar API.

### 4.3 Autentikasi: JWT stateless + refresh token

- Access token JWT (HS256), umur 60 menit, dikirim via header `Authorization: Bearer`.
- Refresh token opaque (bukan JWT), disimpan sebagai SHA-256 hash di tabel `refresh_token`, umur 7 hari, mendukung logout dan rotasi.
- Penghapusan access token sepenuhnya di sisi klien; efek "logout" di server dicapai dengan merevoke refresh token.

### 4.4 Admin tidak boleh mengunggah file `.pkl`

Fitur "upload model baru" pada v1.0 dihapus. Memuat pickle dari unggahan pengguna setara dengan eksekusi kode arbitrer di server. Admin hanya dapat **memicu retraining** dari dataset yang ada, dan server hanya memuat file dari direktori `backend/models/` yang sudah ditetapkan.

## 5. Fitur Fungsional

Penomoran `FR-*` di sini adalah **satu-satunya** sumber ID fitur produk. Dokumen FRD memakai awalan `UC-*` untuk use case agar tidak bentrok.

### FR-01 — Landing Page & Autentikasi (High)
- Landing page menjelaskan produk, CTA login/register.
- Registrasi: nama, email, password (min 8 karakter). Email unik, dinormalisasi lowercase.
- Login mengembalikan access token + refresh token.
- `POST /auth/logout` merevoke refresh token aktif.
- Password di-hash bcrypt (cost ≥ 12).

### FR-02 — Dashboard (High)
- Setelah login diarahkan ke `/dashboard`.
- Menampilkan: total deteksi, jumlah spam/ham, deteksi terakhir, dan kartu info model aktif.
- Grafik distribusi spam vs ham (Chart.js).

### FR-03 — Halaman Deteksi (High)
- Textarea pesan, tombol "Detect".
- Validasi klien + server: tidak kosong, minimal 3 karakter, maksimal 5.000 karakter.

### FR-04 — Hasil Deteksi (High)
- Label kelas: **Fraud** / **Not Fraud** pada UI Inggris, atau **Penipuan** / **Bukan Penipuan** pada UI Indonesia — dipilih satu saat implementasi, tidak dicampur.
- Probabilitas tiap kelas dalam persen + progress bar.
- Rekomendasi tindakan (statis per kelas).
- Tombol "Detect Again" dan "View in History" (tautan ke riwayat, bukan menyimpan — penyimpanan sudah otomatis, lihat §4.2).

### FR-05 — Riwayat Deteksi (Medium)
- Tabel: pesan, hasil, probabilitas, waktu.
- Pencarian teks pada `pesan_asli` dan filter `label` (`spam`/`ham`).
- Hapus single dan hapus semua (dengan dialog konfirmasi).
- Pagination server-side (default 10, max 100).

### FR-06 — Informasi Model (Medium)
- Menampilkan nama algoritma, versi, akurasi, precision/recall/F1 kelas spam, jumlah data training, tanggal training.
- Confusion matrix divisualisasikan dari `TRAINING_RUN.confusion_matrix`.
- Confusion matrix **wajib** ditampilkan (bukan opsional) karena dipakai di bab pengujian.

### FR-07 — Admin Panel (Low, di luar MVP)
- Melihat daftar model & run training, mengaktifkan model.
- Memicu retraining dari dataset yang ada (bukan upload `.pkl`).
- Melihat statistik dataset, menghapus user.
- **Tidak termasuk:** unggah file model.

## 6. Kebutuhan Non-Fungsional

| Kode | Kebutuhan |
|---|---|
| NFR-01 | Akurasi model ≥ 90% **dan** recall kelas spam ≥ 90% pada data uji 20%. Recall diprioritaskan karena false negative (penipuan lolos) lebih mahal daripada false positive. |
| NFR-02 | Latensi `POST /predict` p95 ≤ 500 ms, maksimum 2 detik pada hardware deployment. Model dimuat saat startup, bukan per-request. |
| NFR-03 | Web responsif (mobile-first) dengan Tailwind CSS; target Lighthouse Performance ≥ 85 di mobile. |
| NFR-04 | API FastAPI dengan dokumentasi otomatis di `/docs` dan `/redoc`. |
| NFR-05 | Model & vectorizer disimpan sebagai `.pkl` terpisah dan dimuat sekali saat startup (`@lru_cache` / lifespan handler). |
| NFR-06 | Preprocessing: case folding → normalisasi URL/telepon/angka menjadi placeholder → hapus tanda baca → hapus stopword Inggris. **Angka tidak dibuang** (lihat §7.3). |
| NFR-07 | Ekstraksi fitur TF-IDF: gabungan **word** unigram+bigram (`min_df=2`) dan **char_wb 3–5 gram** (`min_df=2`), `sublinear_tf=True` — di-fit **hanya** pada data training. Char n-gram ditambahkan setelah pengukuran menunjukkan recall naik dari 90,8% ke 94,4% (CV); lihat `PLAN.md` Fase 4. |
| NFR-08 | Split 80/20 stratified dengan `random_state` tetap yang dicatat di `TRAINING_RUN.split_seed`. |
| NFR-09 | Password bcrypt cost ≥ 12; HTTPS wajib di production; CORS dibatasi ke origin frontend; rate limit 5 login/menit/IP; token tidak disimpan di `localStorage` (gunakan cookie `httpOnly` untuk refresh token). |
| NFR-10 | Kompatibel dengan 2 versi terakhir Chrome, Firefox, Edge, Safari. |
| NFR-11 | Semua timestamp disimpan UTC dan dikirim ISO-8601 dengan sufiks `Z`. |
| NFR-12 | Migrasi skema melalui Alembic; tidak ada `Base.metadata.create_all()` di production. |
| NFR-13 | Unit test untuk `preprocessing.py` dan integration test untuk seluruh endpoint (pytest + httpx). Coverage service layer ≥ 80%. |

## 7. Arsitektur & Pipeline

### 7.1 Arsitektur

```
+-------------------+        HTTPS/JSON        +----------------------+
|  Browser (SPA)    | -----------------------> |  FastAPI (Uvicorn)   |
|  React + Vite     | <----------------------- |  routers/services    |
+-------------------+                          +----------+-----------+
                                                          |
                        +---------------------------------+------------------+
                        |                |                                   |
                        v                v                                   v
              +------------------+  +------------------+          +------------------+
              | Model .pkl       |  | PostgreSQL       |          | File models/     |
              | NB + TF-IDF      |  | users, history,  |          | (allowlist)      |
              | (load at boot)   |  | model_info       |          |                  |
              +------------------+  +------------------+          +------------------+
```

### 7.2 Alur data (offline → online)

1. **Dataset:** UCI SMS Spam Collection (`sms_spam_collection.csv`, 5.574 baris).
2. **Cleaning:** buang baris kosong, buang duplikat persis (5.574 → **5.171**; 403 duplikat terbuang), validasi label hanya `spam`/`ham`.
3. **Preprocessing:** sesuai NFR-06.
4. **Feature extraction:** TF-IDF fit pada train saja, transform pada test.
5. **Split:** 80/20 stratified, seed tetap.
6. **Training:** `MultinomialNB(alpha=1.0)` sebagai baseline; alpha dan set fitur akhirnya **dipilih lewat 5-fold CV pada data training saja** (terpilih: alpha=0.1, word+char n-gram), karena baseline hanya mencapai recall spam 77,86%.
7. **Evaluasi:** akurasi, precision/recall/F1 kelas spam, confusion matrix → ditulis ke `TRAINING_RUN` dan `MODEL_INFO`. Data uji 20% dinilai **tepat satu kali** setelah konfigurasi dipilih; tabel CV lengkap disimpan sebagai bukti seleksi.
8. **Deployment:** simpan `naive_bayes.pkl` + `tfidf_vectorizer.pkl`, set `is_active = TRUE` untuk model baru.
9. **Serving:** frontend → `POST /predict` → preprocessing → transform → predict_proba → simpan riwayat → JSON.

### 7.3 Catatan preprocessing: mengapa angka dipertahankan

v1.0 menghapus semua digit. Untuk deteksi penipuan ini justru membuang sinyal terkuat: nomor telepon (`0812…`), nomor rekening, dan nominal (`menang 1000`). Aturan v1.1:

| Pola | Diganti menjadi |
|---|---|
| `http://…`, `https://…`, `www.…` | `<url>` |
| Deret 8–15 digit (nomor telepon) | `<phone>` |
| Deret digit lain | `<num>` |

Placeholder ini menjadi token yang dipelajari TF-IDF, sehingga keberadaan URL/telepon tetap menjadi fitur, bukan hilang.

## 8. Kriteria Keberhasilan

- Akurasi ≥ 90% dan recall spam ≥ 90% pada data uji.
- p95 latensi `/predict` ≤ 500 ms.
- Semua FR-01 s/d FR-06 berfungsi end-to-end (FR-07 opsional).
- Riwayat tersimpan otomatis dan dapat difilter/dihapus.
- Confusion matrix dan metrik per-kelas tampil di halaman Info Model.
- Seluruh integration test lulus di CI.

## 9. Batasan & Asumsi

- Model v1 hanya mengenali **pesan berbahasa Inggris** (lihat §4.1). Pesan Indonesia akan diklasifikasi berdasarkan prior kelas dan hasilnya tidak valid — batasan ini harus ditulis eksplisit di laporan dan di UI (catatan kecil di form deteksi).
- Hanya 2 kelas: spam / ham.
- Frontend & backend di-deploy terpisah; koneksi internet diperlukan.
- Dataset tidak di-commit ke repo; disediakan script unduh + checksum.

## 10. Milestone

| Fase | Aktivitas | Output | Kriteria selesai |
|---|---|---|---|
| 1 | Scaffold repo & tooling | Monorepo, CI, pre-commit | `pytest` & `ruff` jalan di CI kosong |
| 2 | Dataset & cleaning | `data/sms_spam_collection.csv`, `clean_dataset.py` | Laporan jumlah baris sebelum/sesudah dedup |
| 3 | Preprocessing & fitur | `preprocessing.py`, unit test | ≥ 15 test case preprocessing lulus |
| 4 | Training & evaluasi | `train_model.py`, `*.pkl`, metrik | Akurasi & recall ≥ 90%, artefak metrik JSON |
| 5 | Backend: auth & model | `/auth/*`, `/model-info` | Login/logout/refresh lulus integration test |
| 6 | Backend: predict & history | `/predict`, `/history`, `/dashboard/stats` | Semua endpoint lulus integration test |
| 7 | Frontend SPA | 7 halaman + routing terproteksi | E2E manual: register → detect → history → delete |
| 8 | Deployment & dokumentasi | URL publik, README, laporan | Smoke test production lulus |
| 9 (opsional) | Dataset Indonesia | Model `2.0.0` | Metrik dilaporkan terpisah |

## 11. Teknologi

**Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, Pydantic v2, scikit-learn, pandas, bcrypt (via `pwdlib` atau `passlib`), PyJWT, pytest + httpx, ruff.

> Pin versi di `requirements.txt` **setelah** mengecek status maintenance & advisory keamanan terkini untuk library autentikasi — hindari mengandalkan versi "terbaru" secara implisit.

**Frontend:** React 18, Vite, React Router, Tailwind CSS, Axios, Chart.js, TanStack Query (opsional).

**Deployment:** backend di Railway/Render/VPS (Docker), frontend di Vercel/Netlify, PostgreSQL terkelola (Railway/Supabase/Neon).

## 12. Rencana API (ringkas)

Detail kontrak ada di `FRD.md` §5.

| Method | Endpoint | Auth | Deskripsi |
|---|---|---|---|
| POST | `/auth/register` | – | Registrasi |
| POST | `/auth/login` | – | Login, terbitkan access + refresh |
| POST | `/auth/refresh` | refresh cookie | Rotasi access token |
| POST | `/auth/logout` | Bearer | Revoke refresh token |
| GET | `/auth/me` | Bearer | Profil user aktif |
| POST | `/predict` | Bearer | Prediksi + simpan riwayat |
| GET | `/history` | Bearer | Riwayat (page, limit, q, label) |
| GET | `/history/{id}` | Bearer | Detail satu riwayat |
| DELETE | `/history/{id}` | Bearer | Hapus satu riwayat |
| DELETE | `/history` | Bearer | Hapus semua riwayat |
| GET | `/model-info` | Bearer | Info model aktif |
| GET | `/dashboard/stats` | Bearer | Statistik dashboard |
| GET | `/health` | – | Health check |
