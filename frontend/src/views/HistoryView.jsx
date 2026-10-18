import { useState } from 'react';
import { HistoryIcon, ArrowRightIcon } from '../components/Icons';
import HistoryDetail from '../components/HistoryDetail';

export default function HistoryView({ items, onOpen, onDelete, onClear, onDetect }) {
  const [confirmingClear, setConfirmingClear] = useState(false);

  function handleClear() {
    onClear();
    setConfirmingClear(false);
  }

  return (
    <div className="view">
      <header className="view-head">
        <div>
          <h1 className="view-title">Riwayat deteksi.</h1>
          <p className="view-subtitle">
            Setiap pesan yang Anda periksa tersimpan di perangkat ini, lengkap
            dengan hasil dan peluangnya. Tidak ada yang dikirim ke server untuk
            disimpan.
          </p>
        </div>
        <aside className="glance" aria-label="Jumlah riwayat">
          <p className="glance-label">Pesan tersimpan di perangkat ini</p>
          <p className="glance-value">{items.length}</p>
        </aside>
      </header>

      {items.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">
            <HistoryIcon size={28} />
          </span>
          <h2 className="empty-title">Belum ada yang diperiksa</h2>
          <p className="empty-copy">
            Mulai dengan menempelkan satu pesan yang mencurigakan. Hasilnya
            akan muncul di sini dan tetap tersedia setelah halaman ditutup.
          </p>
          <button type="button" className="primary-button" onClick={onDetect}>
            Periksa pesan pertama
            <ArrowRightIcon size={17} />
          </button>
        </div>
      ) : (
        <>
          <div className="history-toolbar">
            <span className="history-count">
              {items.length} hasil deteksi, terbaru di atas
            </span>
            <div className="history-actions">
              {confirmingClear ? (
                <div className="confirm-row">
                  <span>Hapus seluruh riwayat?</span>
                  <button type="button" className="confirm-delete" onClick={handleClear}>
                    Ya, hapus
                  </button>
                  <button
                    type="button"
                    className="confirm-cancel"
                    onClick={() => setConfirmingClear(false)}
                  >
                    Batal
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  className="danger-text-button"
                  onClick={() => setConfirmingClear(true)}
                >
                  Hapus semua
                </button>
              )}
            </div>
          </div>

          <ul className="history-list">
            {items.map((item) => (
              <HistoryDetail
                key={item.id}
                item={item}
                onOpen={onOpen}
                onDelete={onDelete}
              />
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
