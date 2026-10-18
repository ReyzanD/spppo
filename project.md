# Sistem Pendeteksi Pesan Penipuan Online

**TF-IDF + Multinomial Naive Bayes · FastAPI · Web + Android**
Penulis: Naufal Faiz Mutawally / 232290

Aplikasi untuk memeriksa apakah sebuah pesan SMS/WhatsApp terindikasi penipuan.
Pesan dibersihkan dengan aturan yang sama saat pelatihan dan saat prediksi,
diubah menjadi fitur TF-IDF, lalu diklasifikasikan oleh Multinomial Naive Bayes.

## Stack

- **ML** — Python, scikit-learn; TF-IDF kata (1–2 gram) + karakter (3–5 gram),
  `MultinomialNB(alpha=0.1)`; artefak `model.joblib`, `vectorizer.joblib`,
  `metadata.json`.
- **Backend** — FastAPI; `POST /predict`, `GET /model-info`, `GET /health`;
  validasi Pydantic dan CORS.
- **Web** — React 19 + Vite; deteksi, hasil dengan peluang per kelas, riwayat
  lokal, dan informasi model.
- **Android** — Kotlin + Jetpack Compose, MVVM, Retrofit, Room; enam layar
  (Splash, Dashboard, Deteksi, Hasil, Riwayat, Informasi Model).
- **Dataset** — UCI SMS Spam Collection, 5.574 pesan mentah; 403 duplikat
  dibuang; 5.171 pesan bersih.

## Hasil terukur

Data uji 1.035 pesan: akurasi **97,87%**, presisi Penipuan 89,21%, recall
94,66%, F1 91,85%. Angka dihasilkan oleh `ml/train_model.py` dan disimpan di
`ml/metadata.json`, bukan nilai yang ditulis manual.

## Mulai

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cd .. && python ml/train_model.py
cd backend && uvicorn app.main:app --reload
```

Web: `cd frontend && npm install && npm run dev`.
Android: buka `android/` di Android Studio atau jalankan
`./gradlew :app:assembleDebug`.

Instruksi lengkap, contoh curl, konfigurasi, dan batasan ada di
[README.md](README.md).

## Dokumentasi

Dokumen di `docs/` adalah catatan desain fase web sebelumnya. Untuk menjalankan
versi yang sekarang, gunakan README di atas.
