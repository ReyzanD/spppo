import { API_BASE_URL } from '../ApiService';
import { HistoryIcon, InfoIcon, SearchIcon, ShieldIcon } from './Icons';

const NAV_ITEMS = [
  { id: 'detect', label: 'Deteksi', icon: SearchIcon },
  { id: 'history', label: 'Riwayat', icon: HistoryIcon },
  { id: 'model', label: 'Model', icon: InfoIcon },
];

function statusLabel(health) {
  if (health.status === 'checking') return 'Menghubungi API';
  if (health.status === 'offline') return 'API tidak terjangkau';
  if (!health.modelLoaded) return 'Model belum dimuat';
  return 'API siap';
}

function statusClass(health) {
  if (health.status === 'offline') return 'offline';
  if (health.status === 'online' && health.modelLoaded) return 'online';
  return '';
}

export default function Sidebar({ view, onNavigate, health }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">
          <ShieldIcon size={23} />
        </span>
        <div>
          <div className="brand-name">Pesan Aman</div>
          <div className="brand-tagline">Pendeteksi pesan penipuan</div>
        </div>
      </div>

      <nav className="nav" aria-label="Navigasi utama">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              className={`nav-button ${view === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              aria-current={view === item.id ? 'page' : undefined}
            >
              <span className="nav-icon">
                <Icon size={19} />
              </span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="status-chip" title={API_BASE_URL}>
          <span className={`status-dot ${statusClass(health)}`} aria-hidden="true" />
          <span>{statusLabel(health)}</span>
        </div>
        <p className="sidebar-note">
          Riwayat disimpan di perangkat ini. Pesan hanya dikirim ke API untuk
          dianalisis dan tidak disimpan oleh server.
        </p>
      </div>
    </aside>
  );
}
