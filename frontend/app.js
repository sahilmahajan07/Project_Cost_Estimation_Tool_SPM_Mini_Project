const $ = (id) => document.getElementById(id);
const rupees = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0));
const number = (id) => Math.max(0, Number($(id).value || 0));
const COLORS = { Personnel: '#3478f6', Resources: '#8066ed', Testing: '#13a99a', Overhead: '#e2a13b', Contingency: '#95a5ba' };
let projects = [];
let toastTimer;

const roles = [
  { role: 'Developer', count: 2, hourly_rate: 550 },
  { role: 'Designer', count: 1, hourly_rate: 450 },
  { role: 'Tester', count: 1, hourly_rate: 350 },
  { role: 'Project Manager', count: 1, hourly_rate: 600 },
];

function makeTeamRows() {
  $('teamRows').innerHTML = roles.map((r, i) => `
    <tr data-index="${i}"><td>${r.role}</td><td><input aria-label="${r.role} count" data-field="count" type="number" min="0" max="500" step="1" value="${r.count}"></td>
    <td><input aria-label="${r.role} hourly rate" data-field="hourly_rate" type="number" min="0" step="25" value="${r.hourly_rate}"></td></tr>`).join('');
  $('teamRows').querySelectorAll('input').forEach(input => input.addEventListener('input', updatePreview));
}
function gatherPayload() {
  const team = [...$('teamRows').querySelectorAll('tr')].map(tr => ({
    role: tr.cells[0].textContent.trim(),
    count: Math.max(0, parseInt(tr.querySelector('[data-field="count"]').value || '0', 10)),
    hourly_rate: Math.max(0, Number(tr.querySelector('[data-field="hourly_rate"]').value || 0)),
  }));
  const resource = number('resourcesAmount'), testing = number('testingAmount'), overhead = number('overheadAmount');
  return {
    name: $('projectName').value.trim(), description: $('description').value.trim(), project_type: $('projectType').value,
    duration_months: Number($('duration').value || 0), hours_per_day: Number($('hoursDay').value || 0),
    working_days_per_week: Number($('daysWeek').value || 0), contingency_percent: Number($('contingency').value || 0),
    actual_cost: number('actualCost'), team,
    resources: [{ name: 'Resources and infrastructure', amount: resource }],
    testing: [{ name: 'Testing and QA', amount: testing }],
    overhead: [{ name: 'Project overhead', amount: overhead }],
  };
}
function calculatePreview(p) {
  const personnel = p.team.reduce((sum, t) => sum + t.count * t.hourly_rate * p.hours_per_day * p.working_days_per_week * 4.33 * p.duration_months, 0);
  const resources = p.resources.reduce((s, x) => s + x.amount, 0);
  const testing = p.testing.reduce((s, x) => s + x.amount, 0);
  const overhead = p.overhead.reduce((s, x) => s + x.amount, 0);
  const direct = personnel + resources + testing + overhead;
  const contingency = direct * p.contingency_percent / 100;
  return { personnel_cost: personnel, resource_cost: resources, testing_cost: testing, overhead_cost: overhead,
    direct_cost: direct, contingency_percent: p.contingency_percent, contingency_amount: contingency,
    total_cost: direct + contingency, actual_cost: p.actual_cost, variance: p.actual_cost - (direct + contingency) };
}
function breakdownItems(e) {
  return [ ['Personnel', e.personnel_cost], ['Resources', e.resource_cost], ['Testing / QA', e.testing_cost], ['Overhead', e.overhead_cost], ['Contingency', e.contingency_amount] ];
}
function updatePreview() {
  const p = gatherPayload();
  const valid = p.duration_months > 0 && p.hours_per_day > 0 && p.working_days_per_week > 0 && p.contingency_percent >= 0 && p.contingency_percent <= 100;
  if (!valid) { $('totalCost').textContent = '—'; $('breakdownChart').innerHTML = '<div class="empty-chart">Enter valid duration and working-hour values.</div>'; return; }
  const e = calculatePreview(p);
  $('totalCost').textContent = rupees(e.total_cost);
  $('resultSubtitle').textContent = p.name || 'Unsaved estimate preview';
  const items = breakdownItems(e).filter(x => x[1] > 0);
  $('breakdownChart').innerHTML = items.map(([name, value]) => {
    const pct = e.total_cost > 0 ? value / e.total_cost * 100 : 0;
    return `<div class="bar-row"><span class="bar-label">${name}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100,pct)}%;background:${COLORS[name]}"></div></div><span class="bar-value">${pct.toFixed(1)}%</span></div>`;
  }).join('') || '<div class="empty-chart">No costs entered yet.</div>';
  $('breakdownRows').innerHTML = breakdownItems(e).map(([name, value]) => `<div class="breakdown-item"><div class="breakdown-label"><span class="legend-dot" style="background:${COLORS[name]}"></span>${name}</div><strong>${rupees(value)}</strong></div>`).join('');
  const variance = e.variance;
  if (e.actual_cost === 0) {
    $('varianceText').textContent = 'No actual spend entered'; $('varianceTag').textContent = 'Not compared'; $('varianceTag').className = 'variance-tag neutral';
  } else if (variance > 0) {
    $('varianceText').textContent = `${rupees(variance)} above estimate`; $('varianceTag').textContent = 'Over estimate'; $('varianceTag').className = 'variance-tag over';
  } else {
    $('varianceText').textContent = `${rupees(Math.abs(variance))} under / at estimate`; $('varianceTag').textContent = 'Within estimate'; $('varianceTag').className = 'variance-tag under';
  }
}
function toast(message, error = false) {
  $('toast').textContent = message; $('toast').className = `toast show${error ? ' error' : ''}`;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').className = 'toast', 2800);
}
async function api(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'Request failed.');
  return body;
}
async function loadProjects(search = '') {
  try {
    const body = await api('/api/projects' + (search ? '?search=' + encodeURIComponent(search) : ''));
    projects = body.projects || [];
    renderProjects(); renderStats();
  } catch (e) {
    $('projectsBody').innerHTML = `<tr><td colspan="7" class="empty-cell">Could not load projects: ${e.message}</td></tr>`;
    toast('Could not connect to the local API.', true);
  }
}
function renderStats() {
  const totals = projects.map(p => Number(p.estimate?.total_cost || 0));
  const portfolio = totals.reduce((a,b) => a+b, 0);
  const latest = projects[0]?.estimate;
  $('statProjects').textContent = projects.length;
  $('statPortfolio').textContent = rupees(portfolio);
  $('statAverage').textContent = rupees(projects.length ? portfolio / projects.length : 0);
  $('statContingency').textContent = latest ? `${Number(latest.contingency_percent).toFixed(0)}%` : '—';
}
function renderProjects() {
  if (!projects.length) {
    $('projectsBody').innerHTML = '<tr><td colspan="7" class="empty-cell">No saved projects yet. Create your first estimate above.</td></tr>';
    $('projectCount').textContent = '0 records'; return;
  }
  $('projectsBody').innerHTML = projects.map(p => {
    const e = p.estimate || {};
    const actual = Number(p.actual_cost || 0);
    const status = actual <= 0 ? '<span class="budget-status"><i class="tiny-dot"></i> Not compared</span>' : (actual > Number(e.total_cost) ? '<span class="budget-status"><i class="tiny-dot" style="background:#e08069"></i> Above estimate</span>' : '<span class="budget-status"><i class="tiny-dot" style="background:#19b487"></i> Within estimate</span>');
    return `<tr><td><div class="project-name">${escapeHTML(p.name)}</div><div class="project-sub">${escapeHTML(p.description || 'No description added')}</div></td><td><span class="type-chip">${escapeHTML(p.project_type)}</span></td><td>${Number(p.duration_months)} mo</td><td>${Number(e.contingency_percent || 0)}%</td><td><strong>${rupees(e.total_cost)}</strong></td><td>${status}</td><td><div class="actions"><button class="action-btn" data-action="edit" data-id="${p.id}">Open</button><button class="action-btn delete" data-action="delete" data-id="${p.id}">Delete</button></div></td></tr>`;
  }).join('');
  $('projectCount').textContent = `${projects.length} record${projects.length === 1 ? '' : 's'}`;
  $('projectsBody').querySelectorAll('button').forEach(btn => btn.addEventListener('click', handleProjectAction));
}
function escapeHTML(value) { return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
async function handleProjectAction(event) {
  const id = Number(event.currentTarget.dataset.id), action = event.currentTarget.dataset.action;
  const project = projects.find(p => Number(p.id) === id);
  if (!project) return;
  if (action === 'edit') { populateForm(project); document.querySelector('#estimator').scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  if (action === 'delete' && confirm(`Delete "${project.name}" and its saved estimate history?`)) {
    try { await api(`/api/projects/${id}`, { method: 'DELETE' }); toast('Project and linked data deleted.'); await loadProjects($('searchInput').value.trim()); }
    catch (e) { toast(e.message, true); }
  }
}
function populateForm(p) {
  $('projectId').value = p.id; $('formTitle').textContent = 'Edit and re-estimate'; $('saveBtn').innerHTML = 'Update estimate <span>→</span>';
  $('projectName').value = p.name || ''; $('description').value = p.description || ''; $('projectType').value = p.project_type || 'Web Application';
  $('duration').value = p.duration_months; $('hoursDay').value = p.hours_per_day; $('daysWeek').value = p.working_days_per_week;
  $('contingency').value = p.contingency_percent; $('actualCost').value = p.actual_cost || 0;
  $('resourcesAmount').value = (p.resources || []).reduce((s,x)=>s+Number(x.amount||0),0);
  $('testingAmount').value = (p.testing || []).reduce((s,x)=>s+Number(x.amount||0),0);
  $('overheadAmount').value = (p.overhead || []).reduce((s,x)=>s+Number(x.amount||0),0);
  const byRole = new Map((p.team || []).map(t => [t.role, t]));
  $('teamRows').querySelectorAll('tr').forEach(tr => { const item = byRole.get(tr.cells[0].textContent.trim()); if (item) { tr.querySelector('[data-field="count"]').value = item.count; tr.querySelector('[data-field="hourly_rate"]').value = item.hourly_rate; } else { tr.querySelector('[data-field="count"]').value = 0; } });
  updatePreview(); toast('Project loaded. Change any values and save a new snapshot.');
}
function resetForm() {
  $('projectId').value = ''; $('formTitle').textContent = 'Build an estimate'; $('saveBtn').innerHTML = 'Calculate &amp; save estimate <span>→</span>';
  $('estimateForm').reset(); $('projectType').value = 'Web Application';
  roles.forEach((r, i) => { const tr = $('teamRows').querySelectorAll('tr')[i]; tr.querySelector('[data-field="count"]').value = r.count; tr.querySelector('[data-field="hourly_rate"]').value = r.hourly_rate; });
  $('duration').value = 3; $('hoursDay').value = 8; $('daysWeek').value = 5; $('resourcesAmount').value = 26500; $('testingAmount').value = 12000; $('overheadAmount').value = 7000; $('contingency').value = 10; $('actualCost').value = 0;
  updatePreview();
}
$('estimateForm').addEventListener('submit', async event => {
  event.preventDefault();
  const payload = gatherPayload();
  if (!payload.name) { toast('Please enter a project name.', true); $('projectName').focus(); return; }
  if (payload.duration_months <= 0 || payload.hours_per_day <= 0 || payload.hours_per_day > 24 || payload.working_days_per_week <= 0 || payload.working_days_per_week > 7 || payload.contingency_percent < 0 || payload.contingency_percent > 100) { toast('Check duration, hours, working days and contingency.', true); return; }
  const id = $('projectId').value;
  try {
    const result = await api(id ? `/api/projects/${id}` : '/api/projects', { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) });
    $('projectId').value = result.project.id; $('formTitle').textContent = 'Edit and re-estimate'; $('saveBtn').innerHTML = 'Update estimate <span>→</span>';
    await loadProjects($('searchInput').value.trim());
    updatePreview();
    toast(id ? 'Estimate updated and history snapshot saved.' : 'Estimate calculated and saved to database.');
  } catch (e) { toast(e.message, true); }
});
['projectName','duration','hoursDay','daysWeek','resourcesAmount','testingAmount','overheadAmount','contingency','actualCost','projectType','description'].forEach(id => $(id).addEventListener('input', updatePreview));
$('resetBtn').addEventListener('click', () => { resetForm(); toast('Form reset to the demo defaults.'); });
$('newEstimateBtn').addEventListener('click', () => { resetForm(); document.querySelector('#estimator').scrollIntoView({behavior:'smooth',block:'start'}); $('projectName').focus(); });
let searchTimer;
$('searchInput').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => loadProjects($('searchInput').value.trim()), 200); });
makeTeamRows(); updatePreview(); loadProjects();

$('exportBtn').addEventListener('click', () => {
  if (!projects.length) { toast('No project estimates to export.', true); return; }
  const header = ['Project ID','Project Name','Project Type','Duration (months)','Personnel Cost','Resource Cost','Testing Cost','Overhead Cost','Contingency (%)','Contingency Amount','Estimated Total (INR)','Actual Cost (INR)','Variance (Actual - Estimated)'];
  const rows = projects.map(p => { const e = p.estimate || {}; return [p.id,p.name,p.project_type,p.duration_months,e.personnel_cost,e.resource_cost,e.testing_cost,e.overhead_cost,e.contingency_percent,e.contingency_amount,e.total_cost,p.actual_cost,e.variance]; });
  const csv = [header, ...rows].map(row => row.map(value => '"' + String(value ?? '').replace(/"/g, '""') + '"').join(',')).join('\r\n');
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'project-cost-estimates.csv'; link.click(); URL.revokeObjectURL(url);
  toast('CSV export prepared.');
});
