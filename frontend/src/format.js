const percentFormatter = new Intl.NumberFormat('id-ID', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const numberFormatter = new Intl.NumberFormat('id-ID');

const dateFormatter = new Intl.DateTimeFormat('id-ID', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

/** 0.9787 -> "97,9%" */
export function asPercent(value, digits = 1) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—';
  const formatter =
    digits === 1
      ? percentFormatter
      : new Intl.NumberFormat('id-ID', {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        });
  return `${formatter.format(value * 100)}%`;
}

/** 5171 -> "5.171" */
export function asNumber(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—';
  return numberFormatter.format(value);
}

export function asDate(value) {
  if (!value) return '—';
  const date = typeof value === 'number' ? new Date(value) : new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return dateFormatter.format(date);
}
