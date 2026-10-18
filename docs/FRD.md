# Functional Requirements Document (FRD)

**Sistem Pendeteksi Pesan Penipuan Online — Multinomial Naive Bayes**
Platform: Web (FastAPI + React)
Versi dokumen: 1.1

> Use case di dokumen ini diberi awalan **`UC-*`** (bukan `FR-*`) agar tidak bentrok dengan ID fitur produk di `PRD.md` §5. Pemetaan ada di §8.

## 1. Aktor

| Aktor | Deskripsi |
|---|---|
| **Guest** | Belum login; hanya dapat mengakses landing, register, login |
| **User** | Pengguna terautentikasi; mendeteksi pesan dan mengelola riwayatnya sendiri |
| **Admin** | Mengelola model, dataset, dan pengguna (di luar MVP) |
| **ML Service** | Komponen internal FastAPI: preprocessing, TF-IDF, klasifikasi NB |

## 2. Use Case

| ID | Nama | Aktor | Precondition | Postcondition |
|---|---|---|---|---|
| UC-01 | Registrasi | Guest | Email belum terdaftar | Akun dibuat, dapat login |
| UC-02 | Login | Guest | Akun terverifikasi ada | Access + refresh token terbit |
| UC-03 | Refresh Token | User | Refresh token valid & belum revoked | Access token baru terbit |
| UC-04 | Logout | User | Login | Refresh token di-revoke, sesi klien dibersihkan |
| UC-05 | Melihat Dashboard | User | Login, ada data | Statistik tampil |
| UC-06 | Memasukkan Pesan | User | Login, di halaman deteksi | Teks terisi di form (state klien) |
| UC-07 | Melakukan Deteksi | User, ML Service | Pesan ≥ 3 karakter | Prediksi + probabilitas diterima |
| UC-08 | Preprocessing & TF-IDF | ML Service | Pesan diterima | Vektor fitur siap |
| UC-09 | Klasifikasi Naive Bayes | ML Service | Vektor fitur tersedia | Kelas + probabilitas dihasilkan |
| UC-10 | Menampilkan Hasil Deteksi | User | Response API diterima | Label, probabilitas, rekomendasi tampil |
| UC-11 | Melihat Riwayat | User | Login, riwayat ada | Daftar riwayat (pagination) tampil |
| UC-12 | Mencari & Memfilter Riwayat | User | Riwayat ada | Hasil terfilter tampil |
| UC-13 | Menghapus Riwayat | User | Riwayat ada | Baris terhapus dari database |
| UC-14 | Melihat Informasi Model | User | Login | Info model + metrik tampil |
| UC-15 | Memicu Retraining | Admin | Dataset tersedia | Model baru dibuat dan diaktifkan |
| UC-16 | Melihat Statistik Dataset | Admin | Dataset terisi | Jumlah spam/ham tampil |

## 3. Alur Detail

### 3.1 Registrasi (UC-01)

```
1. Guest membuka /register dan mengisi nama, email, password.
2. Validasi klien: email berformat, password >= 8 karakter.
3. POST /auth/register { nama, email, password }
4. Server normalisasi email -> lowercase, cek keunikan (409 bila ada).
5. Server hash password dengan bcrypt (cost 12).
6. Insert ke tabel user.role = 'user'.
7. Response 201 { status, data: { id_user, nama, email, role } }
8. Frontend arahkan ke /login dengan pesan sukses.
```

### 3.2 Login & Refresh (UC-02, UC-03, UC-04)

```
1. POST /auth/login { email, password }
2. Server verifikasi password; gagal -> 401 (pesan generik, tanpa membocorkan
   apakah email atau password yang salah).
3. Server terbitkan:
   - access_token  : JWT HS256, sub=id_user, role, exp=60 menit
   - refresh_token : string acak 32 byte (hex), disimpan sebagai SHA-256
                     hash di tabel refresh_token, exp=7 hari
4. Response 200 { status, access_token, token_type, expires_in,
                  user: { id_user, nama, role } }
   refresh_token dikirim sebagai cookie httpOnly, Secure, SameSite=Strict.
5. Frontend menyimpan access_token HANYA di memori (bukan localStorage).

Refresh:
1. POST /auth/refresh (cookie terkirim otomatis)
2. Server cari hash token; tolak bila tidak ada / revoked_at not null /
   expired_at < now -> 401.
3. Rotasi: revoke token lama, terbitkan token baru.
4. Response 200 { status, access_token, expires_in }

Logout:
1. POST /auth/logout dengan Bearer token.
2. Server set revoked_at = now untuk refresh token yang cocok.
3. Hapus cookie. Response 200 { status, message }.
```

### 3.3 Deteksi Pesan (UC-06 → UC-10)

```
1. User membuka /detect dan mengetik pesan.
2. Validasi klien: panjang >= 3 dan <= 5000 karakter.
3. POST /predict { pesan } dengan header Authorization: Bearer <access_token>
4. Server validasi JWT; invalid/expired -> 401 (frontend coba /auth/refresh
   sekali, lalu ulangi request; gagal -> arahkan ke /login).
5. Server validasi skema (Pydantic); gagal -> 422.
6. ML Service: preprocessing -> bersihkan(pesan)  [lihat §7]
7. ML Service: vec.transform([pesan_bersih]) dengan vectorizer ter-cache.
8. ML Service: model.predict_proba(...) -> [p_ham, p_spam]
9. label = 'spam' jika p_spam >= 0.5 else 'ham'
10. Server insert ke detection_history (pesan_asli, pesan_bersih,
    label_prediksi, prob_spam, prob_ham, id_user, id_model=model aktif).
11. Response 200:
    {
      "status": "success",
      "id_history": 1,
      "label": "spam",
      "hasil": "Penipuan",
      "prob_spam": 0.97,
      "prob_ham": 0.03,
      "pesan_bersih": "won prize click <url> claim",
      "model_versi": "1.0.0",
      "created_at": "2026-10-17T12:05:00Z"
    }
12. Frontend menampilkan hasil + progress bar + rekomendasi.
13. Riwayat sudah tersimpan (langkah 10). Tidak ada aksi simpan tambahan.
```

**Catatan:** langkah 10 adalah *write* di jalur baca-berat. Bila muncul error saat insert, request tetap dijawab sukses dengan `id_history: null` dan dilog — prediksi tidak boleh gagal hanya karena riwayat gagal disimpan.

### 3.4 Training Model (offline, UC-15 bagian ML)

```
1. Unduh dataset UCI SMS Spam Collection bila belum ada (dengan checksum).
2. Cleaning: buang baris kosong & duplikat, normalisasi header kolom.
3. Catat jumlah baris sebelum/sesudah -> dataset_report.json
4. Preprocessing seluruh teks (§7) -> kolom teks_bersih
5. Import ke tabel dataset (label ENUM 'spam'/'ham', sumber 'uci_sms_spam').
6. train_test_split(test_size=0.2, stratify=y, random_state=42)
7. TfidfVectorizer(min_df=2, ngram_range=(1,2), sublinear_tf=True).fit(X_train)
8. MultinomialNB(alpha=1.0).fit(X_train_tfidf, y_train)
9. Evaluasi pada X_test: accuracy, precision/recall/F1 kelas spam,
   confusion_matrix
10. Simpan: models/naive_bayes.pkl, models/tfidf_vectorizer.pkl
11. Insert TRAINING_RUN (test_size, split_seed, n_train, n_test,
    confusion_matrix, catatan) -> dapatkan id_training
12. Insert MODEL_INFO (id_training, id_dataset, metrik, versi, file_path,
    vectorizer_path, is_active=FALSE)
13. Transaksi: set is_active=FALSE untuk semua model, lalu TRUE untuk model
    baru. Hanya satu model aktif.
14. Tulis metrics.json sebagai artefak laporan.
```

## 4. Spesifikasi API

Base URL: `http://localhost:8000` (dev) · Semua response JSON.

### 4.1 Format envelope

Sukses (200/201) — **konsisten di semua endpoint**:

```json
{ "status": "success", "data": { }, "message": "optional" }
```

Untuk endpoint daftar, `data` adalah objek berisi `items` + `meta`:

```json
{
  "status": "success",
  "data": {
    "items": [],
    "meta": { "total": 25, "page": 1, "limit": 10, "total_pages": 3 }
  }
}
```

Error — **selalu** bentuk ini:

```json
{
  "status": "error",
  "error": { "code": "EMAIL_ALREADY_EXISTS", "message": "Email sudah terdaftar" }
}
```

| HTTP | `error.code` | Kapan |
|---|---|---|
| 400 | `BAD_REQUEST` | Payload tidak masuk akal |
| 401 | `INVALID_CREDENTIALS` | Login gagal |
| 401 | `TOKEN_EXPIRED` | Access token kedaluwarsa (klien → refresh) |
| 401 | `TOKEN_INVALID` | Token cacat / refresh token revoked |
| 403 | `FORBIDDEN` | Role tidak mencukupi |
| 404 | `NOT_FOUND` | Resource tidak ada atau bukan milik user |
| 409 | `EMAIL_ALREADY_EXISTS` | Registrasi email duplikat |
| 422 | `VALIDATION_ERROR` | Gagal validasi Pydantic (sertakan `details`) |
| 429 | `RATE_LIMITED` | Melebihi rate limit |
| 503 | `MODEL_UNAVAILABLE` | Tidak ada model aktif |

> **Catatan keamanan:** `NOT_FOUND` dipakai (bukan 403) ketika user mengakses riwayat milik user lain, agar keberadaan resource tidak bocor.

### 4.2 `POST /auth/register` — publik

Request: `{ "nama": "Naufal", "email": "naufal@example.com", "password": "rahasia123" }`

```json
{ "status": "success",
  "data": { "id_user": 1, "nama": "Naufal", "email": "naufal@example.com", "role": "user" },
  "message": "Registrasi berhasil" }
```

### 4.3 `POST /auth/login` — publik, rate limited

Request: `{ "email": "naufal@example.com", "password": "rahasia123" }`

```json
{ "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": { "id_user": 1, "nama": "Naufal", "role": "user" }
  } }
```
+ `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Path=/auth`

### 4.4 `POST /auth/refresh` — via cookie
`{ "status": "success", "data": { "access_token": "...", "expires_in": 3600 } }`

### 4.5 `POST /auth/logout` — Bearer
`{ "status": "success", "message": "Logout berhasil" }`

### 4.6 `GET /auth/me` — Bearer
`{ "status": "success", "data": { "id_user": 1, "nama": "Naufal", "email": "...", "role": "user" } }`

### 4.7 `POST /predict` — Bearer

Request:
```json
{ "pesan": "Congratulations! You won a prize. Click this link to claim it." }
```

Response 200:
```json
{ "status": "success",
  "data": {
    "id_history": 1,
    "label": "spam",
    "hasil": "Penipuan",
    "prob_spam": 0.97,
    "prob_ham": 0.03,
    "pesan_bersih": "congratulations won prize click link claim <url>",
    "model_versi": "1.0.0",
    "created_at": "2026-10-17T12:05:00Z"
  } }
```

### 4.8 `GET /history` — Bearer

Query: `?page=1&limit=10&q=prize&label=spam&sort=created_at:desc`
(`label` ∈ `spam|ham`, kosong = semua)

```json
{ "status": "success",
  "data": {
    "items": [
      { "id_history": 1,
        "pesan_asli": "Congratulations! You won a prize...",
        "pesan_bersih": "congratulations won prize click link claim <url>",
        "label": "spam", "hasil": "Penipuan",
        "prob_spam": 0.97, "prob_ham": 0.03,
        "created_at": "2026-10-17T12:05:00Z" }
    ],
    "meta": { "total": 25, "page": 1, "limit": 10, "total_pages": 3 }
  } }
```

### 4.9 `GET /history/{id}` · `DELETE /history/{id}` · `DELETE /history` — Bearer

- `GET /history/{id}` → satu objek seperti di atas; 404 bila bukan milik user.
- `DELETE /history/{id}` → `{ "status": "success", "message": "Riwayat berhasil dihapus" }`
- `DELETE /history` → `{ "status": "success", "message": "10 riwayat berhasil dihapus", "data": { "deleted": 10 } }`

### 4.10 `GET /model-info` — Bearer

```json
{ "status": "success",
  "data": {
    "nama_model": "Multinomial Naive Bayes",
    "versi": "1.0.0",
    "akurasi": 95.5,
    "precision_spam": 94.2,
    "recall_spam": 91.8,
    "f1_spam": 92.9,
    "total_data": 4135,
    "tanggal_training": "2026-10-17T12:00:00Z",
    "confusion_matrix": [[890, 40], [45, 405]],
    "label_kelas": ["ham", "spam"]
  } }
```

### 4.11 `GET /dashboard/stats` — Bearer

```json
{ "status": "success",
  "data": {
    "total_deteksi": 25,
    "total_penipuan": 15,
    "total_bukan_penipuan": 10,
    "deteksi_terakhir": { "id_history": 25, "pesan": "Congratulations...", "label": "spam", "created_at": "..." }
  } }
```

### 4.12 `GET /health` — publik
`{ "status": "ok", "model_loaded": true }`

## 5. Layering & Aturan Implementasi

```
routers/     → HTTP saja: parse, panggil service, bentuk response. Tanpa query SQL langsung.
services/    → logika bisnis + akses DB (SQLAlchemy session).
schemas/     → Pydantic I/O, termasuk mapping label 'spam' → 'Penipuan'.
models/      → deklarasi ORM.
utils/       → security (JWT, hash), pagination helpers.
```

Aturan wajib:

1. **Ownership** — setiap query riwayat difilter `WHERE id_user = current_user.id`. Tidak ada endpoint riwayat tanpa filter ini.
2. **Model aktif** — `ml_service` di-refresh saat startup; jika tidak ada model `is_active` → endpoint prediksi mengembalikan 503 `MODEL_UNAVAILABLE`.
3. **Konsistensi label** — DB selalu `spam`/`ham`; `"Penipuan"`/`"Bukan Penipuan"` hanya dibentuk di `schemas/`.
4. **Tanpa pickle dari unggahan** — jalur load model hanya dari direktori `backend/models/` berbasis baris `MODEL_INFO.file_path` (lihat PRD §4.4).
5. **Idempotensi logout** — logout pada token yang sudah revoked tetap 200.

## 6. Skema Database (DDL ringkas, PostgreSQL)

```sql
CREATE TYPE label_kelas AS ENUM ('spam', 'ham');
CREATE TYPE user_role  AS ENUM ('user', 'admin');

CREATE TABLE users (
  id_user     SERIAL PRIMARY KEY,
  nama        VARCHAR(100) NOT NULL,
  email       VARCHAR(254) NOT NULL UNIQUE,
  password    VARCHAR(255) NOT NULL,
  role        user_role    NOT NULL DEFAULT 'user',
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE dataset (
  id_dataset SERIAL PRIMARY KEY,
  teks_pesan TEXT        NOT NULL,
  label      label_kelas NOT NULL,
  split      VARCHAR(5)  NULL CHECK (split IN ('train','test') OR split IS NULL),
  sumber     VARCHAR(50) NOT NULL DEFAULT 'uci_sms_spam',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_dataset_dup ON dataset (md5(teks_pesan), label);

CREATE TABLE training_run (
  id_training      SERIAL PRIMARY KEY,
  id_dataset       INT     NOT NULL REFERENCES dataset(id_dataset) ON DELETE RESTRICT,
  test_size        REAL    NOT NULL DEFAULT 0.2,
  split_seed       INT     NOT NULL,
  n_train          INT     NOT NULL,
  n_test           INT     NOT NULL,
  confusion_matrix JSONB   NULL,
  catatan          VARCHAR(255) NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE model_info (
  id_model        SERIAL PRIMARY KEY,
  id_training     INT          NOT NULL UNIQUE REFERENCES training_run(id_training) ON DELETE RESTRICT,
  id_dataset      INT          NOT NULL REFERENCES dataset(id_dataset) ON DELETE RESTRICT,
  nama_model      VARCHAR(100) NOT NULL,
  versi           VARCHAR(20)  NOT NULL UNIQUE,
  akurasi         REAL         NOT NULL,
  precision_spam  REAL         NOT NULL,
  recall_spam     REAL         NOT NULL,
  f1_spam         REAL         NOT NULL,
  total_data      INT          NOT NULL,
  tanggal_training TIMESTAMPTZ NOT NULL,
  file_path       VARCHAR(255) NOT NULL,
  vectorizer_path VARCHAR(255) NOT NULL,
  is_active       BOOLEAN      NOT NULL DEFAULT FALSE
);
CREATE UNIQUE INDEX uq_model_single_active ON model_info (is_active) WHERE is_active;

CREATE TABLE detection_history (
  id_history     SERIAL PRIMARY KEY,
  id_user        INT         NOT NULL REFERENCES users(id_user) ON DELETE CASCADE,
  id_model       INT         NOT NULL REFERENCES model_info(id_model) ON DELETE RESTRICT,
  pesan_asli     TEXT        NOT NULL,
  pesan_bersih   TEXT        NOT NULL,
  label_prediksi label_kelas NOT NULL,
  prob_spam      REAL        NOT NULL CHECK (prob_spam BETWEEN 0 AND 1),
  prob_ham       REAL        NOT NULL CHECK (prob_ham  BETWEEN 0 AND 1),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_history_user_created ON detection_history (id_user, created_at DESC);
CREATE INDEX idx_history_user_label   ON detection_history (id_user, label_prediksi);

CREATE TABLE refresh_token (
  id_token   SERIAL PRIMARY KEY,
  id_user    INT          NOT NULL REFERENCES users(id_user) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  expired_at TIMESTAMPTZ  NOT NULL,
  revoked_at TIMESTAMPTZ  NULL,
  created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_refresh_user ON refresh_token (id_user);
```

Versi SQLite (dev) mengganti `SERIAL` → `INTEGER PRIMARY KEY AUTOINCREMENT`, `ENUM` → `VARCHAR + CHECK`, `JSONB` → `JSON`, `TIMESTAMPTZ` → `DATETIME`, dan partial unique index tetap didukung. Alembic menangani keduanya.

## 7. Preprocessing (detail)

```
clean(text) =
  1. casefold                         "WON a PRIZE!"        -> "won a prize!"
  2. normalisasi placeholder:
     - r'https?://\S+|www\.\S+'       -> "<url>"
     - r'\b\d{8,15}\b'                -> "<phone>"
     - r'\b\d+\b'                     -> "<num>"
  3. hapus tanda baca & karakter non-alfanumerik selain '<' '>' '_'
  4. collapse whitespace
  5. tokenisasi
  6. hapus stopword Inggris (NLTK english)
     -> token satu karakter dibuang
```

| Tahap | Input | Output |
|---|---|---|
| Case folding | `"HALO Dunia"` | `"halo dunia"` |
| Placeholder URL | `"klik http://x.co/a"` | `"klik <url>"` |
| Placeholder telepon | `"hub 081234567890"` | `"hub <phone>"` |
| Placeholder angka | `"menang 1000"` | `"menang <num>"` |
| Hapus tanda baca | `"halo!!!"` | `"halo"` |
| Stopword | `"this is a test"` | `"test"` |
| Tokenisasi + TF-IDF | `"won prize"` | sparse vector |

**Perubahan dari v1.0:** angka **tidak** dibuang, melainkan diganti placeholder (PRD §7.3). Tahap stemming/lemmatisasi tidak dipakai untuk bahasa Inggris (bukan kebutuhan) dan menjadi bahan ablation study bila diinginkan — dicatat di `TRAINING_RUN.catatan`.

## 8. Matriks Keterlacakan

| FR (PRD) | Use Case | Endpoint | Prioritas |
|---|---|---|---|
| FR-01 | UC-01, UC-02, UC-03, UC-04 | `/auth/*` | High |
| FR-02 | UC-05 | `/dashboard/stats` | High |
| FR-03 | UC-06, UC-07 | `/predict` | High |
| FR-04 | UC-08, UC-09, UC-10 | `/predict` | High |
| FR-05 | UC-11, UC-12, UC-13 | `/history*` | Medium |
| FR-06 | UC-14 | `/model-info` | Medium |
| FR-07 | UC-15, UC-16 | `/admin/*` | Low (opsional) |

## 9. Halaman Frontend

| Rute | Halaman | Akses | Isi |
|---|---|---|---|
| `/` | Landing | Public | Penjelasan, CTA |
| `/register` | Register | Public | Form registrasi |
| `/login` | Login | Public | Form login |
| `/dashboard` | Dashboard | User | Statistik + grafik + kartu model |
| `/detect` | Detect | User | Form + hasil + probabilitas |
| `/history` | History | User | Tabel, cari, filter, hapus, pagination |
| `/model` | Model Info | User | Metrik, confusion matrix |
| `/admin` | Admin Panel | Admin | Model, dataset, user (opsional) |

Routing terproteksi: guard memeriksa access token in-memory; jika kosong, coba `/auth/refresh` sekali sebelum redirect ke `/login`. 404 route → halaman fallback.
