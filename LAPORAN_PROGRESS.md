# Laporan Progress, Kendala, dan Rencana Kerja Proyek
## Sistem Pendeteksi Pesan Penipuan Online (TF-IDF + Multinomial Naive Bayes)

| Informasi Proyek | Keterangan |
|---|---|
| **Judul Proyek** | Sistem Pendeteksi Pesan Penipuan Online Menggunakan Metode Multinomial Naive Bayes |
| **Penyusun / Mahasiswa** | Naufal Faiz Mutawally (NIM: 232290) |
| **Kategori Sistem** | Natural Language Processing (NLP), RESTful API, Web Application & Mobile Android |
| **Status Saat Ini** | Tahap Implementasi Inti & Pengujian Selesai (Feature-Complete MVP) |
| **Tanggal Pembaruan** | 19 Oktober 2026 |

---

## 1. Ringkasan Eksekutif

Proyek ini bertujuan mengembangkan sistem klasifikasi pesan teks otomatis untuk mendeteksi indikasi penipuan daring (*fraud/scam message*) pada pesan SMS dan WhatsApp berbahasa Indonesia. Sistem mengintegrasikan empat pilar utama:
1. **Pipeline Machine Learning**: Berbasis TF-IDF (gabungan n-gram kata dan karakter) serta algoritma Multinomial Naive Bayes.
2. **Backend API**: Layanan inferensi asinkron berkinerja tinggi berbasis FastAPI dengan arsitektur modular dan terdokumentasi via OpenAPI/Swagger.
3. **Web Frontend**: Antarmuka berbasis React 19 + Vite yang menyediakan visualisasi probabilitas, transparansi pra-pemrosesan teks, dan penyimpanan riwayat lokal.
4. **Mobile Client (Android)**: Aplikasi native berbasis Kotlin dan Jetpack Compose dengan arsitektur MVVM, koneksi jaringan via Retrofit, dan penyimpanan riwayat offline berbasis Room Database (SQLite).

Seluruh komponen telah teruji dengan **95 automated unit tests** (100% kelulusan) dan siap digunakan untuk pengujian inferensi real-time.

---

## 2. Laporan Progress yang Telah Dicapai

### 2.1 Modul Machine Learning & Preprocessing
* **Dataset SMS Indonesia**:
  - Berhasil mengintegrasikan dataset korpus pesan SMS Indonesia (*Indonesian SMS Spam Collection*).
  - Total dataset mentah sebanyak 1.143 baris. Dilakukan sanitasi data (menghapus 1 baris duplikat), menghasilkan **1.142 pesan bersih** (335 Penipuan, 807 Bukan Penipuan / Ham).
* **Pipeline Pembersihan Teks (*Preprocessing*) Khusus Modus Penipuan**:
  - *Case Folding*: Mengubah seluruh teks menjadi huruf kecil (*lowercase*).
  - *Token Placeholder Dinamis*: Nomor HP dinormalisasi menjadi token `<phone>`, tautan/URL menjadi `<url>`, dan nominal rupiah/angka menjadi `<num>`. Teknik ini mempertahankan pola penting yang menjadi sinyal kuat modus penipuan tanpa membebani vocabulary.
  - *Pembersihan Tanda Baca & Whitespace*: Menghilangkan karakter non-alfanumerik di luar token placeholder.
  - *Stopword Removal Bilingual*: Mengintegrasikan 356 stopword Bahasa Indonesia (Sastrawi/Tala) dan 198 stopword Bahasa Inggris umum.
* **Ekstraksi Fitur (Feature Extraction)**:
  - Menggunakan TF-IDF berbobot ganda: *Word n-gram* (1–2 gram) untuk menangkap konteks frasa dan *Character n-gram* (3–5 gram) untuk mengenali variasi typo atau penyingkatan kata khas SMS.
  - Mengaktifkan `sublinear_tf=True` guna meredam lonjakan frekuensi kata berulang.
* **Pelatihan & Evaluasi Model**:
  - Model dilatih menggunakan `MultinomialNB(alpha=0.1)` dengan pembagian *stratified train-test split* 80:20 (913 data latih, 229 data uji held-out).
  - Evaluasi objektif yang dihasilkan script pelatihan:
    - **Akurasi**: **95,20%**
    - **Presisi (Kelas Penipuan)**: **92,42%**
    - **Recall (Kelas Penipuan)**: **91,04%**
    - **F1-Score (Kelas Penipuan)**: **91,73%**
  - Matriks Konfusi (*Confusion Matrix* Data Uji):
    - *True Negative* (Bukan Penipuan benar): 157
    - *False Positive* (Bukan Penipuan ditebak Penipuan): 5
    - *False Negative* (Penipuan terlewat): 6
    - *True Positive* (Penipuan terdeteksi benar): 61
  - Serialisasi model dan vectorizer ke dalam format `model.joblib`, `vectorizer.joblib`, dan rekaman metrik ke `metadata.json`.

---

### 2.2 Modul Backend REST API (FastAPI)
* **Arsitektur & Konfigurasi**:
  - Menggunakan FastAPI dengan struktur berbasis service layer (`app/routers`, `app/services`, `app/utils`).
  - Pola *Application Factory* dan *Lifespan Event* untuk memuat model ML satu kali ke dalam memori saat server dinyalakan (*load once per process*), menjamin latensi inferensi sangat rendah (< 10 ms per request).
  - Penanganan error terpusat (*Global Exception Handling*) dengan format envelope JSON terstandarisasi.
* **Endpoint yang Tersedia**:
  - `POST /predict`: Menerima string pesan mentah, menjalankan preprocessing yang identik dengan pipeline training, menghasilkan label prediksi, probabilitas kedua kelas, serta teks hasil preprocessing.
  - `GET /model-info`: Menyediakan metadata model, akurasi, rincian dataset, matriks evaluasi, dan parameter training secara transparan.
  - `GET /health`: Pemeriksaan kesehatan layanan dan verifikasi kesiapan model dalam memori.
* **Keamanan & Kompatibilitas**:
  - Validasi ketat menggunakan skema Pydantic (menolak payload kosong atau string whitespace).
  - Konfigurasi CORS adaptif yang mendukung lingkungan pengembangan (`localhost`, port dinamis Vite) maupun produksi.

---

### 2.3 Modul Frontend Web (React 19 + Vite)
* **Desain UI/UX Responsif**:
  - Menggunakan React 19 dengan Vite sebagai bundler modern yang ringan dan cepat.
  - Tampilan navigasi sidebar yang bersih dengan 3 menu utama: **Deteksi Pesan**, **Riwayat Pemeriksaan**, dan **Informasi Model**.
* **Fitur Utama Web**:
  - *Interactive Test Input*: Dilengkapi tombol pintas template contoh pesan penipuan umum (undian berhadiah, transfer darurat) dan pesan percakapan normal.
  - *Visualisasi Hasil*: Tampilan visual status badge (Penipuan vs Aman), bar probabilitas persentase interaktif, serta ringkasan rekomendasi pencegahan kejahatan siber.
  - *Transparansi Model*: Menampilkan teks hasil normalisasi (*processed text*) agar pengguna dapat melihat representasi pesan yang diproses model.
  - *Penyimpanan Riwayat Lokal*: Menggunakan `localStorage` browser sehingga riwayat pemeriksaan tersimpan rapi tanpa mengirim atau menyimpan data pesan pribadi pengguna ke basis data server.

---

### 2.4 Modul Mobile Application (Android Native)
* **Teknologi & Desain Arsitektur**:
  - Dibangun secara native menggunakan **Kotlin** dan toolkit deklaratif **Jetpack Compose**.
  - Mengadopsi prinsip arsitektur **MVVM (Model-View-ViewModel)** dengan pemisahan dependensi yang bersih.
* **Fitur & Layar Aplikasi**:
  1. *Splash Screen*: Inisialisasi awal aplikasi.
  2. *Dashboard Screen*: Menampilkan ringkasan statistik (total pemeriksaan, rasio penipuan yang terdeteksi, panduan singkat).
  3. *Detect Screen*: Formulir pengujian pesan dengan tombol clear, paste clipboard, dan template pengujian.
  4. *Result Screen*: Visualisasi detail probabilitas, label penipuan/aman, serta langkah antisipasi.
  5. *History Screen*: Riwayat pemeriksaan lokal yang tersimpan secara persisten menggunakan **Room Database (SQLite)** dengan fitur hapus riwayat.
  6. *Model Info Screen*: Memuat detail performa model secara langsung dari endpoint `/model-info`.
* **Konektivitas Jaringan**:
  - Menggunakan **Retrofit 2** dan **OkHttp 3** dengan konfigurasi base URL fleksibel yang mendukung emulator (`10.0.2.2`) maupun perangkat fisik smartphone melalui argumen Gradle `-PAPI_BASE_URL`.

---

### 2.5 Pengujian Otomatis & Penjaminan Mutu (QA)
* **Automated Unit Testing Backend**:
  - Sebanyak **95 unit test** telah diimplementasikan menggunakan `pytest` dengan hasil 100% *passed*.
  - Rincian cakupan pengujian:
    - `test_preprocessing.py`: Pengujian casefolding, ekstraksi token URL, nomor telepon Indonesia, nominal rupiah, dan pemfilteran stopword.
    - `test_clean_dataset.py`: Pengujian pembersihan duplikasi dan baris null pada dataset.
    - `test_training.py`: Validasi pipeline TF-IDF, pelatihan Naive Bayes, perhitungan metrik evaluasi, dan integritas metadata.
    - `test_predict.py`: Pengujian endpoint API `/predict` dengan berbagai variasi input (pesan penipuan, pesan normal, input kosong, penanganan error).
    - `test_health.py` & `test_config.py`: Pengujian konfigurasi environment dan endpoint pemantauan status.
* **Linting & Code Quality**:
  - Backend lulus inspeksi linter Python modern `ruff`.
  - Frontend lulus pemeriksaan `oxlint`.

---

## 3. Kendala yang Dihadapi & Solusi yang Diterapkan

Selama proses pengembangan, terdapat beberapa tantangan teknis dan metodologis yang berhasil diidentifikasi dan diselesaikan:

### 3.1 Keterbatasan & Ketidakseimbangan Dataset Bahasa Indonesia
* **Kendala**:
  - Dataset publik SMS spam berbahasa Indonesia memiliki jumlah sampel yang relatif terbatas (sekitar 1.140 baris) dibandingkan dataset global bahasa Inggris seperti UCI SMS Spam Collection (5.574 baris).
  - Terjadi ketidakseimbangan kelas (*class imbalance*), di mana jumlah pesan normal (807 baris / ~70%) jauh lebih dominan dibanding pesan penipuan (335 baris / ~30%).
* **Solusi**:
  - Menerapkan pembagian data secara *stratified split* (`stratified=True`) agar proporsi kelas penipuan dan normal pada data latih (80%) dan data uji (20%) tetap seimbang dan representatif.
  - Memilih metrik evaluasi **F1-Score** dan **Recall** sebagai acuan utama performa, bukan hanya akurasi, untuk meminimalkan lolosnya pesan penipuan (*False Negative*).

---

### 3.2 Variasi Slang, Ejaan Typo, dan Penyamaran Kata oleh Pelaku
* **Kendala**:
  - Pesan penipuan di Indonesia sering memakai singkatan informal (*slang*), variasi angka pengganti huruf (*leetspeak*, misal `d4n4` untuk `dana`), atau penulisan ejaan yang sengaja disamarkan (misal `w-a`, `k-l-i-k`).
  - Jika hanya mengandalkan *word n-gram*, kata-kata yang salah ketik atau bervariasi tidak akan cocok dengan kosakata (*out-of-vocabulary*).
* **Solusi**:
  - Menerapkan ekstraksi fitur gabungan antara **Word n-gram (1–2 gram)** dan **Character n-gram (3–5 gram)** dalam pipeline TF-IDF. Character n-gram sangat efektif mengenali pola substring dan akar kata meskipun terjadi variasi typo atau penyamaran huruf.
  - Mengonversi nomor kontak, tautan web, dan angka ke token umum (`<phone>`, `<url>`, `<num>`). Dengan pendekatan ini, nomor atau link baru yang belum pernah muncul saat training tetap dikenali sebagai indikator kuat pesan mencurigakan.

---

### 3.3 Penyesuaian Arsitektur Penyimpanan Riwayat & Privasi Pengguna
* **Kendala**:
  - Pada dokumen desain awal (PRD fase perencanaan v1.0), dirancang sistem autentikasi pengguna (JWT) dan penyimpanan riwayat terpusat pada basis data PostgreSQL di backend.
  - Pendekatan ini memiliki risiko privasi data: menyimpan percakapan SMS pribadi pengguna di server berpotensi melanggar privasi, menambah beban latensi, dan membutuhkan infrastruktur database relasional yang rumit.
* **Solusi**:
  - Mengalihkan arsitektur ke model **Client-Side Persistence**:
    - Pada web frontend: riwayat tersimpan pada `localStorage` browser pengguna.
    - Pada aplikasi Android: riwayat tersimpan pada database lokal perangkat menggunakan **Room Database (SQLite)**.
  - Backend difokuskan sebagai layanan inferensi murni (*stateless microservice*), menghasilkan kinerja inferensi yang sangat cepat, aman, dan menghormati privasi data pengguna.

---

### 3.4 Konektivitas Aplikasi Android terhadap Backend Lokal
* **Kendala**:
  - Saat menguji aplikasi Android di emulator, alamat `localhost` atau `127.0.0.1` merujuk ke internal emulator Android itu sendiri, bukan ke server FastAPI di laptop/komputer host.
  - Pada perangkat fisik smartphone, koneksi HTTP sering diblokir oleh kebijakan keamanan *Cleartext Traffic* default Android (Android 9+).
* **Solusi**:
  - Mengonfigurasi `10.0.2.2` sebagai default base URL khusus Android Emulator.
  - Menyediakan argumen build Gradle dinamis `-PAPI_BASE_URL=http://<IP_KOMPUTER>:8000/` untuk pengujian pada perangkat fisik melalui jaringan Wi-Fi lokal.
  - Memastikan konfigurasi `AndroidManifest.xml` mendukung izin `android.permission.INTERNET` dan traffic HTTP lokal untuk keperluan pengembangan.

---

## 4. Rencana Progress Berikutnya (Next Steps & Roadmap)

Untuk meningkatkan kapabilitas, keandalan, dan kemudahan penyebaran sistem ke depan, berikut adalah rencana pengembangan yang terbagi ke dalam tiga fase:

```
Rencana Pengembangan:
Fase 1 (Jangka Pendek) ──> Fase 2 (Jangka Menengah) ──> Fase 3 (Jangka Panjang)
• Augmentasi Dataset       • Analisis Modus Baru (.apk) • Cloud Deployment & CI/CD
• Evaluasi Model Pembanding • Fitur Pelaporan Pengguna  • Auto-detect SMS Android
```

### 4.1 Fase 1: Optimasi Dataset & Eksperimen Model (Jangka Pendek)
1. **Pengumpulan & Augmentasi Korpus Data**:
   - Menambah sampel pesan penipuan terbaru (seperti modus surat tilang digital, undangan pernikahan APK, tagihan PLN/BPJS palsu, dan penipuan pinjaman online ilegal).
   - Melakukan teknik *Text Augmentation* (sinonim kata, variasi typo terencana) untuk memperkaya variasi data latih kelas minoritas.
2. **Benchmark Algoritma Alternatif**:
   - Melakukan perbandingan kinerja Multinomial Naive Bayes terhadap algoritma lain seperti **Linear Support Vector Machine (Linear SVM)**, **Logistic Regression**, dan model transformer bahasa Indonesia (misalnya **IndoBERT**).
   - Memastikan apakah model alternatif dapat memberikan kenaikan F1-Score yang signifikan dengan tetap menjaga latensi inferensi yang rendah.

---

### 4.2 Fase 2: Pengayaan Fitur Sistem (Jangka Menengah)
1. **Deteksi Ekstensi & Analisis URL Berbahaya**:
   - Menambahkan heuristik khusus untuk mendeteksi file berbahaya yang sering dikirimkan via WhatsApp/SMS, seperti ekstensi `.apk`, `.exe`, atau pemendek tautan (*link shortener* seperti `bit.ly`, `tinyurl.com`).
   - Menyediakan peringatan spesifik kepada pengguna mengenai jenis ancaman yang terdeteksi.
2. **Fitur Pelaporan & Crowdsourcing (*User Feedback Loop*)**:
   - Menyediakan tombol "Laporkan Kesalahan Prediksi" di aplikasi web dan mobile (*False Positive* / *False Negative*).
   - Data laporan dapat ditinjau untuk retraining model secara berkala.
3. **Ekspor Riwayat Deteksi**:
   - Menambahkan fitur ekspor riwayat pemeriksaan ke format CSV atau PDF pada aplikasi web dan mobile untuk keperluan dokumentasi atau bukti laporan kepolisian.

---

### 4.3 Fase 3: Integrasi Lanjutan & Deployment Cloud (Jangka Panjang)
1. **Penerapan Containerization & Cloud Hosting**:
   - Mengemas backend FastAPI ke dalam container Docker (`Dockerfile` dan `docker-compose.yml`).
   - Melakukan *deployment* ke layanan cloud publik (misalnya Railway, Render, atau VPS) dengan konfigurasi domain HTTPS (SSL).
   - Meng-host frontend web ke platform static hosting seperti Vercel atau Cloudflare Pages.
   - Dengan backend cloud ber-HTTPS, aplikasi Android dapat langsung diunduh dan digunakan oleh masyarakat luas tanpa konfigurasi IP lokal.
2. **Fitur Otomatisasi pada Aplikasi Android**:
   - Mengembangkan modul *BroadcastReceiver* opsional (dengan izin pengguna) untuk memindai SMS masuk secara otomatis dan memberikan notifikasi peringatan jika terindikasi penipuan.

---

## 5. Kesimpulan

Proyek **Sistem Pendeteksi Pesan Penipuan Online** telah berhasil mencapai milestone fungsional utama (MVP yang lengkap dan stabil). Seluruh komponen mulai dari pipeline Machine Learning, backend REST API, antarmuka web modern, hingga aplikasi mobile native Android telah saling terintegrasi dan beroperasi dengan baik. Pengujian otomatis menunjukkan tingkat akurasi model sebesar **95,20%** dan tingkat keberhasilan uji unit backend sebesar **100%**. 

Rencana kerja selanjutnya akan berfokus pada pengayaan dataset terkini, penambahan deteksi modus malware/APK, serta penyebaran sistem ke lingkungan cloud agar dapat dimanfaatkan oleh masyarakat secara luas.
