import { asPercent } from '../format';

const SEGMENTS = 24;

export default function ProbabilityBar({ label, value, tone }) {
  const safeValue = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  const percentage = Math.round(Math.min(1, Math.max(0, safeValue)) * 100);
  const filled = Math.round((percentage / 100) * SEGMENTS);

  return (
    <div className={`prob-item ${tone}`}>
      <div className="prob-head">
        <span className="prob-name">{label}</span>
        <span className="prob-value">{asPercent(safeValue)}</span>
      </div>
      <div
        className="segment-bar"
        role="progressbar"
        aria-label={`Probabilitas ${label}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percentage}
      >
        {Array.from({ length: SEGMENTS }, (_, index) => (
          <span
            key={index}
            className={`segment ${index < filled ? `filled ${tone}` : ''}`}
          />
        ))}
      </div>
    </div>
  );
}
