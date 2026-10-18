
import { ArrowRightIcon } from './Icons';
import ProbabilityBar from './ProbabilityBar';
import ResultHead from './ResultHead';

export default function ResultPanel({ result, onReset, onHistory }) {
  const isFraud = result.label === 'Penipuan';
  const fraudProbability = result.probabilities?.Penipuan ?? 0;
  const hamProbability = result.probabilities?.['Bukan Penipuan'] ?? 0;

  return (
    <section
      className={`result-panel ${isFraud ? 'fraud' : 'safe'}`}
      aria-live="polite"
      id="hasil-deteksi"
    >
      <ResultHead result={result} isFraud={isFraud} />

      <div className="prob-section">
        <div className="prob-grid">
          <ProbabilityBar label="Penipuan" value={fraudProbability} tone="fraud" />
          <ProbabilityBar
            label="Bukan Penipuan"
            value={hamProbability}
            tone="safe"
          />
        </div>
      </div>

      <div className="result-details">
        <div>
          <p className="detail-label">Pesan yang diperiksa</p>
          <blockquote className="message-quote">{result.message}</blockquote>
        </div>
        <div>
          <p className="detail-label">Teks setelah pembersihan</p>
          <p className="processed-text">
            {result.processed_text || '(tidak ada teks tersisa setelah pembersihan)'}
          </p>
        </div>
      </div>

      <div className="result-actions">
        <button
          type="button"
          className="primary-button"
          onClick={onReset}
        >
          Periksa pesan lain
          <ArrowRightIcon size={17} />
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={onHistory}
        >
          Buka riwayat
        </button>
      </div>
    </section>
  );
}
