/**
 * Prerana College ERP - Core Application Controller
 * Handles SPA navigation, role-based controls, offline attendance,
 * internal mark moderation, AI NL queries, fee accounting, and compliance.
 */

const App = {
  currentRole: 'faculty',
  activeScreen: 'dashboard',
  roster: [],
  marksSheet: null,

  init() {
    // 1. Setup offline sync engine
    OfflineSync.init();

    // 2. Setup role switcher listener
    const roleSelect = document.getElementById('role-switcher');
    if (roleSelect) {
      roleSelect.value = this.currentRole;
      roleSelect.addEventListener('change', (e) => {
        this.currentRole = e.target.value;
        this.showToast(`Switched active role to: ${e.target.options[e.target.selectedIndex].text}`);
        this.adaptRolePermissions();
      });
    }

    // 3. Setup navigation click handlers
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const screen = item.getAttribute('data-screen');
        if (screen) this.navigateTo(screen);
      });
    });

    // 4. Setup simulated offline toggle button
    const simBtn = document.getElementById('btn-toggle-offline');
    if (simBtn) {
      simBtn.addEventListener('click', () => {
        const isOffline = OfflineSync.toggleSimulatedOffline();
        simBtn.textContent = isOffline ? '📶 Reconnect' : '📶 Sim Offline';
        this.showToast(isOffline ? 'Weak Classroom Wi-Fi simulated: Offline Mode active' : 'Network restored: Online Mode active');
        this.updateOfflineUI();
      });
    }

    // 5. Setup today date
    const dateInput = document.getElementById('att-session-date');
    if (dateInput) {
      dateInput.value = new Date().toISOString().split('T')[0];
    }

    // 6. Listen for sync events
    window.addEventListener('erp:sync_complete', (e) => {
      this.showToast(`Synced ${e.detail.syncedCount} queued attendance session(s) to server.`);
      this.loadDashboardData();
      this.updateOfflineUI();
    });

    // 7. Initial data loads
    this.navigateTo('dashboard');
    this.loadMastersData();
    this.updateOfflineUI();
  },

  navigateTo(screenId) {
    this.activeScreen = screenId;
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const targetScreen = document.getElementById(`screen-${screenId}`);
    if (targetScreen) targetScreen.classList.add('active');

    const targetNav = document.querySelector(`.nav-item[data-screen="${screenId}"]`);
    if (targetNav) targetNav.classList.add('active');

    // Route-specific data refresh
    if (screenId === 'dashboard') this.loadDashboardData();
    if (screenId === 'attendance') this.loadRosterForAttendance();
    if (screenId === 'marks') this.loadMarksSheet();
    if (screenId === 'fees') this.loadFeesData();
    if (screenId === 'ai') this.loadAtRiskList();
    if (screenId === 'reports') this.loadReportsData();
    if (screenId === 'students') this.loadStudentsDirectory();
  },

  adaptRolePermissions() {
    const isModerator = this.currentRole === 'exam_moderator' || this.currentRole === 'office_admin';
    const lockBtn = document.getElementById('btn-toggle-lock');
    if (lockBtn) {
      lockBtn.style.display = isModerator ? 'inline-flex' : 'none';
    }
  },

  updateOfflineUI() {
    const queue = OfflineSync.getQueue();
    const countSpan = document.getElementById('offline-queue-count');
    if (countSpan) countSpan.textContent = queue.length;
  },

  showToast(msg) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 200);
    }, 3200);
  },

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('active');
  },

  // =========================================================================
  // 1. DASHBOARD
  // =========================================================================
  async loadDashboardData() {
    try {
      const res = await fetch('/api/reports/kpi-dashboard');
      const data = await res.json();
      
      const attRateEl = document.getElementById('stat-attendance-rate');
      if (attRateEl) attRateEl.textContent = `${data.kpi_same_day_attendance_rate}%`;
      const attendanceStatusEl = document.getElementById('stat-attendance-status');
      if (attendanceStatusEl) {
        attendanceStatusEl.textContent = `Target >${data.kpi_same_day_target} (${data.kpi_attendance_success ? 'Met' : 'Not Met'}) • 0 paper logs`;
      }

      // Load at-risk alerts table
      const riskRes = await fetch('/api/ai/at-risk-students');
      const atRiskData = await riskRes.json();

      const riskCountEl = document.getElementById('stat-risk-count');
      const navRiskCount = document.getElementById('nav-risk-count');
      if (riskCountEl) riskCountEl.textContent = `${atRiskData.length} Flagged`;
      if (navRiskCount) navRiskCount.textContent = atRiskData.length;

      const tbody = document.getElementById('dashboard-alerts-body');
      if (tbody) {
        tbody.innerHTML = atRiskData.map(s => `
          <tr>
            <td><strong>${s.roll_no}</strong></td>
            <td>${s.name}</td>
            <td>${s.programme} (Yr ${s.year})</td>
            <td>
              <span class="badge ${s.attendance_pct < 75 ? 'badge-danger' : 'badge-warning'}">
                ${s.attendance_pct}%
              </span>
            </td>
            <td>
              <span class="badge ${s.internal_marks < 24 ? 'badge-warning' : 'badge-success'}">
                ${s.internal_marks} / 40
              </span>
            </td>
            <td>${s.fee_due > 0 ? `<span style="color: var(--danger); font-weight: 600;">₹${s.fee_due.toLocaleString()}</span>` : '₹0'}</td>
            <td style="font-size: 12px; color: var(--text-muted);">${s.triggers.join(', ')}</td>
            <td>
              ${s.attendance_pct < 75 ? `
                <button class="btn btn-secondary btn-sm" onclick="App.triggerParentAlert(${s.student_id}, 'ATTENDANCE_SHORTAGE')">
                  📲 Alert Parent
                </button>
              ` : (s.fee_due > 0 ? `
                <button class="btn btn-secondary btn-sm" onclick="App.triggerParentAlert(${s.student_id}, 'FEE_DUE')">
                  📲 Alert Parent
                </button>
              ` : '<span class="badge badge-neutral">No matching alert</span>')}
            </td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.warn('Dashboard load error:', e);
    }
  },

  // =========================================================================
  // 2. MASTERS
  // =========================================================================
  async loadMastersData() {
    try {
      const [progRes, batchRes, subjRes] = await Promise.all([
        fetch('/api/masters/programmes'),
        fetch('/api/masters/batches'),
        fetch('/api/masters/subjects')
      ]);
      const programmes = await progRes.json();
      const batches = await batchRes.json();
      const subjects = await subjRes.json();

      const pList = document.getElementById('masters-programmes-list');
      if (pList) {
        pList.innerHTML = programmes.map(p => `
          <li style="padding: 8px 0; border-bottom: 1px solid var(--border-light);">
            <strong>${p.code}</strong> - ${p.name}
            <div style="font-size: 11px; color: var(--text-muted);">${p.degree_type} &bull; ${p.duration_years} Years &bull; Annual Tuition: ₹${p.annual_tuition.toLocaleString()}</div>
          </li>
        `).join('');
      }

      const bList = document.getElementById('masters-batches-list');
      if (bList) {
        bList.innerHTML = batches.map(b => `
          <li style="padding: 8px 0; border-bottom: 1px solid var(--border-light);">
            <strong>Batch ${b.name}</strong> (Section ${b.section})
            <div style="font-size: 11px; color: var(--text-muted);">Year ${b.academic_year} &bull; Semester ${b.current_semester}</div>
          </li>
        `).join('');
      }

      const sList = document.getElementById('masters-subjects-list');
      if (sList) {
        sList.innerHTML = subjects.map(s => `
          <li style="padding: 8px 0; border-bottom: 1px solid var(--border-light);">
            <strong>${s.code}</strong>: ${s.name}
            <div style="font-size: 11px; color: var(--text-muted);">${s.credits} Credits &bull; Max Internal Marks: ${s.max_internal_marks}</div>
          </li>
        `).join('');
      }
    } catch (e) {
      console.warn('Masters load error:', e);
    }
  },

  // =========================================================================
  // 3. MOBILE ATTENDANCE (<30 SECONDS ROLL CALL + OFFLINE SYNC)
  // =========================================================================
  async loadRosterForAttendance() {
    try {
      const subjectSelect = document.getElementById('att-subject-select');
      const subjectId = parseInt(subjectSelect.value, 10);
      const batchId = (subjectId === 3) ? 2 : ((subjectId === 4) ? 3 : 1);

      const res = await fetch(`/api/attendance/batch-roster?batch_id=${batchId}`);
      this.roster = await res.json();
      this.renderAttendanceRoster();
    } catch (e) {
      console.warn('Roster load error:', e);
    }
  },

  renderAttendanceRoster() {
    const container = document.getElementById('attendance-roster-container');
    if (!container) return;

    if (this.roster.length === 0) {
      container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted);">No students enrolled in this batch.</div>';
      return;
    }

    container.innerHTML = this.roster.map((s, idx) => `
      <div class="student-att-card ${s.status === 'Absent' ? 'absent' : (s.status === 'Late' ? 'late' : 'present')}" id="att-card-${s.student_id}">
        <div>
          <div style="font-weight: 600; font-size: 14px;">${s.name}</div>
          <div style="font-size: 12px; color: var(--text-muted);">
            ${s.roll_no} &bull; Cum. Attendance: 
            <span class="badge ${s.attendance_pct < 75 ? 'badge-danger' : 'badge-success'}">${s.attendance_pct}%</span>
          </div>
        </div>

        <div class="att-toggles">
          <button type="button" class="att-btn present ${(!s.status || s.status === 'Present') ? 'active present' : ''}" 
                  onclick="App.setStudentStatus(${s.student_id}, 'Present')">P</button>
          <button type="button" class="att-btn late ${s.status === 'Late' ? 'active late' : ''}" 
                  onclick="App.setStudentStatus(${s.student_id}, 'Late')">L</button>
          <button type="button" class="att-btn absent ${s.status === 'Absent' ? 'active absent' : ''}" 
                  onclick="App.setStudentStatus(${s.student_id}, 'Absent')">A</button>
        </div>
      </div>
    `).join('');
  },

  setStudentStatus(studentId, status) {
    const student = this.roster.find(s => s.student_id === studentId);
    if (student) {
      student.status = status;
      this.renderAttendanceRoster();
    }
  },

  markAllPresent() {
    this.roster.forEach(s => s.status = 'Present');
    this.renderAttendanceRoster();
    this.showToast('All students marked Present (1-tap)');
  },

  async submitAttendanceSession() {
    const subjectSelect = document.getElementById('att-subject-select');
    const subjectId = parseInt(subjectSelect.value, 10);
    const batchId = (subjectId === 3) ? 2 : ((subjectId === 4) ? 3 : 1);
    const dateVal = document.getElementById('att-session-date').value;
    const periodVal = parseInt(document.getElementById('att-period-select').value, 10);

    const records = this.roster.map(s => ({
      student_id: s.student_id,
      status: s.status || 'Present',
      remarks: null
    }));

    const clientBatchId = `SYNC-BATCH-${subjectId}-${dateVal.replace(/-/g, '')}-P${periodVal}-${Date.now()}`;

    const payload = {
      client_batch_id: clientBatchId,
      subject_id: subjectId,
      batch_id: batchId,
      session_date: dateVal,
      period: periodVal,
      records: records,
      captured_offline: !OfflineSync.isOnline()
    };

    if (!OfflineSync.isOnline()) {
      OfflineSync.enqueueAttendance(payload);
      this.showToast('📶 Offline: Attendance saved locally in offline queue. Will sync automatically when connected.');
      this.updateOfflineUI();
      return;
    }

    try {
      const res = await fetch('/api/attendance/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const errorData = await res.json();
        const detail = Array.isArray(errorData.detail)
          ? errorData.detail.map(error => error.msg).join(', ')
          : errorData.detail;
        this.showToast(`Attendance save failed: ${detail || `HTTP ${res.status}`}`);
        return;
      }
      const data = await res.json();
      this.showToast(`Attendance saved! Marked ${data.present_count} present, ${data.absent_count} absent.`);

      if (data.shortage_alerts_triggered && data.shortage_alerts_triggered.length > 0) {
        this.showToast(`🚨 Shortage Alert (<75%): Automated notice sent to parent of ${data.shortage_alerts_triggered[0].name}`);
      }
      this.loadDashboardData();
    } catch (err) {
      // Fallback to queue on unexpected network fail
      OfflineSync.enqueueAttendance(payload);
      this.showToast('Saved to offline sync queue due to connection interruption.');
      this.updateOfflineUI();
    }
  },

  async syncOfflineQueue() {
    const res = await OfflineSync.syncPendingQueue();
    if (res.synced > 0) {
      this.showToast(`Successfully synced ${res.synced} offline session(s)!`);
      this.updateOfflineUI();
      this.loadDashboardData();
    } else if (res.pending > 0) {
      this.showToast(`Could not sync: Device still offline (${res.pending} pending).`);
    } else {
      this.showToast('No pending offline sessions to sync.');
    }
  },

  // =========================================================================
  // 4. INTERNAL MARKS & MODERATION LOCK
  // =========================================================================
  async loadMarksSheet() {
    try {
      const subjectSelect = document.getElementById('marks-subject-select');
      const subjectId = parseInt(subjectSelect.value, 10);
      const batchId = (subjectId === 3) ? 2 : ((subjectId === 4) ? 3 : 1);

      const res = await fetch(`/api/marks/sheet?subject_id=${subjectId}&batch_id=${batchId}`);
      this.marksSheet = await res.json();

      const badge = document.getElementById('marks-moderation-badge');
      const lockBtn = document.getElementById('btn-toggle-lock');
      const saveBtn = document.getElementById('btn-save-marks');

      if (this.marksSheet.is_locked) {
        badge.className = 'badge badge-success';
        badge.textContent = '🔒 Moderated & Locked';
        if (lockBtn) lockBtn.textContent = '🔓 Unlock for Revision';
        if (saveBtn) saveBtn.disabled = true;
      } else {
        badge.className = 'badge badge-warning';
        badge.textContent = '📝 Draft / Unlocked';
        if (lockBtn) lockBtn.textContent = '🔒 Submit & Lock Moderation';
        if (saveBtn) saveBtn.disabled = false;
      }

      const tbody = document.getElementById('marks-sheet-body');
      if (tbody) {
        tbody.innerHTML = this.marksSheet.students.map(s => `
          <tr id="mark-row-${s.student_id}">
            <td><strong>${s.roll_no}</strong></td>
            <td>${s.name}</td>
            <td>
              <input type="number" min="0" max="20" step="0.5" class="form-control mark-input" 
                     id="midterm-${s.student_id}" value="${s.midterm_score}" 
                     ${s.is_locked ? 'disabled' : ''}
                     onchange="App.calcRowTotal(${s.student_id})" style="width: 80px;">
            </td>
            <td>
              <input type="number" min="0" max="10" step="0.5" class="form-control mark-input" 
                     id="quiz-${s.student_id}" value="${s.quiz_score}" 
                     ${s.is_locked ? 'disabled' : ''}
                     onchange="App.calcRowTotal(${s.student_id})" style="width: 80px;">
            </td>
            <td>
              <input type="number" min="0" max="10" step="0.5" class="form-control mark-input" 
                     id="assign-${s.student_id}" value="${s.assignment_score}" 
                     ${s.is_locked ? 'disabled' : ''}
                     onchange="App.calcRowTotal(${s.student_id})" style="width: 80px;">
            </td>
            <td>
              <strong id="total-${s.student_id}">${s.total_score}</strong> / 40
            </td>
            <td>
              <span class="badge ${s.is_pass ? 'badge-success' : 'badge-danger'}">
                ${s.is_pass ? 'PASS' : 'FAIL'}
              </span>
            </td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="App.viewExamAudit(${s.student_id})">
                📜 Logs
              </button>
            </td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.warn('Marks sheet load error:', e);
    }
  },

  calcRowTotal(studentId) {
    const mid = parseFloat(document.getElementById(`midterm-${studentId}`).value) || 0;
    const quiz = parseFloat(document.getElementById(`quiz-${studentId}`).value) || 0;
    const assign = parseFloat(document.getElementById(`assign-${studentId}`).value) || 0;
    const totalEl = document.getElementById(`total-${studentId}`);
    if (totalEl) {
      totalEl.textContent = (mid + quiz + assign).toFixed(1);
    }
  },

  async saveMarksSheet() {
    if (!this.marksSheet) return;
    const subjectId = this.marksSheet.subject_id;

    const updates = this.marksSheet.students.filter(s => !s.is_locked).map(s => {
      const mid = parseFloat(document.getElementById(`midterm-${s.student_id}`).value) || 0;
      const quiz = parseFloat(document.getElementById(`quiz-${s.student_id}`).value) || 0;
      const assign = parseFloat(document.getElementById(`assign-${s.student_id}`).value) || 0;
      return {
        student_id: s.student_id,
        midterm_score: mid,
        quiz_score: quiz,
        assignment_score: assign,
        change_reason: 'Regular marks update'
      };
    });

    try {
      const res = await fetch('/api/marks/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_id: subjectId, marks: updates })
      });
      if (res.ok) {
        this.showToast('Internal marks updated and logged to exam audit trail!');
        this.loadMarksSheet();
      } else {
        const err = await res.json();
        alert('Error saving marks: ' + (err.detail || 'Access Denied'));
      }
    } catch (e) {
      alert('Error updating marks');
    }
  },

  async handleModerationAction() {
    if (!this.marksSheet) return;
    const isCurrentlyLocked = this.marksSheet.is_locked;
    const action = isCurrentlyLocked ? 'UNLOCK' : 'LOCK';
    const reason = prompt(`Enter reason for ${action}ing internal marks:`, isCurrentlyLocked ? 'Administrative revision requested' : 'Academic Committee verification');
    if (!reason) return;

    try {
      const res = await fetch('/api/marks/moderation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject_id: this.marksSheet.subject_id,
          batch_id: this.marksSheet.batch_id,
          action: action,
          reason: reason
        })
      });
      if (res.ok) {
        this.showToast(`Moderation state updated to: ${action}ED`);
        this.loadMarksSheet();
      }
    } catch (e) {
      alert('Error updating moderation status');
    }
  },

  async viewExamAudit(studentId) {
    try {
      const res = await fetch(`/api/marks/audit-logs?subject_id=${this.marksSheet ? this.marksSheet.subject_id : 1}`);
      const logs = await res.json();
      const filtered = logs.filter(l => l.student_id === studentId);

      const modal = document.getElementById('audit-modal');
      const content = document.getElementById('audit-log-content');
      
      if (filtered.length === 0) {
        content.innerHTML = '<p style="color: var(--text-muted);">No audit change records for this student.</p>';
      } else {
        content.innerHTML = `
          <ul style="list-style: none;">
            ${filtered.map(l => `
              <li style="padding: 10px 0; border-bottom: 1px solid var(--border-light);">
                <div style="display: flex; justify-content: space-between;">
                  <strong>Action: ${l.action_type}</strong>
                  <span style="font-size: 11px; color: var(--text-muted);">${l.timestamp}</span>
                </div>
                <div>Actor: <em>${l.actor_username}</em> (${l.actor_role})</div>
                <div>Mark Change: Total ${l.old_total !== null ? l.old_total : '--'} &rarr; ${l.new_total}</div>
                <div style="color: var(--text-muted); font-size: 12px;">Reason: ${l.reason || 'None provided'}</div>
              </li>
            `).join('')}
          </ul>
        `;
      }
      modal.classList.add('active');
    } catch (e) {
      alert('Could not load audit log');
    }
  },

  exportUniversityCSV() {
    if (!this.marksSheet) return;
    window.location.href = `/api/marks/export-university-csv?subject_id=${this.marksSheet.subject_id}&batch_id=${this.marksSheet.batch_id}`;
  },

  // =========================================================================
  // 5. FEES & TALLY RECONCILIATION
  // =========================================================================
  async loadFeesData() {
    try {
      const res = await fetch('/api/fees/ledgers');
      const ledgers = await res.json();

      const tbody = document.getElementById('fees-ledger-body');
      if (tbody) {
        tbody.innerHTML = ledgers.map(l => `
          <tr>
            <td><strong>${l.roll_no}</strong></td>
            <td>${l.student_name}</td>
            <td>${l.programme_name} (Yr ${l.year})</td>
            <td>₹${l.total_fee.toLocaleString()}</td>
            <td>${l.scholarship_discount > 0 ? `₹${l.scholarship_discount.toLocaleString()}` : '₹0'}</td>
            <td><strong>₹${l.net_payable.toLocaleString()}</strong></td>
            <td>₹${l.paid_amount.toLocaleString()}</td>
            <td>
              <strong style="color: ${l.due_amount > 0 ? 'var(--danger)' : 'var(--success)'};">
                ₹${l.due_amount.toLocaleString()}
              </strong>
            </td>
            <td>
              <span class="badge ${l.status === 'Paid' ? 'badge-success' : 'badge-warning'}">
                ${l.status}
              </span>
            </td>
            <td>
              <span class="badge badge-neutral">${l.reconciliation_status}</span>
            </td>
            <td>
              ${l.due_amount > 0 ? `
                <button class="btn btn-primary btn-sm" onclick="App.openPaymentModal(${l.student_id}, '${l.student_name}', ${l.due_amount})">
                  💳 Pay Fee
                </button>
              ` : `
                <span style="font-size: 12px; color: var(--success); font-weight: 600;">Settled</span>
              `}
            </td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.warn('Fees load error:', e);
    }
  },

  openPaymentModal(studentId, name, due) {
    document.getElementById('modal-student-id').value = studentId;
    document.getElementById('modal-student-name').value = name;
    document.getElementById('modal-due-amount').value = `₹${due.toLocaleString()}`;
    document.getElementById('modal-pay-amount').value = due;
    document.getElementById('payment-modal').classList.add('active');
  },

  async submitMockPayment() {
    const studentId = parseInt(document.getElementById('modal-student-id').value, 10);
    const amount = parseFloat(document.getElementById('modal-pay-amount').value);
    const mode = document.getElementById('modal-pay-mode').value;

    try {
      const res = await fetch('/api/fees/mock-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          amount: amount,
          payment_mode: mode
        })
      });

      if (res.ok) {
        const data = await res.json();
        this.closeModal('payment-modal');
        this.showToast(`Receipt Generated: ${data.receipt_no}! Instant reconciliation completed via Tally XML.`);
        this.loadFeesData();
      } else {
        const err = await res.json();
        alert('Payment error: ' + (err.detail || 'Invalid amount'));
      }
    } catch (e) {
      alert('Payment processing failed');
    }
  },

  exportTallyXML() {
    window.location.href = '/api/fees/export-tally-xml';
  },

  exportFeeCSV() {
    window.location.href = '/api/fees/export-csv';
  },

  // =========================================================================
  // 6. AI QUERY ASSISTANT & AT-RISK ENGINE
  // =========================================================================
  setAIQuery(q) {
    const input = document.getElementById('ai-query-input');
    if (input) {
      input.value = q;
      this.executeAIQuery();
    }
  },

  async executeAIQuery() {
    const input = document.getElementById('ai-query-input');
    const prompt = input.value.trim();
    if (!prompt) return;

    try {
      const res = await fetch('/api/ai/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();

      const container = document.getElementById('ai-response-container');
      container.style.display = 'block';

      const safetyBadge = document.getElementById('ai-safety-badge');
      if (data.safety_audit.includes('BLOCKED')) {
        safetyBadge.className = 'badge badge-danger';
        safetyBadge.textContent = 'BLOCKED (Write/DDL Mutation Prevented)';
      } else {
        safetyBadge.className = 'badge badge-success';
        safetyBadge.textContent = 'PASSED (Read-only verified, Scoped)';
      }

      document.getElementById('ai-execution-stats').textContent = `${data.row_count} rows &bull; ${data.execution_time_ms}ms latency`;
      document.getElementById('ai-interpretation').textContent = data.interpretation;
      document.getElementById('ai-filter-summary').textContent = data.generated_filter_summary;
      document.getElementById('ai-sql-code').textContent = data.read_only_sql;

      // Render results table
      const head = document.getElementById('ai-results-head');
      const body = document.getElementById('ai-results-body');

      if (data.results.length === 0) {
        head.innerHTML = '';
        body.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">No rows matching these exact criteria.</td></tr>`;
      } else {
        const keys = ['roll_no', 'name', 'programme', 'attendance_pct', 'internal_marks_of_40', 'fee_due_inr'];
        head.innerHTML = `<tr>
          <th>Roll No</th>
          <th>Name</th>
          <th>Programme</th>
          <th>Attendance %</th>
          <th>Internal Marks (40)</th>
          <th>Fee Due (₹)</th>
        </tr>`;

        body.innerHTML = data.results.map(r => `
          <tr>
            <td><strong>${r.roll_no}</strong></td>
            <td>${r.name}</td>
            <td>${r.programme} (Yr ${r.year})</td>
            <td><span class="badge ${r.attendance_pct < 75 ? 'badge-danger' : 'badge-success'}">${r.attendance_pct}%</span></td>
            <td>${r.internal_marks_of_40} / 40</td>
            <td>${r.fee_due_inr > 0 ? `₹${r.fee_due_inr.toLocaleString()}` : '₹0'}</td>
          </tr>
        `).join('');
      }
    } catch (e) {
      alert('AI Query execution error');
    }
  },

  async loadAtRiskList() {
    try {
      const [riskRes, taskRes] = await Promise.all([
        fetch('/api/ai/at-risk-students'),
        fetch('/api/ai/mentor-tasks')
      ]);
      const atRiskData = await riskRes.json();
      const tasks = await taskRes.json();

      const tbody = document.getElementById('at-risk-table-body');
      if (tbody) {
        tbody.innerHTML = atRiskData.map(s => {
          const task = tasks.find(t => t.student_id === s.student_id);
          return `
            <tr>
              <td><strong>${s.roll_no}</strong></td>
              <td>${s.name}</td>
              <td>
                <span class="badge ${s.risk_level === 'HIGH' ? 'badge-danger' : 'badge-warning'}">
                  ${s.risk_level} RISK
                </span>
              </td>
              <td><strong>${s.risk_score} / 100</strong></td>
              <td style="font-size: 12px; color: var(--text-muted);">${s.triggers.join('; ')}</td>
              <td style="font-size: 12px;">
                <strong>${task ? task.title : 'Mentor Counseling Task'}</strong><br>
                <span style="color: var(--text-muted);">${task ? task.recommended_action : ''}</span>
              </td>
              <td>
                ${task && task.status === 'Completed' ? `
                  <span class="badge badge-success">Completed</span>
                ` : `
                  <button class="btn btn-secondary btn-sm" onclick="App.resolveMentorTask(${task ? task.id : 1})">
                    ✓ Complete Counseling
                  </button>
                `}
              </td>
            </tr>
          `;
        }).join('');
      }
    } catch (e) {
      console.warn('At-risk load error:', e);
    }
  },

  async triggerRiskScan() {
    await this.loadAtRiskList();
    this.showToast('At-Risk Indicators re-scanned across campus.');
  },

  async resolveMentorTask(taskId) {
    try {
      const res = await fetch(`/api/ai/mentor-tasks/${taskId}/resolve`, { method: 'POST' });
      if (res.ok) {
        this.showToast('Mentor Task resolved and logged to student file.');
        this.loadAtRiskList();
      }
    } catch (e) {
      alert('Failed to resolve mentor task');
    }
  },

  // =========================================================================
  // 7. REPORTS & BILINGUAL ODIA NOTIFICATIONS
  // =========================================================================
  async loadReportsData() {
    try {
      const [naacRes, aicteRes, notifRes] = await Promise.all([
        fetch('/api/reports/naac-criterion-2'),
        fetch('/api/reports/aicte-disclosure'),
        fetch('/api/notifications/logs')
      ]);
      const naac = await naacRes.json();
      const aicte = await aicteRes.json();
      const notifs = await notifRes.json();

      const naacList = document.getElementById('naac-metrics-list');
      if (naacList) {
        naacList.innerHTML = naac.metrics.map(m => `
          <div style="padding: 8px 0; border-bottom: 1px solid var(--border-light);">
            <strong>Metric ${m.metric_id}: ${m.title}</strong>
            <div style="color: var(--primary); font-weight: 600;">${m.value}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${m.status}</div>
          </div>
        `).join('');
      }

      const aicteList = document.getElementById('aicte-disclosure-list');
      if (aicteList) {
        aicteList.innerHTML = aicte.programmes.map(p => `
          <div style="padding: 8px 0; border-bottom: 1px solid var(--border-light);">
            <strong>${p.programme_name} (${p.programme_code})</strong>
            <div style="font-size: 12px; color: var(--text-muted);">
              Approved Duration: ${p.duration_years} Years &bull; Active Enrolment: ${p.current_enrollment} &bull; Tuition: ₹${p.annual_tuition.toLocaleString()}
            </div>
          </div>
        `).join('');
      }

      const notifBody = document.getElementById('notifications-table-body');
      if (notifBody) {
        notifBody.innerHTML = notifs.map(n => `
          <tr>
            <td>
              <strong>${n.student_name}</strong><br>
              <span style="font-size: 11px; color: var(--text-muted);">${n.student_roll}</span>
            </td>
            <td>${n.parent_phone}</td>
            <td><span class="badge badge-neutral">${n.channel}</span></td>
            <td style="font-size: 12px; max-width: 280px;">${n.message_text_en}</td>
            <td style="font-size: 12px; max-width: 280px; font-family: sans-serif; color: #1e3a8a;">
              ${n.message_text_or}
            </td>
            <td><span class="badge badge-success">${n.status}</span></td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.warn('Reports load error:', e);
    }
  },

  async triggerParentAlert(studentId, triggerType) {
    try {
      const res = await fetch('/api/notifications/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, trigger_type: triggerType })
      });
      if (!res.ok) {
        const errorData = await res.json();
        const detail = Array.isArray(errorData.detail)
          ? errorData.detail.map(error => error.msg).join(', ')
          : errorData.detail;
        this.showToast(`Alert dispatch failed: ${detail || `HTTP ${res.status}`}`);
        return;
      }

      this.showToast('Mock bilingual parent notification recorded (English + Odia).');
      this.loadReportsData();
    } catch (e) {
      console.error('Parent alert dispatch error:', e);
      this.showToast(`Alert dispatch failed: ${e.message}`);
    }
  },

  // =========================================================================
  // 8. STUDENT DIRECTORY & DPDP 2023
  // =========================================================================
  async loadStudentsDirectory() {
    try {
      const res = await fetch('/api/students');
      const students = await res.json();

      const tbody = document.getElementById('students-directory-body');
      if (tbody) {
        tbody.innerHTML = students.map(s => `
          <tr>
            <td><strong>${s.roll_no}</strong></td>
            <td>${s.name}</td>
            <td>${s.programme_code}</td>
            <td>Yr ${s.current_year} (Sem ${s.current_semester})</td>
            <td>
              <span class="badge ${s.attendance_pct < 75 ? 'badge-danger' : 'badge-success'}">
                ${s.attendance_pct}%
              </span>
            </td>
            <td>${s.internal_marks_total} / 40</td>
            <td>${s.fee_due > 0 ? `₹${s.fee_due.toLocaleString()}` : '₹0'}</td>
            <td>
              ${s.is_minor ? `
                <span class="badge badge-warning">Minor (&lt;18) &bull; Consent Granted</span>
              ` : `
                <span class="badge badge-neutral">Major (&ge;18)</span>
              `}
            </td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="App.viewStudentProfile(${s.id})">
                Profile
              </button>
            </td>
          </tr>
        `).join('');
      }
    } catch (e) {
      console.warn('Students directory load error:', e);
    }
  },

  async viewStudentProfile(studentId) {
    try {
      const res = await fetch(`/api/students/${studentId}`);
      const s = await res.json();
      alert(`Student Profile: ${s.name} (${s.roll_no})\nProgramme: ${s.programme}\nParent: ${s.parent_name} (${s.parent_phone})\nDPDP Consent Status: ${s.dpdp_consent_status}\nAttendance: ${s.attendance.percentage}%\nOutstanding Fee: ₹${s.fee_ledger.due_amount}`);
    } catch (e) {
      alert('Could not load student profile');
    }
  }
};

window.App = App;

// Bootstrap on DOM loaded
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
