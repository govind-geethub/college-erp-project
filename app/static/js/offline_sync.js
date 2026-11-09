/**
 * Offline Attendance Synchronization Engine
 * Handles classroom offline capture, local storage queueing,
 * idempotent batch submissions, and automatic background sync.
 */

const OfflineSync = {
  QUEUE_KEY: 'erp_offline_attendance_queue',
  SIMULATED_OFFLINE_KEY: 'erp_simulate_offline',

  init() {
    window.addEventListener('online', () => this.handleNetworkChange());
    window.addEventListener('offline', () => this.handleNetworkChange());
    this.updateStatusIndicator();
    // Check if there are pending items on startup
    if (this.isOnline()) {
      this.syncPendingQueue();
    }
  },

  isSimulatedOffline() {
    return localStorage.getItem(this.SIMULATED_OFFLINE_KEY) === 'true';
  },

  setSimulatedOffline(status) {
    localStorage.setItem(this.SIMULATED_OFFLINE_KEY, status ? 'true' : 'false');
    this.handleNetworkChange();
  },

  toggleSimulatedOffline() {
    const current = this.isSimulatedOffline();
    this.setSimulatedOffline(!current);
    return !current;
  },

  isOnline() {
    if (this.isSimulatedOffline()) {
      return false;
    }
    return navigator.onLine;
  },

  getQueue() {
    try {
      const raw = localStorage.getItem(this.QUEUE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.error('Error parsing sync queue:', e);
      return [];
    }
  },

  saveQueue(queue) {
    localStorage.setItem(this.QUEUE_KEY, JSON.stringify(queue));
    this.updateStatusIndicator();
  },

  enqueueAttendance(sessionPayload) {
    const queue = this.getQueue();
    // Ensure unique idempotent batch key
    if (!sessionPayload.client_batch_id) {
      sessionPayload.client_batch_id = 'CLIENT-QUEUE-' + Date.now() + '-' + Math.random().toString(36).substr(2, 6);
    }
    sessionPayload.queued_at = new Date().toISOString();
    sessionPayload.captured_offline = true;

    queue.push(sessionPayload);
    this.saveQueue(queue);
    this.updateStatusIndicator();
    return sessionPayload;
  },

  async syncPendingQueue() {
    if (!this.isOnline()) {
      return { synced: 0, pending: this.getQueue().length };
    }

    const queue = this.getQueue();
    if (queue.length === 0) {
      return { synced: 0, pending: 0 };
    }

    const remaining = [];
    let syncedCount = 0;

    for (const item of queue) {
      try {
        const response = await fetch('/api/attendance/submit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + (localStorage.getItem('erp_token') || '')
          },
          body: JSON.stringify(item)
        });

        if (response.ok) {
          syncedCount++;
        } else {
          // If server error or conflict, keep in queue
          remaining.push(item);
        }
      } catch (err) {
        console.warn('Sync failed for item, keeping in queue:', err);
        remaining.push(item);
      }
    }

    this.saveQueue(remaining);
    this.updateStatusIndicator();

    if (syncedCount > 0) {
      window.dispatchEvent(new CustomEvent('erp:sync_complete', {
        detail: { syncedCount, remainingCount: remaining.length }
      }));
    }

    return { synced: syncedCount, pending: remaining.length };
  },

  updateStatusIndicator() {
    const badge = document.getElementById('network-status-badge');
    if (!badge) return;

    const queue = this.getQueue();
    const online = this.isOnline();
    const simulated = this.isSimulatedOffline();

    if (!online) {
      badge.className = 'status-pill offline';
      badge.innerHTML = `
        <span class="status-dot offline"></span>
        <span>Offline ${simulated ? '(Weak Wi-Fi Sim)' : ''}</span>
        ${queue.length > 0 ? `<span class="queue-badge">${queue.length} Queued</span>` : ''}
      `;
    } else {
      badge.className = 'status-pill online';
      badge.innerHTML = `
        <span class="status-dot online"></span>
        <span>Online</span>
        ${queue.length > 0 ? `<span class="queue-badge warning">${queue.length} Pending Sync</span>` : ''}
      `;
    }
  },

  handleNetworkChange() {
    this.updateStatusIndicator();
    if (this.isOnline()) {
      this.syncPendingQueue();
    }
    window.dispatchEvent(new CustomEvent('erp:network_change', {
      detail: { online: this.isOnline() }
    }));
  }
};

window.OfflineSync = OfflineSync;
