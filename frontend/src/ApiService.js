import axios from 'axios';

// Vite injects VITE_* variables. Set VITE_API_URL in frontend/.env to point at
// a different backend; localhost is the default for the web client.
const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(
  /\/$/,
  '',
);

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: { 'Content-Type': 'application/json' },
});

export { API_BASE_URL };

export async function predict(message) {
  const response = await client.post('/predict', { message });
  return response.data;
}

export async function getModelInfo() {
  const response = await client.get('/model-info');
  return response.data;
}

export async function getHealth() {
  const response = await client.get('/health');
  return response.data;
}

/** Turn an Axios failure into a message that tells the reader what to do. */
export function describeApiError(error) {
  if (error?.code === 'ECONNABORTED') {
    return 'Permintaan melebihi batas waktu. Server mungkin sedang sibuk — coba lagi.';
  }
  if (!error?.response) {
    return 'Tidak dapat terhubung ke server API. Pastikan backend berjalan di ' + API_BASE_URL + '.';
  }

  const status = error.response.status;
  const detail =
    error.response.data?.error?.message || error.response.data?.detail || null;

  if (status === 422) {
    return 'Pesan tidak valid. Pastikan isinya tidak kosong dan tidak lebih dari 1.000 karakter.';
  }
  if (status === 503) {
    return 'Model belum tersedia di server. Jalankan pelatihan model, lalu mulai ulang API.';
  }
  if (status >= 500) {
    return detail || `Server mengalami kesalahan (${status}). Coba lagi sebentar.`;
  }
  return detail || `Permintaan ditolak oleh server (${status}).`;
}
