import { API_BASE_URL } from '../ApiService';
import { asDate, asNumber, asPercent } from '../format';
import { RefreshIcon } from '../components/Icons';

function DetailRow({ label, children }) {
  return (
    <div className="detail-row">
      <span className="detail-key">{label}</span>
      <span className="detail-value">{children}</span>
    </div>
  );
}

function SkeletonState() {
  return (
    <div className="model-layout" aria-busy="true" aria-label="Memuat informasi model">
      <div className="loading-panel">
        <div className="skeleton short" />
        <div className="skeleton" style={{ height: 70 }} />
        <div className="skeleton wide" />
        <div className="skeleton wide" />
      </div>
      <div className="loading-panel">
        <div className="skeleton short" />
        <div className="skeleton wide" />
        <div className="skeleton" />
        <div className="skeleton wide" />
      </div>
    </div>
  );
}

export default function ModelView({ modelState, onReload }) {
  const { status, data, error } = modelState;

  return (
    <div className="view">
      <header className="view-head">
        <div>
          <h1 className="view-title">Model di balik layar.</h1>
          <p className="view-subtitle">
            Angka di bawah diukur pada 20% data uji yang tidak dipakai saat
            pelatihan. Model memakai TF-IDF dan Multinomial Naive Bayes untuk
            membedakan pesan penipuan dari pesan biasa.
          </p>
        </div>
        <aside className="glance" aria-label="Sumber data model">
          <p className="glance-label">Dataset</p>
          <p className="glance-value" style={{ fontSize: '1.45rem', letterSpacing: '-0.03em' }}>
            {data?.dataset?.name || 'Indonesian SMS Spam'}
          </p>
          <div className="glance-row">
            <div>
              <div className="glance-metric-value">
                {data?.dataset?.name?.includes('Indonesian') ? 'Open Source' : 'UCI'}
              </div>
              <div className="glance-metric-label">Sumber</div>
            </div>
            <div>
              <div className="glance-metric-value">
                {data?.dataset?.name?.includes('Indonesian') ? 'Indonesia' : 'Inggris'}
              </div>
              <div className="glance-metric-label">Bahasa</div>
            </div>
          </div>
        </aside>
      </header>

      {status === 'loading' && <SkeletonState />}

      {status === 'error' && (
        <div className="model-error" role="alert">
          <h2 className="model-error-title">Informasi model tidak tersedia</h2>
          <p className="model-error-copy">{error}</p>
          <button type="button" className="secondary-button" onClick={onReload}>
            <RefreshIcon size={17} />
            Coba lagi
          </button>
        </div>
      )}

      {status === 'ready' && data && (
        <div className="model-layout">
          <div>
            <section className="accuracy-card" aria-label="Akurasi model">
              <p className="accuracy-label">Akurasi pada data uji</p>
              <p className="accuracy-number">{asPercent(data.accuracy / 100, 2)}</p>
              <p className="accuracy-caption">
                Dari {asNumber(data.test_size)} pesan uji, model menebak benar
                sebagian besar kasus. Recall lebih tinggi daripada presisi: model
                cenderung menandai pesan mencurigakan agar tidak lolos.
              </p>

              <div className="metric-strip">
                <div className="metric">
                  <div className="metric-value">
                    {asPercent(data.metrics?.precision / 100)}
                  </div>
                  <div className="metric-label">Presisi</div>
                </div>
                <div className="metric">
                  <div className="metric-value">
                    {asPercent(data.metrics?.recall / 100)}
                  </div>
                  <div className="metric-label">Recall</div>
                </div>
                <div className="metric">
                  <div className="metric-value">{asPercent(data.metrics?.f1 / 100)}</div>
                  <div className="metric-label">F1-score</div>
                </div>
              </div>
            </section>

            <div className="panel">
              <h2 className="section-heading">Spesifikasi pelatihan</h2>
              <p className="section-subcopy">
                Konfigurasi yang dipakai untuk menghasilkan model yang sedang
                melayani deteksi.
              </p>
              <div className="detail-list">
                <DetailRow label="Algoritma">{data.algorithm}</DetailRow>
                <DetailRow label="Vektor fitur">{data.vectorizer}</DetailRow>
                <DetailRow label="Data latih">{asNumber(data.train_size)} pesan</DetailRow>
                <DetailRow label="Data uji">{asNumber(data.test_size)} pesan</DetailRow>
                <DetailRow label="Pembagian">
                  {Math.round((1 - (data.split?.test_size ?? 0.2)) * 100)}% latih /{' '}
                  {Math.round((data.split?.test_size ?? 0.2) * 100)}% uji
                </DetailRow>
                <DetailRow label="Tanggal latih">
                  {asDate(data.training_date)}
                </DetailRow>
              </div>
            </div>
          </div>

          <div>
            <div className="panel">
              <h2 className="section-heading">Komposisi dataset</h2>
              <p className="section-subcopy">
                {asNumber(data.dataset?.name ? data.dataset.size : data.dataset_size)}{' '}
                pesan unik setelah {asNumber(data.dataset?.removed?.total)} duplikat
                dibuang. Spam hanya sebagian kecil dari korpus.
              </p>

              <div
                className="dataset-bar"
                role="img"
                aria-label={`${asNumber(data.dataset?.spam)} pesan penipuan dan ${asNumber(
                  data.dataset?.ham,
                )} pesan bukan penipuan`}
              >
                <span
                  className="dataset-segment spam"
                  style={{
                    width: `${((data.dataset?.spam ?? 0) / (data.dataset?.size || 1)) * 100}%`,
                  }}
                />
                <span
                  className="dataset-segment ham"
                  style={{
                    width: `${((data.dataset?.ham ?? 0) / (data.dataset?.size || 1)) * 100}%`,
                  }}
                />
              </div>
              <div className="dataset-legend">
                <span className="legend-item">
                  <span className="legend-swatch spam" aria-hidden="true" />
                  Penipuan: {asNumber(data.dataset?.spam)}
                </span>
                <span className="legend-item">
                  <span className="legend-swatch ham" aria-hidden="true" />
                  Bukan Penipuan: {asNumber(data.dataset?.ham)}
                </span>
              </div>
            </div>

            <div className="panel">
              <h2 className="section-heading">Matriks kebingungan</h2>
              <p className="section-subcopy">
                Setiap sel adalah jumlah pesan uji. Diagonal adalah tebakan yang
                benar.
              </p>

              <div className="confusion">
                <div className="confusion-grid">
                  <div className="confusion-cell correct">
                    <div className="confusion-value">
                      {asNumber(data.metrics?.confusion_matrix?.[0]?.[0])}
                    </div>
                    <div className="confusion-label">
                      Bukan Penipuan → Bukan Penipuan
                    </div>
                  </div>
                  <div className="confusion-cell">
                    <div className="confusion-value">
                      {asNumber(data.metrics?.confusion_matrix?.[0]?.[1])}
                    </div>
                    <div className="confusion-label">
                      Bukan Penipuan → Penipuan
                    </div>
                  </div>
                  <div className="confusion-cell">
                    <div className="confusion-value">
                      {asNumber(data.metrics?.confusion_matrix?.[1]?.[0])}
                    </div>
                    <div className="confusion-label">
                      Penipuan → Bukan Penipuan
                    </div>
                  </div>
                  <div className="confusion-cell correct">
                    <div className="confusion-value">
                      {asNumber(data.metrics?.confusion_matrix?.[1]?.[1])}
                    </div>
                    <div className="confusion-label">Penipuan → Penipuan</div>
                  </div>
                </div>
                <p className="confusion-note">
                  Baris pertama berisi pesan yang sebenarnya bukan penipuan; baris
                  kedua pesan penipuan.
                </p>
              </div>
            </div>

            <div className="panel">
              <h2 className="section-heading">Batas penggunaan</h2>
              <p className="section-subcopy">
                {data?.dataset?.name?.includes('Indonesian')
                  ? 'Model dilatih dengan SMS berbahasa Indonesia untuk mendeteksi penipuan online. Pola penipuan baru tetap memerlukan kehati-hatian pengguna.'
                  : 'Model dilatih sepenuhnya dengan SMS berbahasa Inggris dari UCI. Pesan berbahasa Indonesia belum menjadi bagian dari data pelatihan, sehingga hasilnya perlu dibaca sebagai sinyal awal.'}
              </p>
              <p className="confusion-note">
                Endpoint aktif: <span style={{ fontFamily: 'var(--font-mono)' }}>{API_BASE_URL}</span>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
