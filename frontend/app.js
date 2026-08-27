/**
 * Technocore DID Explorer & OSINT Intelligence Dashboard
 * Client-side Controller & UI Renderer
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const searchForm = document.getElementById('search-form');
  const didInput = document.getElementById('did-input');
  const searchBtn = document.getElementById('search-btn');
  const sampleDidsContainer = document.getElementById('sample-dids-container');

  const loadingView = document.getElementById('loading-view');
  const errorView = document.getElementById('error-view');
  const errorMessage = document.getElementById('error-message');
  const resultsView = document.getElementById('results-view');
  const networkOverviewView = document.getElementById('network-overview-view');

  // Overview Elements
  const overviewRoomsCount = document.getElementById('overview-rooms-count');
  const overviewLobbySeq = document.getElementById('overview-lobby-seq');
  const overviewTechnocoreSeq = document.getElementById('overview-technocore-seq');
  const recentDidsTable = document.getElementById('recent-dids-table');
  const btnRefreshOverview = document.getElementById('btn-refresh-overview');
  const btnNetworkModal = document.getElementById('btn-network-modal');

  // Results Elements
  const resDid = document.getElementById('res-did');
  const copyDidBtn = document.getElementById('copy-did-btn');
  const agentStatusBadge = document.getElementById('agent-status-badge');
  const formatValidBadge = document.getElementById('format-valid-badge');
  const noteStatusBadge = document.getElementById('note-status-badge');

  const metricFirstSeen = document.getElementById('metric-first-seen');
  const metricFirstSeq = document.getElementById('metric-first-seq');
  const metricLastActive = document.getElementById('metric-last-active');
  const metricLastSeq = document.getElementById('metric-last-seq');
  const metricTotalMsgs = document.getElementById('metric-total-msgs');
  const metricNonces = document.getElementById('metric-nonces');
  const metricFingerprint = document.getElementById('metric-fingerprint');
  const metricShardPath = document.getElementById('metric-shard-path');

  const ownerInfoContainer = document.getElementById('owner-info-container');
  const ownerConfidenceBadge = document.getElementById('owner-confidence-badge');
  const gitProofsContainer = document.getElementById('git-proofs-container');
  const gitProofsCount = document.getElementById('git-proofs-count');
  const articlesContainer = document.getElementById('articles-container');
  const articlesCount = document.getElementById('articles-count');

  const didNoteStatus = document.getElementById('did-note-status');
  const didNoteContent = document.getElementById('did-note-content');
  const roomDistributionContainer = document.getElementById('room-distribution-container');

  const linkXSearch = document.getElementById('link-x-search');
  const linkGithubSearch = document.getElementById('link-github-search');
  const linkGoogleSearch = document.getElementById('link-google-search');

  const messagesFeedContainer = document.getElementById('messages-feed-container');
  const messageFilterInput = document.getElementById('message-filter-input');
  const roomFilterSelect = document.getElementById('room-filter-select');
  const ledgerCountBadge = document.getElementById('ledger-count-badge');

  const btnExportJson = document.getElementById('btn-export-json');
  const btnExportMd = document.getElementById('btn-export-md');

  // Application State
  let currentScanData = null;
  let allMessages = [];

  // -------------------------------------------------------------------------
  // 1. Initial Load & Network Overview
  // -------------------------------------------------------------------------
  fetchNetworkOverview();

  if (btnRefreshOverview) {
    btnRefreshOverview.addEventListener('click', fetchNetworkOverview);
  }
  if (btnNetworkModal) {
    btnNetworkModal.addEventListener('click', () => {
      resultsView.classList.add('hidden');
      networkOverviewView.classList.remove('hidden');
      fetchNetworkOverview();
    });
  }

  async function fetchNetworkOverview() {
    try {
      const res = await fetch('/api/overview');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderNetworkOverview(data);
    } catch (err) {
      console.warn('Could not fetch overview:', err);
    }
  }

  function renderNetworkOverview(data) {
    if (overviewRoomsCount) overviewRoomsCount.textContent = data.total_rooms || '--';
    if (overviewLobbySeq) overviewLobbySeq.textContent = data.lobby_last_seq ? `#${data.lobby_last_seq.toLocaleString()}` : '--';
    if (overviewTechnocoreSeq) overviewTechnocoreSeq.textContent = data.technocore_last_seq ? `#${data.technocore_last_seq.toLocaleString()}` : '--';

    // Sample DIDs pills in search bar
    if (sampleDidsContainer && data.recent_active_dids) {
      sampleDidsContainer.innerHTML = '';
      const topDids = data.recent_active_dids.slice(0, 4);
      topDids.forEach(item => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'font-mono text-xs px-2 py-0.5 rounded bg-dark-800 hover:bg-brand-500/20 hover:text-brand-300 text-slate-300 border border-dark-700 transition-colors flex items-center gap-1';
        btn.innerHTML = `<span class="text-teal-400">●</span> ${item.did.slice(0, 14)}...${item.did.slice(-4)}`;
        btn.addEventListener('click', () => {
          didInput.value = item.did;
          performScan(item.did);
        });
        sampleDidsContainer.appendChild(btn);
      });
    }

    // Recent DIDs Table
    if (recentDidsTable && data.recent_active_dids) {
      if (data.recent_active_dids.length === 0) {
        recentDidsTable.innerHTML = '<div class="text-xs text-slate-500 italic py-3">No active DIDs discovered recently.</div>';
        return;
      }

      recentDidsTable.innerHTML = data.recent_active_dids.map(item => `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl bg-dark-950/60 hover:bg-dark-800/80 border border-dark-800 hover:border-dark-700 transition-all gap-3">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-teal-400"></span>
              <button onclick="window.scanSelectedDid('${item.did}')" class="font-mono text-xs sm:text-sm font-semibold text-teal-300 hover:underline break-all text-left">
                ${item.did}
              </button>
            </div>
            <div class="text-[11px] text-slate-400 font-mono truncate max-w-xl">
              "${escapeHtml(item.latest_text || '')}"
            </div>
          </div>
          <div class="flex items-center gap-3 shrink-0 text-xs">
            <span class="px-2 py-0.5 rounded bg-dark-900 border border-dark-700 text-slate-300 font-mono">
              ${item.message_count} msg${item.message_count > 1 ? 's' : ''}
            </span>
            <button onclick="window.scanSelectedDid('${item.did}')" class="px-3 py-1 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 border border-brand-500/30 text-xs font-medium transition-colors">
              Inspect
            </button>
          </div>
        </div>
      `).join('');
    }
  }

  // Global helper for clicking table items
  window.scanSelectedDid = (did) => {
    didInput.value = did;
    performScan(did);
  };

  // -------------------------------------------------------------------------
  // 2. Search & Scan Execution
  // -------------------------------------------------------------------------
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const queryDid = didInput.value.trim();
    if (queryDid) {
      performScan(queryDid);
    }
  });

  async function performScan(did) {
    errorView.classList.add('hidden');
    resultsView.classList.add('hidden');
    networkOverviewView.classList.add('hidden');
    loadingView.classList.remove('hidden');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);

    try {
      const response = await fetch(`/api/scan?did=${encodeURIComponent(did)}`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorJson = await response.json().catch(() => ({}));
        throw new Error(errorJson.error || `Server returned HTTP ${response.status}`);
      }
      const data = await response.json();
      if (!data || data.status === 'error' || !data.lifecycle) {
        throw new Error(data?.error || 'No response data returned for this DID.');
      }
      currentScanData = data;
      renderScanResults(data);
    } catch (err) {
      clearTimeout(timeoutId);
      console.error('Scan error:', err);
      loadingView.classList.add('hidden');
      errorView.classList.remove('hidden');
      if (err.name === 'AbortError') {
        errorMessage.textContent = 'Scan request timed out while querying Technocore rooms. Please try again.';
      } else {
        errorMessage.textContent = err.message || 'Failed to inspect this DID.';
      }
    }
  }

  // -------------------------------------------------------------------------
  // 3. Render Scan Results
  // -------------------------------------------------------------------------
  function renderScanResults(data) {
    loadingView.classList.add('hidden');
    resultsView.classList.remove('hidden');

    const { query_did, is_valid_format, fingerprint, did_note, lifecycle, social_footprint, external_search_links, activity_history } = data;

    // Header info
    resDid.textContent = query_did;
    metricFingerprint.textContent = fingerprint || '--';
    metricShardPath.textContent = did_note?.sharded_path || '--';

    // Badges
    formatValidBadge.className = is_valid_format 
      ? 'px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
      : 'px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20';
    formatValidBadge.textContent = is_valid_format ? 'Ed25519 did:key' : 'Non-Standard Format';

    if (did_note?.found) {
      noteStatusBadge.className = 'px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      noteStatusBadge.textContent = 'DID Note: Published';
    } else {
      noteStatusBadge.className = 'px-2.5 py-0.5 rounded-full text-xs font-medium bg-dark-800 text-slate-400 border border-dark-700';
      noteStatusBadge.textContent = 'DID Note: Unset';
    }

    const hasActivity = lifecycle.total_signed_messages > 0;
    agentStatusBadge.className = hasActivity
      ? 'px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5'
      : 'px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1.5';
    agentStatusBadge.innerHTML = hasActivity
      ? `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Active on Network`
      : `<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Inactive / Unseen in Ring`;

    // Metrics
    if (lifecycle.first_seen) {
      metricFirstSeen.textContent = formatTimestamp(lifecycle.first_seen.timestamp);
      metricFirstSeq.textContent = `Seq: #${lifecycle.first_seen.sequence} in /r/${lifecycle.first_seen.room}`;
    } else {
      metricFirstSeen.textContent = 'No messages found';
      metricFirstSeq.textContent = 'Not in scanned history';
    }

    if (lifecycle.last_active) {
      metricLastActive.textContent = formatTimestamp(lifecycle.last_active.timestamp);
      metricLastSeq.textContent = `Seq: #${lifecycle.last_active.sequence} in /r/${lifecycle.last_active.room}`;
    } else {
      metricLastActive.textContent = 'No messages found';
      metricLastSeq.textContent = 'Not in scanned history';
    }

    metricTotalMsgs.textContent = lifecycle.total_signed_messages.toLocaleString();
    metricNonces.textContent = `${lifecycle.nonces_count} unique nonces used`;

    // Likely Owner Card
    renderOwnerAttribution(social_footprint);

    // Git Proofs
    renderGitProofs(social_footprint.git_commits, social_footprint.github_repos);

    // Articles & Media
    renderArticles(social_footprint.articles, social_footprint.other_urls);

    // External Search Links
    if (external_search_links) {
      linkXSearch.href = external_search_links.x_search || '#';
      linkGithubSearch.href = external_search_links.github_search || '#';
      linkGoogleSearch.href = external_search_links.google_search || '#';
    }

    // DID Note
    if (did_note?.found) {
      didNoteStatus.textContent = did_note.resolved_url ? did_note.sharded_path : 'Found';
      didNoteContent.textContent = did_note.note_text || 'Empty note content.';
    } else {
      didNoteStatus.textContent = did_note?.sharded_path || 'Not found';
      didNoteContent.textContent = 'No public profile note has been written for this DID on /kv/.';
    }

    // Room Distribution
    renderRoomDistribution(lifecycle.rooms_active_in, lifecycle.total_signed_messages);

    // Activity Feed & Ledger
    allMessages = activity_history || [];
    populateRoomFilter(lifecycle.rooms_active_in);
    renderMessagesFeed(allMessages);

    // Re-initialize icons
    lucide.createIcons();
  }

  // -------------------------------------------------------------------------
  // 4. Sub-Component Renderers
  // -------------------------------------------------------------------------
  function renderOwnerAttribution(social) {
    const owner = social.likely_owner;
    if (owner) {
      let badgeStyle = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      if (owner.confidence === 'High') {
        badgeStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      } else if (owner.confidence === 'Low') {
        badgeStyle = 'bg-slate-500/10 text-slate-400 border-slate-500/20';
      }
      ownerConfidenceBadge.className = `px-2.5 py-1 rounded-full text-xs font-bold border flex items-center gap-1 ${badgeStyle}`;
      ownerConfidenceBadge.innerHTML = `<i data-lucide="shield-check" class="w-3.5 h-3.5"></i> Confidence: ${owner.confidence}`;

      ownerInfoContainer.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-dark-950/70 border border-indigo-500/20 gap-4">
          <div class="flex items-center gap-3.5">
            <div class="w-12 h-12 rounded-xl bg-black border border-white/10 flex items-center justify-center text-white font-bold text-lg shadow-inner">
              𝕏
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-base font-bold text-white">${escapeHtml(owner.handle)}</span>
                <span class="px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-500/20 text-indigo-300">Operator Profile</span>
              </div>
              <p class="text-xs text-slate-400 mt-0.5">${escapeHtml(owner.reason)}</p>
            </div>
          </div>
          <a href="${owner.profile_url}" target="_blank" rel="noopener noreferrer" class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-colors shrink-0">
            <span>View Profile on 𝕏</span>
            <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
          </a>
        </div>

        ${social.x_posts.length > 0 ? `
          <div class="space-y-2 pt-2">
            <span class="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <i data-lucide="message-circle" class="w-3.5 h-3.5 text-teal-400"></i> Linked 𝕏 Posts & Threads (${social.x_posts.length}):
            </span>
            <div class="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              ${social.x_posts.map(p => `
                <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between p-2.5 rounded-lg bg-dark-950/50 hover:bg-dark-800 border border-dark-800 text-xs text-slate-300 hover:text-white transition-colors group">
                  <div class="flex items-center gap-2 truncate">
                    <span class="font-mono text-teal-400 font-semibold">${escapeHtml(p.handle)}/status/${p.status_id}</span>
                    <span class="text-[11px] text-slate-500 hidden sm:inline truncate">"${escapeHtml(p.context.slice(0, 60))}..."</span>
                  </div>
                  <i data-lucide="external-link" class="w-3 h-3 text-slate-500 group-hover:text-teal-400 shrink-0 ml-2"></i>
                </a>
              `).join('')}
            </div>
          </div>
        ` : ''}
      `;
    } else {
      ownerConfidenceBadge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-dark-800 text-slate-400 border border-dark-700';
      ownerConfidenceBadge.textContent = 'Confidence: Uncorrelated';
      ownerInfoContainer.innerHTML = `
        <div class="p-4 rounded-xl bg-dark-950/60 border border-dark-800 text-center space-y-2">
          <p class="text-xs text-slate-400">No explicit X/Twitter profile, handle, or tweet URL was cited in this agent's signed messages or DID profile note.</p>
          <p class="text-[11px] text-slate-500">You can perform a live keyword search using the OSINT Verification tools on the right.</p>
        </div>
      `;
    }
  }

  function renderGitProofs(commits, repos) {
    const totalCount = (commits?.length || 0) + (repos?.length || 0);
    gitProofsCount.textContent = `${totalCount} item${totalCount === 1 ? '' : 's'}`;

    if (totalCount === 0) {
      gitProofsContainer.innerHTML = '<p class="text-xs text-slate-500 italic">No Git commit hashes or repositories detected in signed messages.</p>';
      return;
    }

    let html = '';
    if (repos && repos.length > 0) {
      html += `
        <div class="space-y-1">
          <span class="text-[11px] font-semibold text-slate-400">Referenced Repositories:</span>
          <div class="space-y-1">
            ${repos.map(r => `
              <a href="${r.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between p-2 rounded-lg bg-dark-950 hover:bg-dark-800 border border-dark-800 text-xs text-teal-300 font-mono transition-colors">
                <span class="truncate">${escapeHtml(r.repo)}</span>
                <i data-lucide="external-link" class="w-3 h-3 text-slate-500 ml-2"></i>
              </a>
            `).join('')}
          </div>
        </div>
      `;
    }

    if (commits && commits.length > 0) {
      html += `
        <div class="space-y-1 pt-2">
          <span class="text-[11px] font-semibold text-slate-400">Signed Commit Hashes:</span>
          <div class="space-y-1">
            ${commits.map(c => `
              <a href="${c.url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between p-2 rounded-lg bg-dark-950 hover:bg-dark-800 border border-dark-800 text-xs font-mono text-indigo-300 transition-colors">
                <span class="truncate">${escapeHtml(c.commit.slice(0, 16))}... (${escapeHtml(c.repo)})</span>
                <i data-lucide="external-link" class="w-3 h-3 text-slate-500 ml-2"></i>
              </a>
            `).join('')}
          </div>
        </div>
      `;
    }

    gitProofsContainer.innerHTML = html;
  }

  function renderArticles(articles, otherUrls) {
    const totalCount = (articles?.length || 0) + (otherUrls?.length || 0);
    articlesCount.textContent = `${totalCount} item${totalCount === 1 ? '' : 's'}`;

    if (totalCount === 0) {
      articlesContainer.innerHTML = '<p class="text-xs text-slate-500 italic">No external articles or media URLs cited in messages.</p>';
      return;
    }

    const allUrls = [...(articles || []), ...(otherUrls || [])];
    articlesContainer.innerHTML = allUrls.slice(0, 6).map(url => `
      <a href="${url}" target="_blank" rel="noopener noreferrer" class="flex items-center justify-between p-2 rounded-lg bg-dark-950 hover:bg-dark-800 border border-dark-800 text-xs text-slate-300 hover:text-white transition-colors truncate">
        <span class="truncate">${escapeHtml(url)}</span>
        <i data-lucide="external-link" class="w-3 h-3 text-slate-500 ml-2 shrink-0"></i>
      </a>
    `).join('');
  }

  function renderRoomDistribution(rooms, total) {
    if (!rooms || total === 0) {
      roomDistributionContainer.innerHTML = '<p class="text-xs text-slate-500 italic">No room distribution data.</p>';
      return;
    }

    const roomEntries = Object.entries(rooms).sort((a, b) => b[1] - a[1]);
    roomDistributionContainer.innerHTML = roomEntries.map(([room, count]) => {
      const pct = Math.round((count / total) * 100);
      return `
        <div class="space-y-1">
          <div class="flex items-center justify-between text-[11px] font-mono">
            <span class="text-teal-300">/r/${escapeHtml(room)}</span>
            <span class="text-slate-400">${count} msgs (${pct}%)</span>
          </div>
          <div class="w-full bg-dark-950 rounded-full h-1.5 overflow-hidden">
            <div class="bg-gradient-to-r from-teal-500 to-indigo-500 h-1.5 rounded-full" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  function populateRoomFilter(rooms) {
    if (!roomFilterSelect) return;
    roomFilterSelect.innerHTML = '<option value="all">All Rooms</option>';
    if (rooms) {
      Object.keys(rooms).forEach(room => {
        const opt = document.createElement('option');
        opt.value = room;
        opt.textContent = `/r/${room} (${rooms[room]})`;
        roomFilterSelect.appendChild(opt);
      });
    }
  }

  function renderMessagesFeed(messages) {
    const query = (messageFilterInput?.value || '').toLowerCase().trim();
    const selectedRoom = roomFilterSelect?.value || 'all';

    const filtered = messages.filter(msg => {
      if (selectedRoom !== 'all' && msg.room !== selectedRoom) return false;
      if (query && !msg.text.toLowerCase().includes(query) && !String(msg.seq).includes(query)) return false;
      return true;
    });

    if (ledgerCountBadge) {
      ledgerCountBadge.textContent = `${filtered.length} of ${messages.length} message${messages.length === 1 ? '' : 's'}`;
    }

    if (filtered.length === 0) {
      messagesFeedContainer.innerHTML = '<div class="text-center py-8 text-xs text-slate-500 italic">No messages match the selected filters.</div>';
      return;
    }

    messagesFeedContainer.innerHTML = filtered.map(msg => `
      <div class="p-3.5 rounded-xl bg-dark-950/70 border border-dark-800 hover:border-dark-700/80 transition-colors space-y-2">
        <div class="flex flex-wrap items-center justify-between gap-2 text-xs font-mono border-b border-dark-900 pb-2">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20 font-semibold">
              /r/${escapeHtml(msg.room)}
            </span>
            <span class="text-slate-400">Seq #${msg.seq}</span>
          </div>
          <div class="flex items-center gap-3 text-slate-500 text-[11px]">
            <span>Nonce: ${msg.nonce || '--'}</span>
            <span>${formatTimestamp(msg.ts)}</span>
          </div>
        </div>
        <p class="text-xs sm:text-sm text-slate-200 break-words leading-relaxed font-mono selection:bg-teal-900">
          ${highlightMessageText(msg.text)}
        </p>
      </div>
    `).join('');
  }

  // Filter Event Listeners
  if (messageFilterInput) {
    messageFilterInput.addEventListener('input', () => renderMessagesFeed(allMessages));
  }
  if (roomFilterSelect) {
    roomFilterSelect.addEventListener('change', () => renderMessagesFeed(allMessages));
  }

  // -------------------------------------------------------------------------
  // 5. Utility & Export Helpers
  // -------------------------------------------------------------------------
  if (copyDidBtn) {
    copyDidBtn.addEventListener('click', () => {
      const textToCopy = resDid.textContent.trim();
      navigator.clipboard.writeText(textToCopy).then(() => {
        const originalIcon = copyDidBtn.innerHTML;
        copyDidBtn.innerHTML = '<i data-lucide="check" class="w-4 h-4 text-emerald-400"></i>';
        lucide.createIcons();
        setTimeout(() => {
          copyDidBtn.innerHTML = originalIcon;
          lucide.createIcons();
        }, 1500);
      });
    });
  }

  if (btnExportJson) {
    btnExportJson.addEventListener('click', () => {
      if (!currentScanData) return;
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentScanData, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `technocore-agent-${currentScanData.fingerprint || 'scan'}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });
  }

  if (btnExportMd) {
    btnExportMd.addEventListener('click', () => {
      if (!currentScanData) return;
      const mdContent = generateMarkdownReport(currentScanData);
      const dataStr = "data:text/markdown;charset=utf-8," + encodeURIComponent(mdContent);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `technocore-audit-${currentScanData.fingerprint || 'report'}.md`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });
  }

  function generateMarkdownReport(data) {
    return `# Technocore Agent Intelligence & OSINT Audit Report

**Query DID:** \`${data.query_did}\`  
**SHA-256 Fingerprint:** \`${data.fingerprint}\`  
**Scan Timestamp (UTC):** ${data.scan_time_utc}  

---

## 1. Lifecycle Summary
- **First Seen (Creation):** ${data.lifecycle.first_seen ? `${data.lifecycle.first_seen.timestamp} (Seq #${data.lifecycle.first_seen.sequence} in /r/${data.lifecycle.first_seen.room})` : 'N/A'}
- **Last Active:** ${data.lifecycle.last_active ? `${data.lifecycle.last_active.timestamp} (Seq #${data.lifecycle.last_active.sequence} in /r/${data.lifecycle.last_active.room})` : 'N/A'}
- **Total Signed Messages:** ${data.lifecycle.total_signed_messages}
- **Nonces Used:** ${data.lifecycle.nonces_count}
- **Active Rooms:** ${Object.entries(data.lifecycle.rooms_active_in || {}).map(([r, c]) => `/r/${r} (${c})`).join(', ') || 'None'}

---

## 2. Attributed Human / Operator Identity
- **Likely Owner:** ${data.social_footprint.likely_owner ? `${data.social_footprint.likely_owner.handle} (${data.social_footprint.likely_owner.platform})` : 'Uncorrelated'}
- **Confidence:** ${data.social_footprint.likely_owner ? data.social_footprint.likely_owner.confidence : 'N/A'}
- **Attribution Reason:** ${data.social_footprint.likely_owner ? data.social_footprint.likely_owner.reason : 'N/A'}

---

## 3. Git Footprint & Proofs
${data.social_footprint.git_commits.length > 0 ? data.social_footprint.git_commits.map(c => `- Commit: \`${c.commit}\` in repository \`${c.repo}\``).join('\n') : '_No Git commit proofs found._'}

---

## 4. Message History (${data.activity_history.length} records)
${data.activity_history.map(m => `### Seq #${m.seq} | /r/${m.room} | ${m.ts}\n> ${m.text}\n`).join('\n')}
`;
  }

  function formatTimestamp(tsStr) {
    if (!tsStr) return '--';
    try {
      const d = new Date(tsStr);
      return d.toISOString().replace('T', ' ').replace('Z', ' UTC');
    } catch {
      return tsStr;
    }
  }

  function highlightMessageText(text) {
    let escaped = escapeHtml(text);
    escaped = escaped.replace(/(https?:\/\/[^\s<>"]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-teal-400 hover:underline">$1</a>');
    escaped = escaped.replace(/(@[A-Za-z0-9_]{1,15})/g, '<span class="text-indigo-300 font-bold">$1</span>');
    return escaped;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
});
