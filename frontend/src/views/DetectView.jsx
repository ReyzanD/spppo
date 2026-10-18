import { useEffect, useRef, useState } from 'react';
import { describeApiError, predict } from '../ApiService';
import { asPercent } from '../format';
import { AlertIcon, ArrowRightIcon, ShieldIcon } from '../components/Icons';
import ResultPanel from '../components/ResultPanel';

const MAX_LENGTH = 1000;

const SAMPLE_FRAUD =
  'SELAMAT! Nomor Anda meraih hadiah uang tunai Rp 75.000.000 dari Gebyar Undian Berhadiah. Hubungi WhatsApp 08123456789 atau klaim hadiah Anda sekarang di http://bit.ly/undian-resmi.';
const SAMPLE_SAFE =
  'Halo, apa kabar? Besok jadi makan siang bareng jam 12? Nanti biar aku yang pesankan tempatnya ya.';

function GlanceMetric({ value, label }) {
  return (
    <div>
      <div className="glance-metric-value">{value}</div>
      <div className="glance-metric-label">{label}</div>
    </div>
  );
}

export default function DetectView({
  modelInfo,
  lastResult,
  onResult,
  onReset,
  onHistory,
}) {
  const [message, setMessage] = useState(lastResult?.message ?? '');
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const textareaRef = useRef(null);
  const resultRef = useRef(null);
  const scrollAfterSubmit = useRef(false);

  useEffect(() => {
    if (!scrollAfterSubmit.current || !lastResult) return;
    scrollAfterSubmit.current = false;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    resultRef.current?.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'start',
    });
  }, [lastResult]);

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = message.trim();

    if (!trimmed) {
      setError('Tulis atau tempel pesan terlebih dahulu.');
      textareaRef.current?.focus();
      return;
    }

    setStatus('loading');
    setError('');

    try {
      const data = await predict(trimmed);
      setMessage(trimmed);
      scrollAfterSubmit.current = true;
      onResult({
        ...data,
        message: trimmed,
        createdAt: Date.now(),
        id: typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      });
      setStatus('idle');
    } catch (requestError) {
      setError(describeApiError(requestError));
      setStatus('idle');
    }
  }

  function applySample(sample) {
    setMessage(sample);
    setError('');
    textareaRef.current?.focus();
    textareaRef.current?.select();
  }

  function handleReset() {
    setMessage('');
    setError('');
    onReset();
    textareaRef.current?.focus();
  }

  const isLoading = status === 'loading';
  const metrics = modelInfo?.metrics;

  return (
    <div className="view">
      <header className="view-head">
        <div>
          <h1 className="view-title">Sebelum percaya, periksa dulu.</h1>
          <p className="view-subtitle">
            Tempel pesan SMS atau WhatsApp yang mencurigakan. Model Naive Bayes
            akan menilai apakah pesan itu <strong>terindikasi penipuan</strong>
            dan menunjukkan seberapa yakin ia.
          </p>
        </div>

        <aside className="glance" aria-label="Ringkasan performa model">
          <p className="glance-label">Akurasi pada data uji</p>
          <p className="glance-value">
            {modelInfo ? asPercent(modelInfo.accuracy / 100, 2) : '—'}
          </p>
          <div className="glance-row">
            <GlanceMetric
              value={metrics ? asPercent(metrics.precision / 100) : '—'}
              label="Presisi"
            />
            <GlanceMetric
              value={metrics ? asPercent(metrics.recall / 100) : '—'}
              label="Recall"
            />
            <GlanceMetric
              value={metrics ? asPercent(metrics.f1 / 100) : '—'}
              label="F1"
            />
          </div>
        </aside>
      </header>

      <div className="detect-layout">
        <form
          className="input-panel"
          onSubmit={handleSubmit}
          aria-busy={isLoading}
        >
          <div className="field-label-row">
            <label className="field-label" htmlFor="pesan">
              Pesan yang ingin diperiksa
            </label>
            <span className={`char-count ${message.length >= MAX_LENGTH ? 'over' : ''}`}>
              {message.length} / {MAX_LENGTH}
            </span>
          </div>

          <textarea
            ref={textareaRef}
            id="pesan"
            className="message-field"
            value={message}
            onChange={(event) => {
              setMessage(event.target.value);
              setError('');
            }}
            placeholder="Contoh: Selamat! Anda memenangkan hadiah. Hubungi nomor berikut untuk klaim..."
            maxLength={MAX_LENGTH}
            rows={7}
            disabled={isLoading}
            aria-describedby="pesan-bantuan"
          />

          <div className="sample-row">
            <button
              type="button"
              className="sample-button"
              onClick={() => applySample(SAMPLE_FRAUD)}
              disabled={isLoading}
            >
              <span className="sample-button-label">Coba contoh penipuan</span>
              <span className="sample-button-hint">Fraud / penipuan</span>
            </button>
            <button
              type="button"
              className="sample-button"
              onClick={() => applySample(SAMPLE_SAFE)}
              disabled={isLoading}
            >
              <span className="sample-button-label">Coba pesan biasa</span>
              <span className="sample-button-hint">Ham / sah</span>
            </button>
          </div>

          {error && (
            <div
              className="form-error"
              role="alert"
              id="form-error"
            >
              <AlertIcon size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className="submit-row">
            <button
              type="submit"
              className="submit-button"
              disabled={isLoading}
              aria-busy={isLoading}
            >
              <span>{isLoading ? 'Memeriksa pesan…' : 'Periksa pesan'}</span>
              {isLoading ? (
                <span className="spinner" aria-hidden="true" />
              ) : (
                <ArrowRightIcon size={19} />
              )}
            </button>
            <p className="submit-note" id="pesan-bantuan">
              Maksimal 1.000 karakter. Hasil deteksi disimpan di riwayat
              perangkat ini.
            </p>
          </div>
        </form>

        <aside className="side-stack" aria-label="Penjelasan model">
          <div className="note-block">
            <h2 className="note-title">
              <ShieldIcon size={17} />
              Cara model membaca pesan
            </h2>
            <p className="note-body">
              Teks diubah menjadi bobot kata, lalu Multinomial Naive Bayes
              menghitung peluang tiap kelas. Nomor telepon, nominal, dan tautan
              tetap dipertahankan sebagai penanda karena sering muncul pada
              penipuan.
            </p>
          </div>

          <ol className="steps">
            <li className="step">
              <span className="step-number">1</span>
              <p className="step-text">
                <strong>Pembersihan teks</strong>
                Huruf diseragamkan, tanda baca dibuang, dan kata umum
                dihilangkan.
              </p>
            </li>
            <li className="step">
              <span className="step-number">2</span>
              <p className="step-text">
                <strong>TF-IDF</strong>
                Kata dan potongan karakter diberi bobot sesuai kekhasannya.
              </p>
            </li>
            <li className="step">
              <span className="step-number">3</span>
              <p className="step-text">
                <strong>Naive Bayes</strong>
                Peluang Penipuan dan Bukan Penipuan dibandingkan untuk
                menentukan hasil.
              </p>
            </li>
          </ol>

          <div className="language-note">
            <strong>Model dilatih dengan SMS berbahasa Indonesia</strong>
            Model menggunakan dataset SMS penipuan dan pesan normal Indonesia untuk deteksi yang lebih akurat.
          </div>
        </aside>
      </div>

      {lastResult && (
        <div ref={resultRef}>
          <ResultPanel result={lastResult} onReset={handleReset} onHistory={onHistory} />
        </div>
      )}
    </div>
  );
}
