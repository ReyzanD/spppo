# Sistem Pendeteksi Pesan Penipuan Online

Aplikasi berbasis kecerdasan buatan (*Machine Learning*) untuk mendeteksi apakah sebuah pesan SMS atau WhatsApp terindikasi sebagai **penipuan (*fraud/scam*)** atau **pesan biasa/sah (*ham*)**.

Model dibangun menggunakan kombinasi **TF-IDF + Multinomial Naive Bayes** yang dilatih langsung pada dataset **SMS Bahasa Indonesia (Indonesian SMS Spam Collection)**. Layanan inferensi disediakan melalui REST API berbasis **FastAPI**, serta dapat diakses melalui antarmuka **Web React (Vite)** dan aplikasi mobile **Android (Kotlin + Jetpack Compose)**.

---

## Performa Model

Hasil pengujian terukur pada data uji (*held-out test set*) sebesar 20% (229 pesan):

| Metrik | Nilai | Keterangan |
|---|---|---|
| **Akurasi** | **95,20%** | Persentase prediksi keseluruhan yang benar |
| **Presisi (Penipuan)** | **92,42%** | Dari semua pesan yang ditebak penipuan, 92,42% benar-benar penipuan |
| **Recall (Penipuan)** | **91,04%** | Dari semua pesan penipuan nyata, 91,04% berhasil terdeteksi |
| **F1-Score (Penipuan)** | **91,73%** | Rata-rata harmonik antara presisi dan recall |

> *Catatan: Nilai metrik di atas dihitung secara objektif oleh `ml/train_model.py` dan tersimpan otomatis di `ml/metadata.json` (bukan nilai yang ditulis manual).*

---

## Struktur Repositori

```
ml/                              # Pipeline Machine Learning & Preprocessing
├── preprocessing.py             # Preprocessing: casefold, placeholder URL/Phone/Num, stopword ID/EN
├── train_model.py               # Script pelatihan: muat data → bersihkan → TF-IDF → Naive Bayes → evaluasi
├── stopwords_id.txt             # 356 stopword Bahasa Indonesia (Sastrawi/Tala)
├── stopwords_en.txt             # 198 stopword Bahasa Inggris
├── data/                        # Dataset SMS (indonesian_sms_spam.csv)
└── model.joblib, vectorizer.joblib, metadata.json   # Artefak model hasil pelatihan

backend/                         # Layanan REST API (FastAPI)
├── app/routers/                 # Endpoint: predict.py, model_info.py, health.py
├── app/services/                # Layanan ML & re-export preprocessing
├── app/config.py                # Konfigurasi aplikasi & CORS
├── tests/                       # Unit test otomatis (95 pengujian)
└── requirements-dev.txt         # Dependensi Python

frontend/                        # Antarmuka Web (React 19 + Vite)
├── src/views/                   # Tampilan: DetectView, HistoryView, ModelView
├── src/components/              # Komponen UI: Sidebar, ResultPanel, ProbabilityBar, Icons
└── src/hooks/                   # Manajemen riwayat lokal (localStorage)

android/                         # Aplikasi Mobile Android (Kotlin + Jetpack Compose)
└── app/src/main/java/com/example/penipuandetector/
    ├── data/                    # Retrofit (API Client), Room Database, Repository
    ├── ui/screens/              # Layar: Splash, Dashboard, Deteksi, Hasil, Riwayat, Info Model
    └── ui/viewmodel/            # ViewModel berbasis arsitektur MVVM
```

---

## 1. Menyiapkan Lingkungan & Melatih Model

**Prasyarat:** Python 3.11 atau lebih baru.

```bash
# 1. Masuk ke folder backend dan buat virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Untuk Windows: .venv\Scripts\activate

# 2. Pasang dependensi
pip install -r requirements-dev.txt
cd ..

# 3. Jalankan pelatihan model
python ml/train_model.py
```

### Tahapan Pelatihan:
1. Memuat dataset `ml/data/indonesian_sms_spam.csv` (1.143 pesan mentah).
2. Memeriksa dan membuang baris kosong serta data duplikat (1.142 pesan bersih).
3. Melakukan pembersihan teks (*preprocessing*):
   * *Case folding* (mengubah ke huruf kecil).
   * Penggantian nomor HP, tautan web, dan nominal angka menjadi placeholder `<phone>`, `<url>`, dan `<num>`.
   * Penghapusan tanda baca dan *whitespace* berlebih.
   * Penghapusan *stopwords* Bahasa Indonesia dan Inggris.
4. Ekstraksi fitur menggunakan **TF-IDF** gabungan: kata (1–2 gram) dan karakter (3–5 gram).
5. Pembagian data latih (80% / 913 baris) dan data uji (20% / 229 baris) secara *stratified* (`random_state=42`).
6. Melatih model **Multinomial Naive Bayes** (`alpha=0.1`).
7. Menyimpan artefak model ke `ml/model.joblib`, `ml/vectorizer.joblib`, dan `ml/metadata.json`.

#### Distribusi Data:
| Kategori | Jumlah Pesan |
|---|---|
| Pesan Mentah | 1.143 |
| Duplikat Dihapus | 1 |
| Pesan Bersih | **1.142** (335 Penipuan / 807 Bukan Penipuan) |
| Data Latih / Data Uji | 913 / 229 |

#### Matriks Konfusi (*Confusion Matrix*) Data Uji:
```
                      Prediksi: Bukan Penipuan    Prediksi: Penipuan
Aktual Bukan Penipuan           157                        5
Aktual Penipuan                   6                       61
```

---

## 2. Menjalankan Backend (FastAPI)

```bash
cd backend
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload
```

Server API akan berjalan di `http://localhost:8000`.

* **Dokumentasi Interaktif (Swagger UI):** <http://localhost:8000/docs>
* **Health Check:** <http://localhost:8000/health>
* **Informasi Model & Metrik:** <http://localhost:8000/model-info>

### Contoh Penggunaan Endpoint API

#### `POST /predict` — Deteksi Pesan Penipuan
```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"message":"SELAMAT! Nomor Anda meraih hadiah tunai Rp 75 juta. Hubungi WA 08123456789 atau klaim di http://bit.ly/hadiah-resmi"}'
```

**Contoh Respons:**
```json
{
  "label": "Penipuan",
  "probabilities": {
    "Penipuan": 1.0,
    "Bukan Penipuan": 0.0
  },
  "processed_text": "selamat nomor meraih hadiah uang tunai rp <num> <num> <num> hubungi whatsapp <phone> klaim <url>"
}
```

#### `POST /predict` — Pesan Normal / Sah
```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"message":"Halo, besok siang jadi makan bareng jam 12? Nanti aku pesankan tempatnya ya."}'
```

**Contoh Respons:**
```json
{
  "label": "Bukan Penipuan",
  "probabilities": {
    "Penipuan": 0.0,
    "Bukan Penipuan": 1.0
  },
  "processed_text": "halo besok siang jadi makan bareng jam <num> pesankan tempatnya ya"
}
```

---

## 3. Menjalankan Frontend (Web)

**Prasyarat:** Node.js 20 atau lebih baru.

```bash
cd frontend
npm install
npm run dev
```

Buka URL lokal yang muncul (default: `http://localhost:5173` atau `http://localhost:5174`).

Secara default, antarmuka web terhubung ke `http://localhost:8000`. Jika backend berjalan pada port atau alamat IP lain, ubah variabel di file `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

### Fitur Antarmuka Web:
* Formulir pemeriksaan teks pesan dengan tombol contoh penipuan dan pesan biasa berbahasa Indonesia.
* Visualisasi hasil analisis lengkap dengan bar persentase probabilitas (*Penipuan* vs *Bukan Penipuan*).
* Tampilan teks hasil normalisasi (*processed text*) untuk transparansi model.
* Penyimpanan riwayat pemeriksaan secara lokal di browser (`localStorage`).
* Halaman informasi lengkap performa model dan matriks evaluasi.

---

## 4. Menjalankan Aplikasi Android (Opsional)

**Prasyarat:** Android Studio, JDK 17+, Android SDK 35, serta emulator atau perangkat fisik Android.

```bash
cd android
echo "sdk.dir=$HOME/Android/Sdk" > local.properties
./gradlew assembleDebug
```

* File APK hasil kompilasi tersedia di: `android/app/build/outputs/apk/debug/app-debug.apk`.
* Base URL default pada emulator adalah `http://10.0.2.2:8000/`. Untuk pengujian pada perangkat fisik Android, tentukan alamat IP komputer Anda:
  ```bash
  ./gradlew assembleDebug -PAPI_BASE_URL=http://192.168.1.10:8000/
  ```

---

## 5. Pengujian Otomatis (*Automated Tests*)

Seluruh komponen dilengkapi pengujian unit untuk menjamin keandalan sistem:

```bash
# Pengujian Backend (95 unit test)
cd backend
source .venv/bin/activate
pytest -v

# Linter kode Python
ruff check app tests ../ml

# Pengujian & Build Frontend
cd ../frontend
npm run lint
npm run build
```

---

## Konfigurasi Environment

Variabel konfigurasi dapat diatur melalui file `.env` di dalam folder `backend/`:

| Variabel | Nilai Default | Penjelasan |
|---|---|---|
| `APP_NAME` | `Sistem Pendeteksi Pesan Penipuan Online` | Nama aplikasi di Swagger & OpenAPI |
| `ENVIRONMENT` | `development` | Mode aplikasi (`development`, `test`, `production`) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174,...` | Daftar URL frontend yang diizinkan mengakses API |
| `ML_MODEL_DIR` | `../ml` | Folder lokasi artefak model |
| `ML_MODEL_FILE` | `model.joblib` | Nama file model Naive Bayes |
| `ML_VECTORIZER_FILE` | `vectorizer.joblib` | Nama file vektorisasi TF-IDF |
| `ML_METADATA_FILE` | `metadata.json` | File ringkasan metrik model |

---

## Catatan & Batasan Sistem

1. **Bahasa Model**: Model dilatih khusus menggunakan dataset pesan SMS berbahasa Indonesia.
2. **Normalisasi Angka**: Angka, nomor telepon, dan URL tidak dihapus, melainkan dinormalisasi menjadi token `<num>`, `<phone>`, dan `<url>` karena merupakan indikator kuat modus penipuan online.
3. **Penyimpanan Riwayat**: Riwayat pemeriksaan pada web disimpan pada `localStorage` browser pengguna secara privat, tanpa pencatatan log pesan pribadi di sisi server database.
