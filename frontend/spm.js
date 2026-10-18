const byId = (id) => document.getElementById(id);
const SPM = { requirements: [], tasks: [], risks: [], team: [], changes: [], metrics: {} };
const STATUSES = ['To Do', 'In Progress', 'Testing / Review', 'Done'];
let toastTimeout;
const escapeText = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatDate = (v) => v ? String(v).slice(0, 10) : '—';
const badgeClass = (v) => String(v ?? '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const money = (v) => new Intl.NumberFormat('en-IN', {style:'currency', currency:'INR', maximumFractionDigits:0}).format(Number(v || 0));

async function spmApi(url, options = {}) {
  const response = await fetch(url, {headers:{'Content-Type':'application/json'}, ...options});
  let body = {};
  try { body = await response.json(); } catch { body = {}; }
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status}).`);
  return body;
}
function showToast(message, isError = false) {
  const el = byId('spmToast'); if (!el) return;
  el.textContent = message; el.className = `toast show${isError ? ' error' : ''}`;
  clearTimeout(toastTimeout); toastTimeout = setTimeout(() => { el.className = 'toast'; }, 3000);
}
function formPayload(form) { return Object.fromEntries(new FormData(form).entries()); }
function setOptions(select, names, fallback) {
  if (!select) return;
  const previous = select.value;
  const options = names.length ? names : ['Unassigned'];
  select.innerHTML = options.map(n => `<option>${escapeText(n)}</option>`).join('');
  if (options.includes(previous)) select.value = previous;
  else if (fallback && options.includes(fallback)) select.value = fallback;
}
async function loadSPM() {
  try {
    const data = await spmApi('/api/spm/data');
    Object.assign(SPM, data);
    setOptions(byId('taskAssignee'), SPM.team.map(t => t.name), 'Project Manager');
    setOptions(byId('riskOwner'), SPM.team.map(t => t.name), 'Project Manager');
    renderOverview(); renderRequirements(); renderPlan(); renderRisks(); renderTeam(); renderChanges();
  } catch (err) {
    showToast(`Could not load SPM workspace: ${err.message}`, true);
  }
}
function switchTab(name) {
  document.querySelectorAll('.spm-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.spm-tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${name}`));
}
document.querySelectorAll('.spm-tab').forEach(button => button.addEventListener('click', () => switchTab(button.dataset.tab)));
document.querySelectorAll('[data-open-tab]').forEach(button => button.addEventListener('click', () => switchTab(button.dataset.openTab)));

function renderOverview() {
  const m = SPM.metrics;
  byId('metricRequirements').textContent = m.requirements ?? SPM.requirements.length;
  byId('metricTasks').textContent = `${m.tasks_done ?? 0} / ${m.tasks ?? SPM.tasks.length}`;
  byId('metricTaskNote').textContent = `${Math.round((m.completed_effort_days || 0) * 10) / 10} of ${(m.planned_effort_days || 0)} person-days completed`;
  byId('metricRisks').textContent = m.open_risks ?? SPM.risks.filter(r => r.status !== 'Closed').length;
  byId('metricRiskNote').textContent = `${(m.risk_severity_counts?.High || 0)} high-severity open risks`;
  byId('metricEffort').textContent = `${m.planned_effort_days ?? 0} days`;
  byId('metricCapacity').textContent = `${m.allocated_effort_days ?? 0} allocated / ${m.total_capacity_days ?? 0} capacity days`;
  const counts = m.task_status_counts || {};
  const max = Math.max(1, ...STATUSES.map(s => Number(counts[s] || 0)));
  byId('overviewStatus').innerHTML = STATUSES.map((status, i) => {
    const count = Number(counts[status] || 0), width = count / max * 100;
    return `<div class="status-row"><span>${escapeText(status)}</span><div class="status-track"><div class="status-fill" style="width:${width}%;opacity:${[.45,.7,.85,1][i]}"></div></div><strong class="status-number">${count}</strong></div>`;
  }).join('');
  const risks = SPM.risks.filter(r => r.status !== 'Closed').sort((a,b) => b.score - a.score).slice(0, 4);
  byId('overviewRisks').innerHTML = risks.length ? risks.map(r => `<div class="overview-risk"><span class="risk-point ${badgeClass(r.severity)}"></span><div><strong>${escapeText(r.risk_code)} · ${escapeText(r.title)}</strong><small>Owner: ${escapeText(r.owner)} · Status: ${escapeText(r.status)}</small></div><span class="pill ${badgeClass(r.severity)}">${escapeText(r.severity)} · ${r.score}</span></div>`).join('') : '<div class="spm-empty">No open risks recorded.</div>';
}
function renderRequirements() {
  byId('requirementsCount').textContent = `${SPM.requirements.length} requirements`;
  byId('requirementsBody').innerHTML = SPM.requirements.length ? SPM.requirements.map(r => `<tr><td class="primary-cell">${escapeText(r.req_code)}</td><td><strong>${escapeText(r.title)}</strong><div class="muted-cell">${escapeText(r.description)}</div></td><td>${escapeText(r.kind)}</td><td><span class="pill ${badgeClass(r.priority)}">${escapeText(r.priority)}</span></td><td><select class="inline-status req-status" data-id="${r.id}">${['Planned','In Progress','Implemented','Tested'].map(s=>`<option ${r.status===s?'selected':''}>${s}</option>`).join('')}</select><button class="tiny-btn save-req" data-id="${r.id}">Save</button></td><td>${escapeText(r.acceptance_criteria || '—')}</td><td><button class="delete-link delete-record" data-kind="requirements" data-id="${r.id}">Delete</button></td></tr>`).join('') : '<tr><td colspan="7" class="spm-empty">No requirements added.</td></tr>';
}
function renderPlan() {
  byId('tasksCount').textContent = `${SPM.tasks.length} tasks · ${SPM.metrics.planned_effort_days || 0} person-days`;
  byId('kanbanBoard').innerHTML = STATUSES.map(status => {
    const tasks = SPM.tasks.filter(t => t.status === status).sort((a,b) => a.start_week - b.start_week);
    return `<section class="kanban-column"><div class="kanban-head"><strong>${escapeText(status)}</strong><span class="kanban-count">${tasks.length}</span></div>${tasks.length ? tasks.map(t => `<article class="task-card"><span class="task-code">${escapeText(t.task_code)} · WEEK ${t.start_week}</span><h3>${escapeText(t.title)}</h3><p>Phase: ${escapeText(t.phase)}</p><p>Owner: ${escapeText(t.assignee)}</p><p>Effort: ${Number(t.effort_days)} person-days · Duration: ${Number(t.duration_days)} days</p><p>Priority: <span class="pill ${badgeClass(t.priority)}">${escapeText(t.priority)}</span></p><select class="task-status" data-id="${t.id}" aria-label="Status for ${escapeText(t.task_code)}">${STATUSES.map(s=>`<option ${t.status===s?'selected':''}>${escapeText(s)}</option>`).join('')}</select><div class="task-card-actions"><button class="tiny-btn save-task" data-id="${t.id}">Update status</button><button class="tiny-btn delete delete-record" data-kind="tasks" data-id="${t.id}">Delete</button></div></article>`).join('') : '<div class="task-empty">No tasks in this status.</div>'}</section>`;
  }).join('');
  byId('planBody').innerHTML = SPM.tasks.slice().sort((a,b) => a.start_week - b.start_week || a.task_code.localeCompare(b.task_code)).map(t => `<tr><td class="primary-cell">${escapeText(t.task_code)}</td><td><strong>${escapeText(t.title)}</strong></td><td>${escapeText(t.phase)}</td><td>${escapeText(t.assignee)}</td><td>W${t.start_week}</td><td>${Number(t.duration_days)} d</td><td><strong>${Number(t.effort_days)} d</strong></td><td>${escapeText(t.dependencies || '—')}</td><td><span class="pill ${badgeClass(t.status)}">${escapeText(t.status)}</span></td></tr>`).join('') || '<tr><td colspan="9" class="spm-empty">No plan tasks added.</td></tr>';
}
function renderRisks() {
  byId('risksCount').textContent = `${SPM.risks.length} risks`;
  byId('risksBody').innerHTML = SPM.risks.slice().sort((a,b)=>b.score-a.score).map(r => `<tr><td class="primary-cell">${escapeText(r.risk_code)}</td><td><strong>${escapeText(r.title)}</strong><div class="muted-cell">${escapeText(r.category)} · Likelihood ${r.likelihood} × Impact ${r.impact}</div></td><td><span class="risk-score">${r.score}/9</span></td><td><span class="pill ${badgeClass(r.severity)}">${escapeText(r.severity)}</span></td><td>${escapeText(r.owner)}</td><td>${escapeText(r.mitigation)}<div class="muted-cell">Contingency: ${escapeText(r.contingency || 'Not specified')}</div></td><td><select class="inline-status risk-status" data-id="${r.id}">${['Identified','Monitoring','Mitigating','Closed'].map(s=>`<option ${r.status===s?'selected':''}>${s}</option>`).join('')}</select><button class="tiny-btn save-risk" data-id="${r.id}">Save</button></td><td><button class="delete-link delete-record" data-kind="risks" data-id="${r.id}">Delete</button></td></tr>`).join('') || '<tr><td colspan="8" class="spm-empty">No risks recorded.</td></tr>';
}
function renderTeam() {
  byId('teamCount').textContent = `${SPM.team.length} roles · ${SPM.metrics.total_capacity_days || 0} capacity days`;
  byId('teamBody').innerHTML = SPM.team.map(m => {
    const pct = Number(m.utilization_pct || 0), width = Math.min(100,pct);
    return `<tr><td class="primary-cell">${escapeText(m.name)}</td><td>${escapeText(m.role)}<div class="muted-cell">₹${Number(m.hourly_rate).toLocaleString('en-IN')}/hour planning rate</div></td><td>${Number(m.capacity_days)} person-days</td><td><strong>${Number(m.allocated_days)} days</strong></td><td>${pct.toFixed(1)}%<div class="workload-track"><div class="workload-fill ${pct>100?'over':''}" style="width:${width}%"></div></div>${pct>100?'<span class="pill high">Over capacity</span>':''}</td><td>${escapeText(m.skills || '—')}</td></tr>`;
  }).join('') || '<tr><td colspan="6" class="spm-empty">No team roles added.</td></tr>';
}
function renderChanges() {
  byId('changesBody').innerHTML = SPM.changes.map(c => `<tr><td>${formatDate(c.created_at)}</td><td><span class="pill ${badgeClass(c.change_type)}">${escapeText(c.change_type)}</span></td><td class="primary-cell">${escapeText(c.branch_name)}</td><td>${escapeText(c.summary)}</td><td>${escapeText(c.author)}</td><td><span class="pill ${badgeClass(c.status)}">${escapeText(c.status)}</span></td></tr>`).join('') || '<tr><td colspan="6" class="spm-empty">No SCM entries recorded.</td></tr>';
}
async function submitForm(form, resource) {
  const payload = formPayload(form);
  try {
    await spmApi(`/api/spm/${resource}`, {method:'POST', body:JSON.stringify(payload)});
    form.reset();
    if (resource === 'tasks') { form.elements.start_week.value = 1; form.elements.duration_days.value=3; form.elements.effort_days.value=3; }
    if (resource === 'risks') { form.elements.likelihood.value=2; form.elements.impact.value=3; }
    if (resource === 'team') { form.elements.capacity_days.value=5; form.elements.hourly_rate.value=0; }
    if (resource === 'changes') { form.elements.branch_name.value='assignment-7-scm'; form.elements.author.value='Project Team'; form.elements.status.value='Completed'; }
    showToast('Record added successfully.'); await loadSPM();
  } catch (err) { showToast(err.message, true); }
}
byId('requirementForm').addEventListener('submit', e => {e.preventDefault(); submitForm(e.currentTarget, 'requirements');});
byId('taskForm').addEventListener('submit', e => {e.preventDefault(); submitForm(e.currentTarget, 'tasks');});
byId('riskForm').addEventListener('submit', e => {e.preventDefault(); submitForm(e.currentTarget, 'risks');});
byId('teamForm').addEventListener('submit', e => {e.preventDefault(); submitForm(e.currentTarget, 'team');});
byId('changeForm').addEventListener('submit', e => {e.preventDefault(); submitForm(e.currentTarget, 'changes');});

document.addEventListener('click', async (event) => {
  const taskBtn = event.target.closest('.save-task');
  const riskBtn = event.target.closest('.save-risk');
  const reqBtn = event.target.closest('.save-req');
  const delBtn = event.target.closest('.delete-record');
  try {
    if (taskBtn) {
      const id = taskBtn.dataset.id, select = document.querySelector(`.task-status[data-id="${id}"]`);
      await spmApi(`/api/spm/tasks/${id}`, {method:'PUT', body:JSON.stringify({status:select.value})});
      showToast('Task status updated.'); await loadSPM();
    } else if (riskBtn) {
      const id = riskBtn.dataset.id, select = document.querySelector(`.risk-status[data-id="${id}"]`);
      await spmApi(`/api/spm/risks/${id}`, {method:'PUT', body:JSON.stringify({status:select.value})});
      showToast('Risk status updated.'); await loadSPM();
    } else if (reqBtn) {
      const id = reqBtn.dataset.id, select = document.querySelector(`.req-status[data-id="${id}"]`);
      await spmApi(`/api/spm/requirements/${id}`, {method:'PUT', body:JSON.stringify({status:select.value})});
      showToast('Requirement status updated.'); await loadSPM();
    } else if (delBtn) {
      const kind = delBtn.dataset.kind, id = delBtn.dataset.id;
      if (!confirm('Delete this record? This cannot be undone.')) return;
      await spmApi(`/api/spm/${kind}/${id}`, {method:'DELETE'}); showToast('Record deleted.'); await loadSPM();
    }
  } catch (err) { showToast(err.message, true); }
});
loadSPM();
