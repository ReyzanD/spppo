import { useCallback, useEffect, useState } from 'react';
import './App.css';
import { describeApiError, getHealth, getModelInfo } from './ApiService';
import Sidebar from './components/Sidebar';
import { WifiOffIcon } from './components/Icons';
import { useHistory } from './hooks/useHistory';
import DetectView from './views/DetectView';
import HistoryView from './views/HistoryView';
import ModelView from './views/ModelView';

export default function App() {
  const [view, setView] = useState('detect');
  const [health, setHealth] = useState({ status: 'checking', modelLoaded: false });
  const [modelState, setModelState] = useState({
    status: 'loading',
    data: null,
    error: null,
  });

  const { items, add, remove, clear } = useHistory();
  const [lastResult, setLastResult] = useState(() => items[0] ?? null);

  const loadModel = useCallback(async () => {
    setModelState({ status: 'loading', data: null, error: null });
    try {
      const data = await getModelInfo();
      setModelState({ status: 'ready', data, error: null });
    } catch (error) {
      setModelState({ status: 'error', data: null, error: describeApiError(error) });
    }
  }, []);

  useEffect(() => {
    let active = true;

    getModelInfo()
      .then((data) => {
        if (active) setModelState({ status: 'ready', data, error: null });
      })
      .catch((error) => {
        if (active) {
          setModelState({
            status: 'error',
            data: null,
            error: describeApiError(error),
          });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    const checkHealth = async () => {
      try {
        const data = await getHealth();
        if (active) {
          setHealth({ status: 'online', modelLoaded: Boolean(data.model_loaded) });
        }
      } catch {
        if (active) {
          setHealth({ status: 'offline', modelLoaded: false });
        }
      }
    };

    checkHealth();
    const interval = window.setInterval(checkHealth, 30000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const navigate = useCallback((nextView) => {
    setView(nextView);
    window.scrollTo(0, 0);
  }, []);

  const handleResult = useCallback(
    (entry) => {
      add(entry);
      setLastResult(entry);
    },
    [add],
  );

  const handleReset = useCallback(() => setLastResult(null), []);

  const handleOpen = useCallback(
    (item) => {
      setLastResult(item);
      navigate('detect');
    },
    [navigate],
  );

  const handleDelete = useCallback(
    (id) => {
      remove(id);
      setLastResult((current) => (current?.id === id ? null : current));
    },
    [remove],
  );

  const handleClear = useCallback(() => {
    clear();
    setLastResult(null);
  }, [clear]);

  const showOfflineBanner = health.status === 'offline';
  const showModelBanner =
    health.status === 'online' && !health.modelLoaded && modelState.status !== 'ready';

  return (
    <div className="app-shell">
      <Sidebar view={view} onNavigate={navigate} health={health} />

      <main className="main">
        {showOfflineBanner && (
          <div className="connection-banner" role="status">
            <WifiOffIcon size={18} />
            <span>
              API tidak terjangkau. Periksa koneksi dan pastikan server berjalan di
              port 8000.
            </span>
          </div>
        )}

        {showModelBanner && (
          <div className="connection-banner" role="status">
            <span>
              API aktif, tetapi model belum dimuat. Jalankan pelatihan model lalu
              mulai ulang API.
            </span>
          </div>
        )}

        {view === 'detect' && (
          <DetectView
            modelInfo={modelState.data}
            lastResult={lastResult}
            onResult={handleResult}
            onReset={handleReset}
            onHistory={() => navigate('history')}
          />
        )}

        {view === 'history' && (
          <HistoryView
            items={items}
            onOpen={handleOpen}
            onDelete={handleDelete}
            onClear={handleClear}
            onDetect={() => navigate('detect')}
          />
        )}

        {view === 'model' && (
          <ModelView modelState={modelState} onReload={loadModel} />
        )}
      </main>
    </div>
  );
}
