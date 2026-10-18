import { asDate } from '../format';
import { AlertIcon, CheckIcon, ClockIcon } from './Icons';

export default function ResultHead({ result, isFraud }) {
  return (
    <div className="result-head">
      <div className="result-verdict">
        <span className="verdict-icon">
          {isFraud ? <AlertIcon size={27} /> : <CheckIcon size={27} />}
        </span>
        <div>
          <h2 className="verdict-title">{result.label}</h2>
          <p className="verdict-desc">
            {isFraud
              ? 'Pesan ini menunjukkan ciri penipuan yang kuat. Jangan membalas, jangan buka tautannya, dan jangan kirim data pribadi.'
              : 'Model tidak menemukan indikasi penipuan yang kuat. Tetap berhati-hati jika pesan meminta uang atau data pribadi.'}
          </p>
        </div>
      </div>

      <div className="result-side">
        <span className="stamp">{isFraud ? 'Perlu waspada' : 'Tanpa indikasi'}</span>
        <span className="result-time">
          <ClockIcon size={14} />
          {asDate(result.createdAt)}
        </span>
      </div>
    </div>
  );
}
