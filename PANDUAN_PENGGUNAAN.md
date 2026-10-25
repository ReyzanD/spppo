# Panduan Penggunaan Repository
## Sistem Pendeteksi Pesan Penipuan Online

Dokumentasi ini menjelaskan langkah-langkah lengkap untuk menyiapkan lingkungan pengembangan, melatih model *Machine Learning*, menjalankan layanan backend (FastAPI), antarmuka web (React + Vite), aplikasi mobile (Android Jetpack Compose), serta menjalankan rangkaian pengujian otomatis.

---

## Daftar Isi
1. [Ringkasan Proyek & Struktur Repositori](#ringkasan-proyek--struktur-repositori)
2. [Prasyarat Sistem](#prasyarat-sistem)
3. [Langkah 1: Setup Lingkungan Python & Pelatihan Model ML](#langkah-1-setup-lingkungan-python--pelatihan-model-ml)
4. [Langkah 2: Menjalankan Backend REST API (FastAPI)](#langkah-2-menjalankan-backend-rest-api-fastapi)
5. [Langkah 3: Menjalankan Frontend Web (React + Vite)](#langkah-3-menjalankan-frontend-web-react--vite)
6. [Langkah 4: Menjalankan & Membangun Aplikasi Android](#langkah-4-menjalankan--membangun-aplikasi-android)
7. [Contoh Pemanggilan Endpoint API (cURL)](#contoh-pemanggilan-endpoint-api-curl)
8. [Menjalankan Pengujian Otomatis & Linting](#menjalankan-pengujian-otomatis--linting)
9. [Panduan Pemecahan Masalah (Troubleshooting)](#panduan-pemecahan-masalah-troubleshooting)

---

## Ringkasan Proyek & Struktur Repositori

Sistem ini dirancang untuk mengidentifikasi apakah pesan teks (SMS / WhatsApp) tergolong sebagai **Penipuan (*Scam/Fraud*)** atau **Bukan Penipuan (*Ham*)** berbahasa Indonesia. Model menggunakan pipeline kombinasi **TF-IDF n-gram (kata & karakter)** dan klasifikasi **Multinomial Naive Bayes**.

```
Relly/
├── ml/                         # Pipeline Machine Learning & Data Training
│   ├── data/                   # Dataset indonesian_sms_spam.csv
│   ├── preprocessing.py        # Logika pembersihan & normalisasi teks
│   ├── train_model.py          # Script eksekusi training & evaluasi
│   ├── stopwords_id.txt        # Daftar stopword Bahasa Indonesia (356 kata)
│   ├── stopwords_en.txt        # Daftar stopword Bahasa Inggris (198 kata)
│   ├── model.joblib            # Artefak model Naive Bayes (dihasilkan train_model.py)
│   ├── vectorizer.joblib       # Artefak TF-IDF vectorizer (dihasilkan train_model.py)
│   └── metadata.json           # Metrik evaluasi & konfigurasi model
│
├── backend/                    # Layanan REST API berbasis FastAPI
│   ├── app/
│   │   ├── main.py             # Entry point aplikasi FastAPI & konfigurasi CORS
│   │   ├── config.py           # Konfigurasi aplikasi & parsing .env
│   │   ├── routers/            # Endpoint: /predict, /model-info, /health
│   │   ├── services/           # Logika inferensi model (ml_service.py)
│   │   └── utils/              # Penanganan exception & response error terpusat
│   ├── tests/                  # 95 automated unit tests (Pytest)
│   ├── pyproject.toml          # Konfigurasi linter ruff dan pytest
│   └── requirements-dev.txt    # Daftar pustaka Python backend
│
├── frontend/                   # Antarmuka Web SPA (React 19 + Vite)
│   ├── src/
│   │   ├── views/              # Halaman DetectView, HistoryView, ModelView
│   │   ├── components/         # Komponen UI: ProbabilityBar, ResultPanel, Sidebar
│   │   ├── hooks/              # useHistory (manajemen riwayat di browser localStorage)
│   │   └── ApiService.js       # Klien HTTP Axios ke Backend
│   ├── .env.example            # Template variabel environment web
│   └── package.json            # Dependensi React & Vite
│
├── android/                    # Aplikasi Mobile Native Android
│   ├── app/src/main/
│   │   ├── java/.../data/      # Retrofit HTTP Client & Room Database lokal
│   │   ├── java/.../ui/screens/# Layar Compose: Splash, Dashboard, Detect, Result, History, ModelInfo
│   │   └── java/.../ui/viewmodel/# Arsitektur MVVM ViewModel
│   └── build.gradle.kts        # Konfigurasi build Gradle Android
│
└── docs/                       # Dokumen Spesifikasi Awal (PRD, FRD, ERD, PLAN)
```

---

## Prasyarat Sistem

Pastikan perangkat Anda telah terpasang perangkat lunak berikut:

* **Python**: Versi `3.11` atau lebih tinggi (mendukung Python 3.11, 3.12, 3.13, 3.14).
* **Node.js**: Versi `20.x` LTS atau lebih baru dan `npm`.
* **Java Development Kit (JDK)**: Versi `17` (khusus untuk build aplikasi Android).
* **Android SDK & Build Tools**: SDK 35 (jika ingin menjalankan modul Android via Android Studio atau CLI Gradle).
* **Git**: Untuk mengelola repositori.

---

## Langkah 1: Setup Lingkungan Python & Pelatihan Model ML

Langkah ini diperlukan untuk memasang dependensi machine learning dan backend, serta melatih model agar artefak `.joblib` tersedia.

1. **Buka terminal dan navigasi ke direktori backend:**
   ```bash
   cd backend
   ```

2. **Buat dan aktifkan virtual environment:**
   * Di Linux / macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   * Di Windows (Command Prompt / PowerShell):
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```

3. **Pasang paket dependensi:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Jalankan script pelatihan model:**
   ```bash
   cd ..
   python ml/train_model.py
   ```

   *Proses ini akan membaca dataset `ml/data/indonesian_sms_spam.csv`, membersihkan teks, melakukan ekstraksi fitur TF-IDF, melatih Multinomial Naive Bayes, dan memperbarui artefak di folder `ml/`:*
   - `ml/model.joblib`
   - `ml/vectorizer.joblib`
   - `ml/metadata.json`

---

## Langkah 2: Menjalankan Backend REST API (FastAPI)

1. **Pastikan virtual environment telah aktif:**
   ```bash
   cd backend
   source .venv/bin/activate    # Linux/macOS
   # atau .venv\Scripts\activate untuk Windows
   ```

2. **Konfigurasi variabel environment (opsional):**
   Backend dapat langsung berjalan menggunakan nilai default. Jika ingin mengubah port atau URL CORS, buat file `.env` di folder `backend/`:
   ```env
   APP_NAME="Sistem Pendeteksi Pesan Penipuan Online"
   ENVIRONMENT=development
   CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173
   ML_MODEL_DIR=../ml
   ML_MODEL_FILE=model.joblib
   ML_VECTORIZER_FILE=vectorizer.joblib
   ML_METADATA_FILE=metadata.json
   ```

3. **Jalankan server Uvicorn:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Verifikasi server:**
   * **Endpoint Swagger UI:** Buka peramban ke [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Status Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
   * **Informasi Model & Metrik:** [http://localhost:8000/model-info](http://localhost:8000/model-info)

---

## Langkah 3: Menjalankan Frontend Web (React + Vite)

1. **Buka jendela terminal baru dan masuk ke folder `frontend`:**
   ```bash
   cd frontend
   ```

2. **Pasang paket node modules:**
   ```bash
   npm install
   ```

3. **Konfigurasi URL API:**
   Pastikan file `.env` di folder `frontend/` mengarah ke backend Anda:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Jalankan server pengembang (development server):**
   ```bash
   npm run dev
   ```

5. **Akses aplikasi web:**
   Buka peramban pada alamat yang ditampilkan pada terminal (biasanya [http://localhost:5173](http://localhost:5173) atau `http://localhost:5174`).

6. **Membangun bundle produksi (Production Build):**
   Jika ingin melakukan kompilasi file statis untuk hosting:
   ```bash
   npm run build
   ```
   Hasil build akan tersimpan di dalam direktori `frontend/dist/`.

---

## Langkah 4: Menjalankan & Membangun Aplikasi Android

Modul Android dibuat menggunakan **Kotlin** dan antarmuka deklaratif **Jetpack Compose**. Riwayat pemeriksaan tersimpan secara offline di perangkat menggunakan **Room Database (SQLite)**.

### Opsi A: Menggunakan Android Studio (Disarankan)
1. Buka Android Studio.
2. Pilih **File > Open**, lalu arahkan ke folder `android/`.
3. Tunggu hingga proses sinkronisasi Gradle selesai.
4. Hubungkan perangkat fisik via USB Debugging atau jalankan Android Emulator.
5. Tekan tombol **Run ('Shift + F10')**.

### Opsi B: Menggunakan Baris Perintah (Gradle CLI)
1. Masuk ke folder `android`:
   ```bash
   cd android
   ```

2. Buat file `local.properties` dan tentukan lokasi Android SDK Anda:
   * **Linux:**
     ```bash
     echo "sdk.dir=$HOME/Android/Sdk" > local.properties
     ```
   * **macOS:**
     ```bash
     echo "sdk.dir=$HOME/Library/Android/sdk" > local.properties
     ```
   * **Windows:**
     ```cmd
     echo sdk.dir=C\:\\Users\\USERNAME\\AppData\\Local\\Android\\Sdk > local.properties
     ```

3. **Kompilasi APK Debug:**
   * **Untuk pengujian pada Android Emulator:**
     Emulator dapat mengakses `localhost` komputer host melalui alamat alias `10.0.2.2`:
     ```bash
     ./gradlew assembleDebug
     ```
   * **Untuk pengujian pada Perangkat Fisik (Real Smartphone):**
     Tentukan alamat IP lokal (LAN) komputer yang menjalankan server FastAPI (misal `192.168.1.10`):
     ```bash
     ./gradlew assembleDebug -PAPI_BASE_URL=http://192.168.1.10:8000/
     ```

4. **Lokasi File APK:**
   File APK yang siap di-install ke HP berada di:
   `android/app/build/outputs/apk/debug/app-debug.apk`

---

## Contoh Pemanggilan Endpoint API (cURL)

Anda dapat menguji backend secara langsung tanpa frontend menggunakan perintah cURL:

### 1. Deteksi Pesan Penipuan
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "message": "SELAMAT! Nomor Anda terpilih mendapatkan hadiah uang tunai Rp 75.000.000 dari Gebyar Telkomsel. Info hubungi WA 08123456789 atau cek https://bit.ly/hadiah-resmi"
  }'
```

**Respon Sukses:**
```json
{
  "label": "Penipuan",
  "probabilities": {
    "Penipuan": 1.0,
    "Bukan Penipuan": 0.0
  },
  "processed_text": "selamat nomor terpilih mendapatkan hadiah uang tunai rp <num> <num> gebyar telkomsel info hubungi whatsapp <phone> cek <url>"
}
```

### 2. Deteksi Pesan Biasa (Bukan Penipuan)
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Halo Budi, nanti sore jadi futsal jam 5 di lapangan biasanya kan?"
  }'
```

**Respon Sukses:**
```json
{
  "label": "Bukan Penipuan",
  "probabilities": {
    "Penipuan": 0.0,
    "Bukan Penipuan": 1.0
  },
  "processed_text": "halo budi nanti sore jadi futsal jam <num> lapangan kan"
}
```

### 3. Mengambil Informasi & Metrik Model
```bash
curl -X GET http://localhost:8000/model-info
```

---

## Menjalankan Pengujian Otomatis & Linting

Repositori ini menerapkan pengujian otomatis untuk memastikan fungsionalitas dan konsistensi kode:

### 1. Pengujian Backend (Python Pytest)
Menjalankan 95 unit test mencakup sanitasi data, preprocessing, kalkulasi metrik, konfigurasi, dan endpoint API:
```bash
cd backend
source .venv/bin/activate
pytest -v
```

### 2. Pengecekan Gaya Kode Python (Ruff)
```bash
cd backend
source .venv/bin/activate
ruff check app tests ../ml
```

### 3. Pengecekan Kode Frontend (Oxlint)
```bash
cd frontend
npm run lint
```

---

## Panduan Pemecahan Masalah (Troubleshooting)

### 1. `FileNotFoundError: model.joblib or vectorizer.joblib not found`
* **Penyebab:** Model belum dilatih atau file artefak terhapus.
* **Solusi:** Jalankan script pelatihan kembali dari root direktori:
  ```bash
  python ml/train_model.py
  ```

### 2. Port 8000 atau 5173 Sudah Digunakan
* **Penyebab:** Proses lain sedang memakai port tersebut.
* **Solusi Backend:** Jalankan backend di port lain, misalnya `8001`:
  ```bash
  uvicorn app.main:app --reload --port 8001
  ```
  Jangan lupa memperbarui `VITE_API_URL=http://localhost:8001` pada `frontend/.env`.

### 3. Pesan Error CORS di Browser Console
* **Penyebab:** Origin frontend belum diizinkan oleh backend.
* **Solusi:** Pastikan port frontend terdaftar di `CORS_ORIGINS` pada `backend/.env` atau `backend/app/config.py`. Secara default, regex backend telah mengizinkan semua port `localhost` dan `127.0.0.1` saat mode `development`.

### 4. Aplikasi Android Tidak Dapat Menghubungi API
* **Jika menggunakan Android Emulator:** Gunakan URL `http://10.0.2.2:8000/` (karena `localhost` di dalam emulator merujuk ke internal emulator itu sendiri).
* **Jika menggunakan Perangkat Fisik (HP):**
  1. Pastikan HP dan laptop/komputer terhubung ke jaringan Wi-Fi yang sama.
  2. Cari IP laptop Anda (misal `ip a` di Linux atau `ipconfig` di Windows).
  3. Pastikan backend di-bind ke `0.0.0.0`: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
  4. Kompilasi aplikasi Android dengan menyertakan parameter IP:
     ```bash
     ./gradlew assembleDebug -PAPI_BASE_URL=http://<IP_LAPTOP_ANDA>:8000/
     ```
  5. Pastikan firewall di komputer mengizinkan koneksi masuk pada port 8000.
