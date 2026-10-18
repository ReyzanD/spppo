const base = {
  width: 22,
  height: 22,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
  focusable: false,
};

export function ShieldIcon({ size = 22 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M12 3l7 3v5c0 4.4-2.9 8.2-7 10-4.1-1.8-7-5.6-7-10V6l7-3z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

export function SearchIcon({ size = 22 }) {
  return (
    <svg {...base} width={size} height={size}>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M16 16l4 4" />
    </svg>
  );
}

export function HistoryIcon({ size = 22 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M4 12a8 8 0 1 0 2.3-5.6" />
      <path d="M4 4v4h4" />
      <path d="M12 8v4l3 2" />
    </svg>
  );
}

export function InfoIcon({ size = 22 }) {
  return (
    <svg {...base} width={size} height={size}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 11v5" />
      <path d="M12 8h.01" />
    </svg>
  );
}

export function ArrowRightIcon({ size = 20 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M4 12h15" />
      <path d="M13 6l6 6-6 6" />
    </svg>
  );
}

export function TrashIcon({ size = 19 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M4 7h16" />
      <path d="M9 7V5h6v2" />
      <path d="M6 7l1 13h10l1-13" />
      <path d="M10 11v5M14 11v5" />
    </svg>
  );
}

export function AlertIcon({ size = 22 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M12 3l9 17H3l9-17z" />
      <path d="M12 9v5" />
      <path d="M12 17h.01" />
    </svg>
  );
}

export function CheckIcon({ size = 22 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M4 12l5 5L20 6" />
    </svg>
  );
}

export function WifiOffIcon({ size = 22 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M3 8a16 16 0 0 1 18 0" />
      <path d="M6.5 11.5a11 11 0 0 1 11 0" />
      <path d="M10 15a5 5 0 0 1 4 0" />
      <path d="M12 19h.01" />
      <path d="M3 3l18 18" />
    </svg>
  );
}

export function RefreshIcon({ size = 18 }) {
  return (
    <svg {...base} width={size} height={size}>
      <path d="M20 11a8 8 0 1 0-2.3 5.6" />
      <path d="M20 4v7h-7" />
    </svg>
  );
}

export function ClockIcon({ size = 16 }) {
  return (
    <svg {...base} width={size} height={size}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 8v4l3 2" />
    </svg>
  );
}
