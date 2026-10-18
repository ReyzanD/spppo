import { asPercent } from '../format';
import { ArrowRightIcon, TrashIcon } from './Icons';

export default function HistoryDetail({ item, onOpen, onDelete }) {
  const isFraud = item.label === 'Penipuan';
  const probability =
    isFraud && item.probabilities?.Penipuan !== undefined
      ? item.probabilities.Penipuan
      : item.probabilities?.['Bukan Penipuan'];

  return (
    <li className="history-row">
      <span className={`history-verdict ${isFraud ? 'fraud' : 'safe'}`}>
        <span className="verdict-dot" aria-hidden="true" />
        {item.label}
      </span>

      <div>
        <p className="history-message">{item.message}</p>
        <p className="history-meta">
          <span>{item.createdAt ? new Date(item.createdAt).toLocaleString('id-ID', {
            day: '2-digit',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
          }) : '—'}</span>
          <span>Keyakinan {asPercent(probability)}</span>
        </p>
      </div>

      <div className="history-side">
        <button
          type="button"
          className="history-open"
          onClick={() => onOpen(item)}
        >
          Lihat
          <ArrowRightIcon size={15} />
        </button>
        <button
          type="button"
          className="icon-button"
          onClick={() => onDelete(item.id)}
          aria-label={`Hapus deteksi "${item.message.slice(0, 40)}"`}
        >
          <TrashIcon size={17} />
        </button>
      </div>
    </li>
  );
}
