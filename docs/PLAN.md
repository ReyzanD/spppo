# Rencana Pembangunan (Build Plan)

**Sistem Pendeteksi Pesan Penipuan Online — Multinomial Naive Bayes**
Versi: 1.0 · Tanggal: 17 Oktober 2026

Dokumen ini adalah urutan kerja yang bisa dieksekusi. Setiap fase punya *exit criteria* yang dapat diverifikasi dengan perintah, bukan opini.

## 0. Keputusan yang Sudah Dikunci

Jangan buka kembali keputusan ini tanpa alasan baru (rujukan: `PRD.md` §4).

| # | Keputusan | Konsekuensi |
|---|---|---|
| D1 | Dataset MVP = **UCI SMS Spam Collection (Inggris)**. Dataset Indonesia = Fase 9 opsional | Semua contoh/demo berbahasa Inggris; UI menampilkan catatan "model hanya untuk pesan Inggris" |
| D2 | Riwayat **tersimpan otomatis** saat `/predict` | Tidak ada endpoint simpan terpisah |
| D3 | Access token JWT di memori + refresh token httpOnly cookie | Tidak pakai `localStorage`; perlu endpoint refresh |
| D4 | Admin **tidak** mengunggah `.pkl` | Hanya retraining; load model dari allowlist |
| D5 | Label DB: `spam`/`ham`. Teks Indonesia hanya di layer schema | Mapping di `schemas/`, bukan DB |
| D6 | Angka **tidak** dihapus saat preprocessing, diganti placeholder | `<url>`, `<phone>`, `<num>` menjadi fitur |
| D7 | Frontend: React 18 + Vite + Tailwind, SPA dengan router terproteksi | Tidak pakai HTML statis |
| D8 | DB target: PostgreSQL produksi, SQLite dev, migrasi Alembic | Tidak ada `create_all()` di production path |

## 1. Struktur Repo Target

```
project-penipuan-detection/
├── docs/                        ERD.md, PRD.md, FRD.md, PLAN.md
├── backend/
│   ├── app/
│   │   ├── main.py              app factory, lifespan, CORS, exception handlers
│   │   ├── config.py            Settings (pydantic-settings) + .env
│   │   ├── database.py          engine, SessionLocal, get_db
│   │   ├── deps.py              get_current_user, require_admin
│   │   ├── models/              user.py, history.py, model_info.py, dataset.py, token.py
│   │   ├── schemas/             user.py, auth.py, history.py, prediction.py, common.py
│   │   ├── routers/             auth.py, predict.py, history.py, model_info.py, dashboard.py, health.py
│   │   ├── services/            preprocessing.py, ml_service.py, auth_service.py, history_service.py
│   │   └── utils/               security.py, pagination.py, errors.py
│   ├── alembic/                 env.py + versions/
│   ├── models/                  naive_bayes.pkl, tfidf_vectorizer.pkl (gitignored)
│   ├── data/                    sms_spam_collection.csv (gitignored)
│   ├── training/                download_dataset.py, clean_dataset.py, train_model.py, export_metrics.py
│   ├── tests/                   conftest.py, test_preprocessing.py, test_auth.py, test_predict.py, test_history.py
│   ├── requirements.txt
│   ├── pyproject.toml           ruff + pytest config
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/client.js        axios instance + interceptor refresh 401
│   │   ├── context/AuthContext.jsx
│   │   ├── components/          Navbar, ProtectedRoute, ResultCard, ProbBar, StatCard
│   │   ├── pages/               Landing, Register, Login, Dashboard, Detect, History, ModelInfo, NotFound
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── tailwind.config.js
│   └── package.json
├── .github/workflows/ci.yml
├── .gitignore
└── README.md
```

## 2. Urutan Fase & Dependency

```
F1 Scaffold ──> F2 Dataset ──> F3 Preprocessing ──> F4 Training ──┐
                                                                  │
                       F5 Auth & Model ◄──────────────────────────┘
                              │
                              v
                       F6 Predict & History
                              │
                              v
                       F7 Frontend SPA
                              │
                              v
                       F8 Integrasi & Deploy ──> F9 (opsional) Dataset ID
```

Backend auth (F5) bisa dikerjakan paralel dengan F2–F4 karena hanya bergantung pada skema DB.

---

## FASE 1 — Scaffold & Tooling

**Tujuan:** repo bisa di-`git clone` lalu `pytest` dan `ruff` jalan (meski test masih kosong).

**Langkah**
1. Buat struktur folder di §1 beserta `.gitignore` (abaikan `*.pkl`, `data/*.csv`, `.env`, `node_modules`, `dist`, `__pycache__`).
2. `backend/requirements.txt` + `pyproject.toml` (ruff: `line-length = 100`, pytest: `testpaths = tests`).
3. `app/config.py` — `Settings` dengan `DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_MINUTES=60`, `REFRESH_TOKEN_DAYS=7`, `CORS_ORIGINS`, `MODEL_DIR`. Gagal start bila `JWT_SECRET` kosong atau default di production.
4. `app/main.py` — FastAPI app, `lifespan` yang memuat model (F4 belum ada → log warning, jangan crash), CORS middleware, exception handler global yang memetakan `AppError` → envelope error §4.1 FRD.
5. `.env.example` (tanpa nilai rahasia) + `README.md` singkat cara menjalankan.
6. `.github/workflows/ci.yml` — job: install deps, `ruff check`, `pytest -q`.

**Exit criteria**
```bash
cd backend && ruff check . && pytest -q      # hijau (0 test dikoleksi pun boleh)
uvicorn app.main:app --reload               # /health -> {"status":"ok","model_loaded":false}
```

**Status: selesai.** 13 test lulus; `/health` menjawab `{"status":"ok","model_loaded":false}`; guard produksi menolak start bila `JWT_SECRET` masih default.

**Risiko:** JWT secret ter-commit. Mitigasi: `.env` di `.gitignore` sejak commit pertama, dan `config.py` menolak secret default.

---

## FASE 2 — Dataset & Cleaning

**Tujuan:** CSV bersih + laporan jumlah baris yang bisa dikutip di laporan.

**Langkah**
1. `training/download_dataset.py` — unduh UCI SMS Spam Collection ke `data/`, simpan `SHA256SUMS`, verifikasi checksum saat dijalankan ulang (idempoten).
2. `training/clean_dataset.py`:
   - normalisasi kolom → `label, teks_pesan`, buang baris kosong/null;
   - buang duplikat persis;
   - validasi label hanya `spam`/`ham`;
   - catat hitungan tiap tahap → `data/dataset_report.json`.
3. Opsional: cek duplikat nyaris identik (normalisasi lowercase + buang tanda baca) dan laporkan jumlahnya **tanpa** menghapus, agar bisa dibahas di bab dataset.

**Exit criteria**
```bash
python training/download_dataset.py && python training/clean_dataset.py
cat data/dataset_report.json   # berisi raw_count, after_dedup, spam/ham counts, near_duplicates
```

**Hasil terukur (dijalankan 2026-10-17):**

| Tahap | Jumlah |
|---|---|
| Baris mentah | 5.574 |
| Duplikat persis dibuang | 403 |
| Setelah dedup (`after_dedup`) | **5.171** |
| Konflik label (teks sama, label beda) | 0 |
| Spam / ham | 653 / 4.518 |
| Rasio spam | 12,63% |
| Grup near-duplicate (tidak dihapus) | 37 grup, 40 baris berlebih |

Angka **5.169** yang sering dikutip di literatur berasal dari prosedur dedup yang berbeda; yang diukur dan dipakai di repo ini adalah **5.171**, dan angka itulah yang harus dikutip di laporan.

**Risiko:** angka tidak cocok dengan laporan v1.0 (yang selalu menulis 5.574 sebagai total data). Mitigasi: `total_data` di `MODEL_INFO` diisi **jumlah baris training** dari `TRAINING_RUN.n_train`, bukan 5.574.

---

## FASE 3 — Preprocessing & Fitur

**Tujuan:** fungsi preprocessing deterministik, teruji, dan siap dipakai training maupun serving.

**Langkah**
1. Tulis `services/preprocessing.py` sesuai `FRD.md` §7. API: `clean(text: str) -> str`, `tokenize(text) -> list[str]`, plus konstanta regex placeholder.
2. Tambah stopword list ke repo (jangan bergantung unduhan NLTK saat runtime — bila pakai `nltk.download`, lakukan sekali di build/training dan simpan file lokal).
3. Unit test: minimal **15 kasus** — huruf besar/kecil, tanda baca berulang, URL (`http`, `https`, `www`), telepon 8–15 digit, angka biasa, campuran, string kosong, hanya tanda baca, hanya stopword, teks Inggris normal.
4. **Tes kritis yang wajib ada:** `"menang 1000"` → mengandung `<num>` (membuktikan angka tidak dibuang).

**Exit criteria**
```bash
pytest tests/test_preprocessing.py -q     # >= 15 kasus, semua lulus
python -c "from app.services.preprocessing import clean; print(clean('Call 081234567890 NOW!!! http://x.co'))"
# -> 'call <phone> <url>'
```

**Status: selesai.** 38 test lulus (syarat minimum 15). Perintah exit criteria menghasilkan tepat `call <phone> <url>`.

**Hasil terukur atas 5.171 pesan nyata:**

| Metrik | Nilai |
|---|---|
| Total token | 46.115 |
| Rata-rata token/pesan | 8,92 (median 7, maks 76) |
| Pesan mengandung `<num>` | 1.113 (21,5%) |
| Pesan mengandung `<phone>` | 333 |
| Pesan mengandung `<url>` | 90 |
| Pesan menjadi kosong setelah dibersihkan | 9 (semuanya ham) |

**Mengapa angka dipertahankan (deviasi dari spesifikasi awal):** 1.113 pesan (21,5%) mengandung token `<num>`. Aturan v1.0 yang membuang semua digit akan menghapus sinyal itu dari seperlima korpus — termasuk nominal dan nomor telepon, yang justru merupakan penanda penipuan terkuat. Ini alasan kuantitatif untuk keputusan pada PRD §7.3.

**Catatan untuk Fase 4:** 9 pesan ham menjadi string kosong (`"What you doing?how are you?"` — semuanya stopword; `":)"` — tidak ada huruf/angka). Vektornya akan menjadi nol dan `MultinomialNB` akan jatuh ke prior kelas. Tidak ada pesan spam yang kosong, jadi efeknya kecil — tetapi harus dilaporkan, bukan ditemukan diam-diam saat pengujian.

**Batasan yang diketahui:** daftar stopword yang dipakai (NLTK) memuat kata **`won`**, sehingga pada `"won 500"` hanya `<num>` yang tersisa. Kata sinyal lain (`click`, `link`, `claim`, `prize`, `call`, `reward`, `amount`) tetap dipertahankan. Perilaku ini dikunci oleh test `test_signal_word_won_is_dropped_by_the_stopword_list`; bila recall kelas spam kurang, mengeluarkan `won` dari daftar adalah kandidat ablation pertama di Fase 4.

**Risiko:** preprocessing di-refactor setelah training → model jadi tidak sinkron dengan serving. Mitigasi: test yang sama dipakai kedua jalur, dan `preprocessing.py` tidak boleh diubah setelah F4 tanpa retraining.

---

## FASE 4 — Training & Evaluasi

**Tujuan:** dua file `.pkl` + metrik JSON + baris `TRAINING_RUN`/`MODEL_INFO` yang memenuhi NFR-01.

**Langkah**
1. `training/train_model.py` — ikuti `FRD.md` §3.4 langkah 4–14 secara literal. Semua angka acak dari satu konfigurasi (`RANDOM_STATE = 42`, `TEST_SIZE = 0.2`).
2. Tulis metrik: `accuracy`, `precision_spam`, `recall_spam`, `f1_spam`, `confusion_matrix` → `models/metrics.json` + output tabel ke stdout.
3. Simpan `models/naive_bayes.pkl` dan `models/tfidf_vectorizer.pkl`.
4. `training/export_metrics.py` — insert `TRAINING_RUN` lalu `MODEL_INFO`, dan aktifkan model dalam satu transaksi (set semua `is_active = FALSE`, lalu `TRUE` untuk model baru).
5. Simpan juga vocabulary size + daftar 20 fitur dengan koefisien log-probabilitas tertinggi per kelas → `models/top_features.json`. Ini bahan bagus untuk bab pembahasan.

**Exit criteria**
```bash
python -m training.train_model
python -c "import json;m=json.load(open('models/metrics.json'));print(m);assert m['accuracy']>=90 and m['recall_spam']>=90"
```
Model/vectorizer dapat di-`pickle.load` ulang dan menghasilkan prediksi identik pada 5 pesan contoh (test determinisme).

**Status: selesai. NFR-01 terpenuhi.**

**Risiko yang benar-benar terjadi.** Baseline (word unigram+bigram, `alpha=1.0`, argmax) memberi **akurasi 97,10% tetapi recall spam hanya 77,86%** — 29 dari 131 spam lolos. Ini persis jebakan yang diperingatkan di atas: kelas positif hanya 12,6%, jadi akurasi tinggi mudah dicapai dengan menebak "ham". Baseline TIDAK memenuhi NFR-01.

**Mitigasi yang dipakai — seleksi lewat cross-validation, bukan tuning di data uji.**

Setiap kandidat dinilai dengan **5-fold stratified CV pada data training saja**; data uji 20% dievaluasi **tepat satu kali** di akhir. Menyetel hyperparameter dengan melihat data uji akan membocorkannya dan membuat angka laporan tidak bermakna.

Aturan seleksi, ditetapkan sebelum data uji dinilai:

```
layak     = CV accuracy >= 90, CV recall(spam) >= 90, CV precision(spam) >= 85
objektif  = F1(spam) CV terbesar
margin    = recall CV >= 92 (bukan 90), karena konfigurasi yang persis 90 di CV
            pernah jatuh ke 87,8 di satu split uji 1.035 baris
```

Hasil seleksi (16 konfigurasi = 4 set fitur x 4 alpha; tabel lengkap tersimpan di `models/training_run.json`):

| Fitur | alpha | CV acc | CV P | CV R | CV F1 | layak |
|---|---|---|---|---|---|---|
| word12_md1 | 0,05 | 98,50 | 96,21 | 91,76 | 93,88 | tidak (margin R) |
| word12 | 0,1 | 98,50 | 97,11 | 90,80 | 93,81 | tidak (margin R) |
| **word12+char35** | **0,1** | **98,09** | **90,83** | **94,44** | **92,56** | **YA (terpilih)** |
| char35 | 0,1 | 98,04 | 91,56 | 93,10 | 92,27 | ya |
| word12 | 1,0 | 97,34 | 100,00 | 78,93 | 88,18 | tidak (baseline) |

**Hasil akhir pada data uji yang ditahan (1.035 pesan, dinilai sekali):**

| Metrik | Baseline | Terpilih | Target |
|---|---|---|---|
| Akurasi | 97,10% | **97,87%** | ≥ 90% |
| Recall spam | 77,86% | **94,66%** | ≥ 90% |
| Precision spam | 99,03% | 89,21% | — |
| F1 spam | 87,18% | **91,85%** | — |
| Confusion `[[TN,FP],[FN,TP]]` | [[903,1],[29,102]] | [[889,15],[7,124]] | — |

Spam yang lolos turun dari **29 menjadi 7**; akurasi ikut naik. Harganya: false positive naik dari 1 ke 15. Pertukaran ini disengaja dan sejalan dengan NFR-01 yang memprioritaskan recall.

**Penyimpangan dari langkah di atas (beserta alasannya):**

1. **Dijalankan sebagai modul, `python -m training.train_model`, bukan `python training/train_model.py`.** Skrip ini mengimpor `app.services.preprocessing` agar preprocessing latih dan serving identik; dengan `-m`, direktori `backend/` ada di `sys.path`. Bentuk `python training/...` akan gagal import.
2. **Fitur ditambah char n-gram** (`char_wb` 3–5 gram) dan digabung dengan word n-gram. Recall naik dari 90,80 ke 94,44 (CV) — char n-gram menangkap obfuscation seperti "Fr33"/"w0n". NFR-07 di PRD diperbarui mengikuti ini.
3. **`training/export_metrics.py` DITUNDA ke Fase 5.** Langkah 4 memerlukan tabel `TRAINING_RUN`/`MODEL_INFO`, sedangkan skema baru dibuat lewat Alembic di Fase 5. Menulis DDL sendiri sekarang berarti ada dua sumber kebenaran skema. Sebagai gantinya Fase 4 menulis `models/training_run.json` (konfigurasi + tabel CV + metrik + provenance), dan Fase 5 tinggal membacanya untuk insert.

**Determinisme (terverifikasi):** menjalankan ulang training menghasilkan `metrics.json`, `naive_bayes.pkl`, dan `top_features.json` yang **byte-identik**; output `transform()` dan prediksi juga bit-identik. Hanya `tfidf_vectorizer.pkl` yang byte-nya berbeda antar-run (urutan serialisasi internal `FeatureUnion`) — tidak fungsional, tetapi disebutkan apa adanya di README.

---

## FASE 5 — Backend: Auth & Model

**Tujuan:** semua endpoint `/auth/*` dan `/model-info` berfungsi dengan kontrak FRD §4.

**Langkah**
1. `database.py` + model ORM sesuai `ERD.md` (SQLAlchemy 2.x style, `Mapped[]`).
2. Alembic init + migrasi awal yang menghasilkan **persis** DDL `FRD.md` §6 (termasuk partial unique index satu-model-aktif dan tiga index riwayat/dataset).
3. `utils/security.py` — hash/verify password (bcrypt cost 12), encode/decode JWT HS256, generator + hasher refresh token (SHA-256).
4. `services/auth_service.py` — register (cek email unik → 409), login (401 generik), refresh (rotasi), logout (revoke, idempoten), get_user_by_id.
5. `deps.py` — `get_current_user` (401 `TOKEN_EXPIRED` vs `TOKEN_INVALID` dibedakan), `require_admin`.
6. `routers/auth.py` + `routers/model_info.py` + `routers/health.py`.
7. Rate limit login 5/menit/IP (middleware sederhana atau `slowapi`) → 429 `RATE_LIMITED`.
8. Integration test (`httpx.AsyncClient` + DB SQLite sementara): register → login → me → refresh → logout → refresh setelah logout harus 401.

**Exit criteria**
```bash
alembic upgrade head
pytest tests/test_auth.py -q      # lulus, termasuk kasus negatif
# Swagger di /docs menampilkan 13 endpoint dengan skema error yang benar
```

**Risiko:** cookie refresh tidak terkirim lintas origin di dev (frontend :5173, backend :8000). Mitigasi: `SameSite=Lax` saat dev + `withCredentials: true` di axios, `Secure` hanya saat production.

---

## FASE 6 — Backend: Predict, History, Dashboard

**Tujuan:** jalur utama produk berfungsi end-to-end lewat API.

**Langkah**
1. `services/ml_service.py` — singleton yang dimuat di `lifespan`: `predict(text) -> (label, p_spam, p_ham, cleaned)`. Jika tidak ada model aktif → `AppError(503, MODEL_UNAVAILABLE)`. Ukur dan log durasi inferensi.
2. `routers/predict.py` — validasi (3–5000 karakter) → cleanup → predict → insert riwayat (id_model = model aktif) → envelope sukses. **Riwayat gagal disimpan tidak boleh menggagalkan prediksi** (log + `id_history: null`).
3. `routers/history.py` — list dengan `page/limit/q/label/sort`, `meta.total_pages`; `GET/DELETE /history/{id}` dengan filter `id_user`; `DELETE /history` (semua milik user). Semua endpoint history wajib filter ownership.
4. `routers/dashboard.py` — agregat `COUNT` + `FILTER` dalam satu query, plus deteksi terakhir.
5. Test: prediksi pesan spam contoh → `label == 'spam'`, `prob_spam > 0.5`, `abs(prob_spam+prob_ham-1) < 1e-6`; riwayat user A tidak terlihat user B (404, bukan 403); pagination & filter benar; `DELETE /history` hanya menghapus milik sendiri.

**Exit criteria**
```bash
pytest tests/ -q                                   # semua lulus
# total waktu respons /predict pada 20 request berturut-turut: p95 < 500 ms
```

**Risiko:** N+1 query saat memuat relasi. Mitigasi: `selectinload` untuk `id_model` dan uji dengan `echo=True` pada 1 request.

---

## FASE 7 — Frontend SPA

**Tujuan:** 7 halaman (PRD FR-01 s.d. FR-06) dapat dipakai manusia tanpa Postman.

**Langkah**
1. Vite + React + React Router + Tailwind setup; `api/client.js` dengan interceptor: pada 401 `TOKEN_EXPIRED`, panggil `/auth/refresh` **sekali**, ulangi request asli, gagal → redirect `/login`.
2. `AuthContext` — access token hanya di state React (bukan localStorage), `login/logout/refresh`, bootstrap saat mount.
3. Halaman: Landing, Register, Login (validasi inline), Dashboard (StatCard + Chart.js), Detect (form + ResultCard + ProbBar + rekomendasi + catatan "model untuk pesan Inggris"), History (tabel + search debounce + filter label + hapus single/all dengan dialog konfirmasi + pagination), ModelInfo (metrik + confusion matrix), NotFound.
4. `ProtectedRoute` — guard + dukungan `role="admin"`.
5. State loading/error/empty untuk setiap fetch — bukan hanya happy path.
6. Uji responsif di 375px dan 1440px.

**Exit criteria**
Skenario manual lengkap: register → login → detect pesan spam → hasil tampil dengan probabilitas → buka History → hasil ada (bukti auto-save) → filter `spam` → hapus satu → hapus semua → logout → `/dashboard` redirect ke `/login`. Semua langkah tanpa error di console.

**Risiko:** campur bahasa UI (Inggris/Indonesia) di tengah pengerjaan. Mitigasi: pilih satu bahasa UI sebelum menulis komponen pertama dan catat di README.

---

## FASE 8 — Integrasi, Deployment, Dokumentasi

**Langkah**
1. `docker-compose.yml` (backend + PostgreSQL) untuk paritas dev/prod.
2. `backend/Dockerfile` multi-stage; jalankan `alembic upgrade head` di entrypoint.
3. Deploy backend (Railway/Render/VPS) + PostgreSQL terkelola; deploy frontend (Vercel/Netlify) dengan `VITE_API_URL`.
4. Set `CORS_ORIGINS` ke domain frontend **saja**; verifikasi request dari origin lain ditolak.
5. Smoke test production: `/health`, register, login, detect, history.
6. README final: cara setup, cara training ulang, daftar endpoint, batasan (model Inggris), screenshot.
7. Kumpulkan artefak laporan: `metrics.json`, `dataset_report.json`, `top_features.json`, confusion matrix.

**Exit criteria:** URL publik dapat dipakai menyelesaikan skenario Fase 7; `/docs` dapat diakses; tidak ada secret di repo (`git log -p | grep -i secret` bersih).

---

## FASE 9 — Opsional: Dataset Indonesia

Hanya dikerjakan bila waktu tersisa. Pilih korpus publik pesan penipuan berbahasa Indonesia, dokumentasikan sumber & lisensinya, ulangi F2–F4, terbitkan model `2.0.0` dengan metrik terpisah, dan bandingkan dengan model `1.0.0` di laporan. **Jangan** menggabungkan dua dataset berbeda bahasa tanpa melaporkannya sebagai eksperimen tersendiri.

---

## 3. Definition of Done (keseluruhan)

- [ ] `ruff check .` dan `pytest -q` hijau di CI
- [ ] Migrasi Alembic bersih dari database kosong (`upgrade head` → `downgrade base`)
- [ ] Akurasi ≥ 90% **dan** recall spam ≥ 90%, keduanya tercatat di `model_info`
- [ ] Hanya satu model `is_active = TRUE` (dipaksa oleh unique index)
- [ ] Semua endpoint mengikuti envelope sukses/error FRD §4.1
- [ ] Endpoint riwayat tidak dapat membaca data user lain
- [ ] Tidak ada secret, dataset, atau `.pkl` di repository
- [ ] Frontend: 7 halaman, responsif, semua state (loading/error/empty) tertangani
- [ ] README memuat cara setup, retraining, dan batasan model

## 4. Urutan Pengujian yang Disarankan (untuk bab pengujian)

| # | Jenis | Cakupan | Alat |
|---|---|---|---|
| 1 | Unit | `preprocessing.clean` | pytest (≥15 kasus) |
| 2 | Unit | `security` (hash, JWT) | pytest |
| 3 | Integration | Seluruh endpoint + kasus negatif | pytest + httpx + SQLite |
| 4 | Model | Akurasi, precision, recall, F1, confusion matrix | `train_model.py` |
| 5 | Performance | p95 latensi `/predict` (20 request) | skrip sederhana / `hey` |
| 6 | UAT | Skenario manual Fase 7 | browser |
