/* House Committee YouTube Event ID Tracker - Dashboard JavaScript */

let committeeData = [];
let missingData = [];

document.addEventListener('DOMContentLoaded', () => {
    loadOverview();
    setupTabs();
    setupSort();
    setupModal();
});

function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab + '-tab').classList.add('active');
            if (tab.dataset.tab === 'missing' && missingData.length === 0) loadMissingIds();
        });
    });
}

function setupSort() {
    document.getElementById('sort-select').addEventListener('change', renderCommittees);
}

function setupModal() {
    const modal = document.getElementById('committee-modal');
    modal.querySelector('.modal-backdrop').addEventListener('click', closeModal);
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
}

function closeModal() {
    document.getElementById('committee-modal').style.display = 'none';
}

async function loadOverview() {
    try {
        const resp = await fetch('/api/overview');
        const data = await resp.json();
        committeeData = data.committees;
        renderSummary(data.overall);
        renderCommittees();
        if (data.data_updated) {
            document.getElementById('data-freshness').textContent = `Data as of ${data.data_updated}`;
        }
    } catch (err) {
        document.getElementById('summary-content').innerHTML =
            '<div class="no-data"><h3>Error loading data</h3><p>Please ensure the server is running and data has been collected.</p></div>';
    }
}

function renderSummary(overall) {
    const el = document.getElementById('summary-content');
    const gradeColor = getGradeColor(overall.grade);
    el.innerHTML = `
        <div class="stat-box">
            <div class="stat-grade" style="color: ${gradeColor}">${overall.grade}</div>
            <div class="stat-label">Overall Grade</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">${overall.compliance_pct}%</div>
            <div class="stat-label">With Event IDs</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">${overall.total_proceedings.toLocaleString()}</div>
            <div class="stat-label">Proceedings Tracked</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: var(--grade-a)">${overall.with_event_id.toLocaleString()}</div>
            <div class="stat-label">With Event ID</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: var(--grade-f)">${overall.without_event_id.toLocaleString()}</div>
            <div class="stat-label">Missing Event ID</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">${overall.committees_tracked}</div>
            <div class="stat-label">Committees Tracked</div>
        </div>
    `;
}

function renderCommittees() {
    const el = document.getElementById('committee-list');
    const sortBy = document.getElementById('sort-select').value;
    let sorted = [...committeeData];
    const gradeOrder = { 'F': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'N/A': 5 };

    switch (sortBy) {
        case 'grade':
            sorted.sort((a, b) => (gradeOrder[a.grade] || 5) - (gradeOrder[b.grade] || 5) || a.name.localeCompare(b.name));
            break;
        case 'grade-best':
            sorted.sort((a, b) => (gradeOrder[b.grade] || 5) - (gradeOrder[a.grade] || 5) || a.name.localeCompare(b.name));
            break;
        case 'name':
            sorted.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'videos':
            sorted.sort((a, b) => b.total_proceedings - a.total_proceedings);
            break;
        case 'compliance':
            sorted.sort((a, b) => b.compliance_pct - a.compliance_pct);
            break;
    }

    if (sorted.length === 0) {
        el.innerHTML = '<div class="no-data"><h3>No data yet</h3><p>Run data collection scripts to populate the dashboard.</p></div>';
        return;
    }

    el.innerHTML = sorted.map(c => {
        const procLabel = c.total_proceedings === 1 ? 'proceeding' : 'proceedings';
        return `
        <div class="committee-card" onclick="openCommitteeDetail('${c.system_code}')">
            <div class="committee-grade" style="background: ${c.grade_color}">${c.grade}</div>
            <div class="committee-info">
                <div class="committee-name" title="${c.name}">${c.name}</div>
                <div class="committee-stats">
                    ${c.total_proceedings} ${procLabel} &middot;
                    ${c.with_event_id} with ID &middot;
                    <strong>${c.compliance_pct}%</strong>
                    ${c.official_events > 0 ? `<span class="official-count">${c.official_events} official events</span>` : ''}
                </div>
                <div class="committee-bar">
                    <div class="committee-bar-fill" style="width: ${Math.max(c.compliance_pct, 1)}%; background: ${c.grade_color}"></div>
                </div>
            </div>
        </div>`;
    }).join('');
}

async function openCommitteeDetail(systemCode) {
    const modal = document.getElementById('committee-modal');
    const body = document.getElementById('modal-body');
    modal.style.display = 'flex';
    body.innerHTML = '<div class="loading">Loading committee details...</div>';

    try {
        const resp = await fetch(`/api/committee/${systemCode}`);
        const data = await resp.json();
        const comm = data.committee;
        const videos = data.videos;
        const total = videos.length;
        const withId = videos.filter(v => v.has_event_id).length;
        const matched = videos.filter(v => v.matched_event_id).length;
        const pct = total > 0 ? Math.round(withId / total * 100) : 0;
        const grade = getGrade(pct);
        const gradeColor = getGradeColor(grade);
        const procLabel = total === 1 ? 'Proceeding' : 'Proceedings';

        body.innerHTML = `
            <div class="modal-header">
                <div class="committee-grade" style="background: ${gradeColor}">${grade}</div>
                <div>
                    <h2>${comm.name}</h2>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        <a href="${comm.youtube_url}" target="_blank">@${comm.youtube_handle}</a>
                        &middot; ${pct}% compliance
                    </div>
                </div>
            </div>
            <div class="modal-stats">
                <div class="stat-box">
                    <div class="stat-number">${total}</div>
                    <div class="stat-label">Total ${procLabel}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" style="color: var(--grade-a)">${withId}</div>
                    <div class="stat-label">With Event ID</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" style="color: var(--grade-f)">${total - withId}</div>
                    <div class="stat-label">Missing Event ID</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">${matched}</div>
                    <div class="stat-label">Matched to Events</div>
                </div>
            </div>
            <div class="video-list-header">
                <h3>${procLabel}</h3>
                <button class="email-btn" onclick="showEmailDraft('${systemCode}')">Generate Email Draft</button>
            </div>
            <div class="video-list-legend">
                <span><span class="video-status status-green"></span> Has Event ID</span>
                <span><span class="video-status status-yellow"></span> Suggested match</span>
                <span><span class="video-status status-red"></span> No match</span>
            </div>
            <div>
                ${videos.length === 0 ? '<div class="no-data">No proceedings found</div>' :
                videos.map(v => `
                    <div class="video-item">
                        <div class="video-status ${v.has_event_id ? 'status-green' : (v.matched_event_id ? 'status-yellow' : 'status-red')}"></div>
                        <div class="video-item-info">
                            <div class="video-item-title">
                                <a href="${v.url}" target="_blank" title="${escapeHtml(v.title)}">${escapeHtml(v.title)}</a>
                            </div>
                            <div class="video-item-meta">
                                ${v.upload_date || 'Unknown date'} &middot; ${v.duration_minutes} min
                                ${v.event_type ? ' &middot; ' + v.event_type : ''}
                            </div>
                        </div>
                        <div class="video-item-eventid">
                            ${v.has_event_id
                                ? `<span style="color: var(--grade-a)">ID: ${v.extracted_event_id}</span>`
                                : (v.matched_event_id
                                    ? `<a href="${v.docs_house_url}" target="_blank" style="color: var(--grade-c)" title="${escapeHtml(v.event_title || '')} (${Math.round((v.match_confidence||0) * 100)}% confidence)">Suggested: ${v.matched_event_id}</a>`
                                    : '<span style="color: var(--grade-f)">No ID</span>')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (err) {
        body.innerHTML = '<div class="no-data"><h3>Error loading details</h3></div>';
    }
}

async function showEmailDraft(systemCode) {
    try {
        const resp = await fetch(`/api/email-draft/${systemCode}`);
        const data = await resp.json();
        if (data.count === 0) {
            const body = document.getElementById('modal-body');
            body.innerHTML += `<div style="margin-top:1rem; padding:1rem; background:#f0fdf4; border-radius:8px; border:1px solid #bbf7d0;">No videos missing Event IDs for this committee.</div>`;
            return;
        }
        const body = document.getElementById('modal-body');
        body.innerHTML += `
            <div style="margin-top: 1.5rem; border-top: 1px solid var(--border); padding-top: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3>Draft Email (${data.count} videos)</h3>
                    <button class="copy-btn" onclick="copyEmailDraft()">Copy to Clipboard</button>
                </div>
                <div style="margin-top: 0.5rem; font-weight: 600; font-size: 0.9rem;">Subject: ${escapeHtml(data.subject)}</div>
                <div class="email-preview" id="email-body">${escapeHtml(data.body)}</div>
            </div>
        `;
    } catch (err) { console.error('Error:', err); }
}

function copyEmailDraft() {
    const body = document.getElementById('email-body');
    if (body) {
        navigator.clipboard.writeText(body.textContent).then(() => {
            const btn = document.querySelector('.copy-btn');
            btn.textContent = 'Copied!';
            setTimeout(() => btn.textContent = 'Copy to Clipboard', 2000);
        });
    }
}

async function loadMissingIds() {
    try {
        const resp = await fetch('/api/missing-ids');
        const data = await resp.json();
        missingData = data.videos;
        renderMissingIds();
        populateCommitteeFilter();
    } catch (err) {
        document.getElementById('missing-list').innerHTML = '<div class="no-data"><h3>Error loading data</h3></div>';
    }
}

function populateCommitteeFilter() {
    const filter = document.getElementById('committee-filter');
    const committees = [...new Set(missingData.map(v => v.committee_name))].sort();
    committees.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        filter.appendChild(opt);
    });
    filter.addEventListener('change', renderMissingIds);
    document.getElementById('search-input').addEventListener('input', renderMissingIds);
}

function renderMissingIds() {
    const el = document.getElementById('missing-list');
    const committeeFilter = document.getElementById('committee-filter').value;
    const searchFilter = document.getElementById('search-input').value.toLowerCase();

    let filtered = missingData;
    if (committeeFilter) filtered = filtered.filter(v => v.committee_name === committeeFilter);
    if (searchFilter) filtered = filtered.filter(v =>
        v.title.toLowerCase().includes(searchFilter) || v.committee_name.toLowerCase().includes(searchFilter)
    );

    if (filtered.length === 0) {
        el.innerHTML = '<div class="no-data"><h3>No matching videos</h3></div>';
        return;
    }

    const shown = filtered.slice(0, 50);
    el.innerHTML = shown.map(v => `
        <div class="missing-video">
            <div class="missing-video-info">
                <div class="missing-video-title">
                    <a href="${v.url}" target="_blank">${escapeHtml(v.title)}</a>
                    <span class="tag tag-committee">${escapeHtml(v.committee_name)}</span>
                </div>
                <div class="missing-video-meta">
                    ${v.upload_date || 'Unknown date'} &middot; ${v.duration_minutes} min
                </div>
                ${v.suggested_event_id ? `
                    <div class="suggested-match">
                        Suggested Event ID: <strong>${v.suggested_event_id}</strong>
                        ${v.event_title ? ` &mdash; <em>${escapeHtml(v.event_title)}</em>` : ''}
                        ${v.docs_house_url ? ` &middot; <a href="${v.docs_house_url}" target="_blank">View on docs.house.gov</a>` : ''}
                        <span style="opacity:0.6">(${Math.round((v.match_confidence || 0) * 100)}% match)</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');

    if (filtered.length > 50) {
        el.innerHTML += `<div class="no-data" style="padding: 1rem;">Showing 50 of ${filtered.length} videos. Use filters to narrow results.</div>`;
    }
}

function getGrade(pct) {
    if (pct >= 50) return 'A';
    if (pct >= 30) return 'B';
    if (pct >= 15) return 'C';
    if (pct >= 5) return 'D';
    return 'F';
}

function getGradeColor(grade) {
    return { 'A': '#22c55e', 'B': '#84cc16', 'C': '#eab308', 'D': '#f97316', 'F': '#ef4444', 'N/A': '#94a3b8' }[grade] || '#94a3b8';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
