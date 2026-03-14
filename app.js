// ===== SECURITY: HTML sanitizer =====
function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ===== ADMIN CONFIG =====
const ADMIN_HASH = "5f4d142bf532ae9f1bf0fe956dca03ecf85d16b47b3c8391b53d574eb9b289f2";

async function hashPassword(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

// ===== STATE =====
let activeFilters = new Set();    // genre/category filters (horror, action, etc.)
let activeModeFilters = new Set(); // mode filters (mode_online, mode_local, players_2, etc.)
let searchQuery = '';
let sortMode = 'default'; // 'default' | 'trending' | 'rating' | 'az'
let wheelSpinning = false;
let isAdmin = false;

// ===== FILTER CONFIG =====
const genreFilters = [
  { id: 'all' },
  { id: 'trending' },
  { id: 'horror' },
  { id: 'action' },
  { id: 'puzzle' },
  { id: 'rpg' },
  { id: 'survival' },
  { id: 'factory' },
  { id: 'roguelike' },
  { id: 'sport' },
  { id: 'strategy' },
  { id: 'indie' },
  { id: 'free' },
];

const modeFilters = [
  { id: 'mode_online',    field: 'coopMode',  value: 'online' },
  { id: 'mode_local',     field: 'coopMode',  value: 'local' },
  { id: 'mode_split',     field: 'coopMode',  value: 'split' },
  { id: 'players_2',      field: 'maxPlayers', value: 2 },
  { id: 'players_4',      field: 'maxPlayers', value: 4 },
];

// Legacy alias for backward compat
const categories = genreFilters;

// ===== LOCALSTORAGE: carica override admin =====
function loadOverrides() {
  const stored = JSON.parse(localStorage.getItem('coopAdminData') || '{}');
  games.forEach(g => {
    const ov = stored[g.id];
    if (!ov) return;
    if (ov.personalNote !== undefined) g.personalNote = ov.personalNote;
    if (ov.played      !== undefined) g.played       = ov.played;
  });
}

function saveOverride(id, personalNote, played) {
  const stored = JSON.parse(localStorage.getItem('coopAdminData') || '{}');
  stored[id] = { personalNote, played };
  localStorage.setItem('coopAdminData', JSON.stringify(stored));
  const g = games.find(x => x.id === id);
  if (g) { g.personalNote = personalNote; g.played = played; }
}

function categoryLabel(category) {
  return t('cat_' + category);
}

const FREE_STORE_LABELS = {
  epic: 'Epic Games',
  steam: 'Steam',
  gog: 'GOG',
  humble: 'Humble Bundle',
};

let freeSectionTimer = null;
let freeBadgeTimer = null;

function normalizeTitle(title) {
  return (title || '').toLowerCase().trim().replace(/\s+/g, ' ');
}

function getFreeGamesData() {
  return typeof freeGames !== 'undefined' && Array.isArray(freeGames) ? freeGames : [];
}

function parseFreeUntil(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function getActiveFreeGames(now = new Date()) {
  return getFreeGamesData()
    .map(entry => {
      const expiresAt = parseFreeUntil(entry.freeUntil);
      return expiresAt ? { ...entry, expiresAt } : null;
    })
    .filter(entry =>
      entry &&
      entry.title &&
      entry.store &&
      entry.storeUrl &&
      entry.expiresAt.getTime() > now.getTime()
    )
    .sort((a, b) => a.expiresAt - b.expiresAt);
}

function getFreeCountdownState(expiresAt, now = new Date()) {
  const diff = expiresAt.getTime() - now.getTime();
  if (diff <= 0) return null;
  if (diff < 60 * 60 * 1000) {
    return { text: t('last_hour'), tone: 'last-hour' };
  }
  if (diff < 24 * 60 * 60 * 1000) {
    const hoursLeft = Math.max(1, Math.ceil(diff / (60 * 60 * 1000)));
    return { text: t('last_hours', hoursLeft), tone: 'urgent' };
  }
  const daysLeft = Math.max(1, Math.ceil(diff / (24 * 60 * 60 * 1000)));
  return { text: t('expires_in_days', daysLeft), tone: 'normal' };
}

function buildFreeGameLookup(now = new Date()) {
  const lookup = new Map();
  getActiveFreeGames(now).forEach(entry => {
    const key = normalizeTitle(entry.title);
    if (!lookup.has(key)) lookup.set(key, entry);
  });
  return lookup;
}

function renderFreeGameCard(entry) {
  const countdown = getFreeCountdownState(entry.expiresAt);
  if (!countdown) return '';
  const safeTitle = esc(entry.title);
  const safeStoreUrl = esc(entry.storeUrl);
  const safeImage = esc(entry.imageUrl || '');
  const storeKey = esc(entry.store);
  const storeLabel = FREE_STORE_LABELS[entry.store] || entry.store;

  return `
    <article class="free-card" data-store="${storeKey}">
      <div class="free-card-media">
        ${entry.imageUrl ? `<img class="free-card-img" src="${safeImage}" alt="${safeTitle}" loading="lazy" onerror="this.style.display='none'">` : '<div class="free-card-placeholder">🎁</div>'}
        <span class="free-store-badge store-${storeKey}">${storeLabel}</span>
      </div>
      <div class="free-card-body">
        <h3 class="free-card-title">${safeTitle}</h3>
        <p class="free-countdown ${countdown.tone}" aria-live="polite">${countdown.text}</p>
        <a class="btn-primary free-claim-btn" href="${safeStoreUrl}" target="_blank" rel="noopener noreferrer">${t('claim_free')}</a>
      </div>
    </article>`;
}

function scheduleFreeSectionRefresh(activeGames) {
  if (freeSectionTimer) clearTimeout(freeSectionTimer);
  if (!activeGames.length) return;
  const urgent = activeGames.some(entry => (entry.expiresAt.getTime() - Date.now()) < 60 * 60 * 1000);
  freeSectionTimer = window.setTimeout(() => renderFreeGamesSection(), urgent ? 1000 : 60000);
}

function scheduleFreeBadgeRefresh(activeGames) {
  if (freeBadgeTimer) clearTimeout(freeBadgeTimer);
  if (!activeGames.length) return;
  const msToNextMinute = 60000 - (Date.now() % 60000);
  freeBadgeTimer = window.setTimeout(() => {
    const refreshedGames = getActiveFreeGames();
    renderGames();
    scheduleFreeBadgeRefresh(refreshedGames);
  }, msToNextMinute);
}

function renderFreeGamesSection() {
  const section = document.getElementById('freeGamesSection');
  if (!section) return;

  const activeGames = getActiveFreeGames();
  if (!activeGames.length) {
    section.hidden = true;
    section.innerHTML = '';
    if (freeSectionTimer) clearTimeout(freeSectionTimer);
    if (freeBadgeTimer) clearTimeout(freeBadgeTimer);
    return;
  }

  section.hidden = false;
  section.innerHTML = `
    <div class="free-strip">
      <div class="free-strip-head">
        <div>
          <div class="free-strip-kicker">${t('free_now')}</div>
          <h2 class="free-strip-title">${t('free_now')}</h2>
        </div>
        <a class="free-strip-link" href="free.html">${t('see_all_offers')}</a>
      </div>
      <div class="free-rail" role="list">
        ${activeGames.map(renderFreeGameCard).join('')}
      </div>
    </div>`;

  scheduleFreeSectionRefresh(activeGames);
  scheduleFreeBadgeRefresh(activeGames);
}

// ===== FEATURED INDIE OF THE WEEK =====
function renderFeatured() {
  const section = document.getElementById('featuredSection');
  if (!section) return;
  if (typeof featuredIndieId === 'undefined' || !featuredIndieId) {
    section.innerHTML = '';
    return;
  }
  const game = games.find(g => g.id === featuredIndieId);
  if (!game) { section.innerHTML = ''; return; }
  const safeTitle = esc(game.title);
  const safeDesc = esc((currentLang === 'en' && game.description_en) ? game.description_en : game.description);
  const storeLinks = [
    game.steamUrl ? `<a class="btn-store btn-steam" href="${esc(game.steamUrl)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">Steam ↗</a>` : '',
    game.epicUrl  ? `<a class="btn-store btn-epic"  href="${esc(game.epicUrl)}"  target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">Epic ↗</a>`  : '',
    game.itchUrl  ? `<a class="btn-store btn-itch"  href="${esc(game.itchUrl)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">itch.io ↗</a>` : '',
  ].join('');
  section.innerHTML = `
    <div class="featured-section">
      <div class="featured-banner" onclick="openModal(${game.id})">
        ${game.image ? `<img class="featured-img" src="${esc(game.image)}" alt="${safeTitle}" onerror="this.style.display='none'" loading="lazy">` : ''}
        <div class="featured-info">
          <div class="featured-label">${t('featured_label')}</div>
          <div class="featured-title">${safeTitle}</div>
          <div class="featured-desc">${safeDesc}</div>
          <div class="featured-meta">
            ${game.rating > 0 ? `<span class="rating-badge rating-${ratingTier(game.rating)}">${ratingIcon(game.rating)} ${game.rating}%</span>` : ''}
            ${storeLinks}
          </div>
        </div>
      </div>
    </div>`;
}

async function waitForFreeGamesReady() {
  if (!window.freeGamesReady || typeof window.freeGamesReady.then !== 'function') return;
  try {
    await window.freeGamesReady;
  } catch (_) {
    // Fall back to an empty feed if the script fails to load.
  }
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', async () => {
  await waitForFreeGamesReady();
  loadOverrides();
  updateStats();
  renderFilters();
  renderFreeGamesSection();
  renderFeatured();
  renderGames();

  const searchInput = document.getElementById('searchInput');
  const searchClear = document.getElementById('searchClear');

  searchInput.addEventListener('input', e => {
    searchQuery = e.target.value.toLowerCase().trim();
    searchClear.style.display = e.target.value ? 'block' : 'none';
    renderGames();
  });

  searchClear.addEventListener('click', () => {
    searchInput.value = '';
    searchQuery = '';
    searchClear.style.display = 'none';
    searchInput.focus();
    renderGames();
  });

  document.getElementById('sortSelect').addEventListener('change', e => {
    sortMode = e.target.value;
    renderGames();
  });

  document.getElementById('wheelBtn').addEventListener('click', openWheel);

  document.getElementById('modalOverlay').addEventListener('click', e => {
    if (e.target === document.getElementById('modalOverlay')) closeModal();
  });
  document.getElementById('wheelOverlay').addEventListener('click', e => {
    if (e.target === document.getElementById('wheelOverlay')) closeWheelModal();
  });
  document.getElementById('adminOverlay').addEventListener('click', e => {
    if (e.target === document.getElementById('adminOverlay')) closeAdminModal();
  });

  document.getElementById('adminBtn').addEventListener('click', toggleAdmin);
  window.addEventListener('freegamesloaded', () => {
    renderFreeGamesSection();
    renderGames();
  });
});

// ===== STATS =====
function updateStats() {
  document.getElementById('totalGames').textContent = games.length;
  document.getElementById('playedGames').textContent = games.filter(g => g.played).length;
  const cats = new Set(games.flatMap(g => g.categories).filter(c => c !== 'trending'));
  document.getElementById('totalCats').textContent = cats.size;
}

// ===== FILTERS =====
function renderFilters() {
  const container = document.getElementById('filterContainer');
  const modeContainer = document.getElementById('modeFilterContainer');
  const allFiltersActive = activeFilters.size === 0;

  // Genre filters
  container.innerHTML = genreFilters.map(cat => `
    <button class="filter-btn ${(cat.id === 'all' && allFiltersActive) || activeFilters.has(cat.id) ? 'active' : ''}" data-cat="${cat.id}">
      ${t('cat_' + cat.id)}
    </button>
  `).join('');

  container.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cat = btn.dataset.cat;
      if (cat === 'all') {
        activeFilters.clear();
        container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      } else {
        container.querySelector('[data-cat="all"]').classList.remove('active');
        if (activeFilters.has(cat)) {
          activeFilters.delete(cat);
          btn.classList.remove('active');
        } else {
          activeFilters.add(cat);
          btn.classList.add('active');
        }
        if (activeFilters.size === 0)
          container.querySelector('[data-cat="all"]').classList.add('active');
      }
      renderGames();
    });
  });

  // Mode / player filters
  if (modeContainer) {
    const isMobile = window.innerWidth <= 600;

    modeContainer.innerHTML = modeFilters.map(f => `
      <button class="filter-btn filter-mode-btn ${activeModeFilters.has(f.id) ? 'active' : ''}" data-mode="${f.id}">
        ${t(f.id)}
      </button>
    `).join('');

    // On mobile, collapse mode filters behind a toggle
    if (isMobile) {
      modeContainer.classList.add('collapsed');
      let toggleBtn = modeContainer.parentElement.querySelector('.btn-toggle-filters');
      if (!toggleBtn) {
        toggleBtn = document.createElement('button');
        toggleBtn.className = 'btn-toggle-filters';
        modeContainer.parentElement.insertBefore(toggleBtn, modeContainer);
      }
      toggleBtn.textContent = t('mode_filters_toggle');
      toggleBtn.onclick = () => {
        const collapsed = modeContainer.classList.toggle('collapsed');
        toggleBtn.classList.toggle('active', !collapsed);
      };
    } else {
      modeContainer.classList.remove('collapsed');
      const toggleBtn = modeContainer.parentElement.querySelector('.btn-toggle-filters');
      if (toggleBtn) toggleBtn.remove();
    }

    modeContainer.querySelectorAll('.filter-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        if (activeModeFilters.has(mode)) {
          activeModeFilters.delete(mode);
          btn.classList.remove('active');
        } else {
          activeModeFilters.add(mode);
          btn.classList.add('active');
        }
        renderGames();
      });
    });
  }
}

// ===== FILTER + SORT LOGIC =====
function matchesModeFilters(game) {
  if (activeModeFilters.size === 0) return true;
  for (const modeId of activeModeFilters) {
    const filterDef = modeFilters.find(f => f.id === modeId);
    if (!filterDef) continue;
    if (filterDef.field === 'coopMode') {
      if (!game.coopMode || !game.coopMode.includes(filterDef.value)) return false;
    } else if (filterDef.field === 'maxPlayers') {
      if (filterDef.value === 2) {
        if (game.maxPlayers !== 2) return false;
      } else if (filterDef.value === 4) {
        if ((game.maxPlayers || 0) < 4) return false;
      }
    }
  }
  return true;
}

function getFilteredGames() {
  let filtered = games.filter(game => {
    // Genre/category filters
    if (activeFilters.has('trending') && !game.trending) return false;
    const normalFilters = [...activeFilters].filter(f => f !== 'trending');
    const matchesCat = normalFilters.length === 0 || game.categories.some(c => normalFilters.includes(c));
    // Mode/player filters (AND logic — must match ALL active mode filters)
    const matchesMode = matchesModeFilters(game);
    // Search
    const descriptions = [game.description, game.description_en]
      .filter(Boolean)
      .map(text => text.toLowerCase());
    const matchesSearch = !searchQuery ||
      game.title.toLowerCase().includes(searchQuery) ||
      descriptions.some(text => text.includes(searchQuery)) ||
      game.categories.some(c => c.includes(searchQuery));
    return matchesCat && matchesMode && matchesSearch;
  });

  if (sortMode === 'trending') {
    filtered = [...filtered].sort((a, b) => (b.ccu || 0) - (a.ccu || 0));
  } else if (sortMode === 'rating') {
    filtered = [...filtered].sort((a, b) => (b.rating || 0) - (a.rating || 0));
  } else if (sortMode === 'az') {
    filtered = [...filtered].sort((a, b) => a.title.localeCompare(b.title));
  }

  return filtered;
}

// ===== RENDER GAMES =====
function renderGames() {
  const filtered = getFilteredGames();
  const grid = document.getElementById('gamesGrid');
  const info = document.getElementById('resultsInfo');
  const freeLookup = buildFreeGameLookup();

  info.innerHTML = t('results_found', filtered.length, games.length);

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <svg width="64" height="64" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <h3>${t('empty_title')}</h3>
        <p>${t('empty_sub')}</p>
      </div>`;
    return;
  }

  grid.innerHTML = filtered.map(game => createCard(game, freeLookup.get(normalizeTitle(game.title)))).join('');

  grid.querySelectorAll('.card').forEach(card => {
    const id = parseInt(card.dataset.id);
    card.addEventListener('click', e => {
      if (e.target.closest('a') || e.target.closest('.btn-admin-edit')) return;
      openModal(id);
    });
    const editBtn = card.querySelector('.btn-admin-edit');
    if (editBtn) editBtn.addEventListener('click', e => { e.stopPropagation(); openAdminModal(id); });
  });
}

// ===== CREATE CARD =====
function createCard(game, freeEntry = null) {
  const tags = game.categories.map(c =>
    `<span class="tag tag-${c}">${categoryLabel(c)}</span>`
  ).join('');

  const safeTitle = esc(game.title);
  const safeDesc = esc((currentLang === 'en' && game.description_en) ? game.description_en : game.description);
  const safeNote = esc(game.personalNote);

  const imgHtml = game.image
    ? `<div class="card-img-wrapper"><img class="card-img" src="${esc(game.image)}" alt="${safeTitle}" loading="lazy"
         onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
       <div class="card-img-placeholder" style="display:none">🎮</div></div>`
    : `<div class="card-img-placeholder">🎮</div>`;

  const noteHtml = game.played && game.personalNote
    ? `<div class="personal-note-preview">${safeNote}</div>` : '';

  const storeButtons = [
    game.steamUrl ? `<a class="btn-store btn-steam" href="${esc(game.steamUrl)}" target="_blank" rel="noopener noreferrer">Steam ↗</a>` : '',
    game.epicUrl  ? `<a class="btn-store btn-epic"  href="${esc(game.epicUrl)}"  target="_blank" rel="noopener noreferrer">Epic ↗</a>`  : '',
    game.itchUrl  ? `<a class="btn-store btn-itch"  href="${esc(game.itchUrl)}" target="_blank" rel="noopener noreferrer">itch.io ↗</a>` : '',
  ].join('');

  const adminBtn = isAdmin
    ? `<button class="btn-admin-edit" title="${t('admin_edit_title')}">✏️</button>` : '';
  const freeBadge = freeEntry
    ? `<div class="free-now-badge ${isAdmin ? 'with-admin' : ''}">${t('free_now_badge')}</div>`
    : '';

  const trendingBadge = game.trending
    ? `<div class="trending-badge">${t('trending_badge')}</div>` : '';

  const ccuHtml = game.ccu > 0
    ? `<span class="ccu-badge" title="${t('ccu_title')}">👥 ${formatCCU(game.ccu)}</span>` : '';

  const ratingHtml = game.rating > 0
    ? `<span class="rating-badge rating-${ratingTier(game.rating)}" title="${game.rating}% ${t('modal_reviews')}">
        ${ratingIcon(game.rating)} ${game.rating}%
      </span>` : '';

  return `
    <div class="card ${isAdmin ? 'admin-mode' : ''} ${game.trending ? 'is-trending' : ''} ${freeEntry ? 'is-free-now' : ''}" data-id="${game.id}">
      ${adminBtn}
      ${freeBadge}
      ${trendingBadge}
      ${imgHtml}
      <div class="card-body">
        <div class="card-header">
          <div class="card-title">${safeTitle}</div>
          <div class="card-badges">
            ${game.played ? `<span class="played-badge">${t('played_badge')}</span>` : ''}
            ${ratingHtml}
            ${ccuHtml}
          </div>
        </div>
        <div class="card-tags">${tags}</div>
        <div class="players-info">
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0"/>
          </svg>
          ${game.players} ${t('card_players')}
        </div>
        <div class="card-desc">${safeDesc}</div>
        ${noteHtml}
      </div>
      <div class="card-footer">
        <a class="btn-details" href="games/${game.id}.html">${t('btn_details')}</a>
        <div class="store-btns">${storeButtons}</div>
      </div>
    </div>`;
}

function formatCCU(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return n.toString();
}

function ratingTier(r) {
  if (r >= 95) return 'acclaimed';
  if (r >= 85) return 'verypos';
  if (r >= 70) return 'positive';
  if (r >= 55) return 'mixed';
  return 'negative';
}

function ratingIcon(r) {
  if (r >= 95) return '🏆';
  if (r >= 85) return '😊';
  if (r >= 70) return '👍';
  if (r >= 55) return '😐';
  return '👎';
}

function ratingLabel(r) {
  if (r >= 95) return t('rating_acclaimed');
  if (r >= 85) return t('rating_verypos');
  if (r >= 70) return t('rating_positive');
  if (r >= 55) return t('rating_mixed');
  if (r >= 40) return t('rating_mediocre');
  return t('rating_negative');
}

// ===== MODAL DETTAGLIO =====
function openModal(id) {
  const game = games.find(g => g.id === id);
  if (!game) return;

  const safeTitle = esc(game.title);
  const safeDesc = esc((currentLang === 'en' && game.description_en) ? game.description_en : game.description);
  const safeNote = esc(game.personalNote);

  const tags = game.categories.map(c =>
    `<span class="tag tag-${c}">${categoryLabel(c)}</span>`
  ).join('');

  const noteHtml = game.played && game.personalNote ? `
    <div class="modal-personal-note">
      <div class="modal-section-title">${t('modal_experience')}</div>
      <p>${safeNote}</p>
    </div>` : '';

  const storeLinks = [
    game.steamUrl ? `<a class="btn-primary" href="${esc(game.steamUrl)}" target="_blank" rel="noopener noreferrer">Steam ↗</a>` : '',
    game.epicUrl  ? `<a class="btn-primary btn-epic-lg" href="${esc(game.epicUrl)}"  target="_blank" rel="noopener noreferrer">Epic Games ↗</a>` : '',
    game.itchUrl  ? `<a class="btn-store btn-itch" href="${esc(game.itchUrl)}" target="_blank" rel="noopener noreferrer" style="padding:10px 20px;font-size:0.9rem">itch.io ↗</a>` : '',
  ].join('');

  const adminEdit = isAdmin
    ? `<button class="btn-details" onclick="closeModal();openAdminModal(${id})" style="padding:10px 20px">${t('btn_edit')}</button>` : '';

  document.getElementById('modalContent').innerHTML = `
    ${game.image ? `<img class="modal-img" src="${esc(game.image)}" alt="${safeTitle}">` : ''}
    <div class="modal-body">
      <div class="modal-header">
        <div class="modal-title">${safeTitle} ${game.played ? `<span class="played-badge">${t('played_badge')}</span>` : ''}</div>
        <button class="modal-close" onclick="closeModal()" aria-label="${t('btn_close_aria')}">✕</button>
      </div>
      <div class="modal-tags">${tags}</div>
      ${game.rating > 0 ? `
      <div>
        <div class="modal-section-title">${t('modal_reviews')}</div>
        <div class="modal-rating-row">
          <span class="modal-rating-badge rating-${ratingTier(game.rating)}">
            ${ratingIcon(game.rating)} ${game.rating}% — ${ratingLabel(game.rating)}
          </span>
        </div>
      </div>` : ''}
      <div>
        <div class="modal-section-title">${t('modal_players')}</div>
        <div class="modal-desc">
          ${esc(game.players)} ${t('card_players')}
          ${game.ccu > 0 ? `<span class="modal-ccu">— <strong>${formatCCU(game.ccu)}</strong> ${t('modal_online')}</span>` : ''}
          ${game.trending ? `<span class="modal-trending-label">${t('modal_trending')}</span>` : ''}
        </div>
      </div>
      <div>
        <div class="modal-section-title">${t('modal_desc')}</div>
        <div class="modal-desc">${safeDesc}</div>
      </div>
      ${noteHtml}
      <div class="modal-actions">
        ${storeLinks}
        <a class="btn-details" href="games/${id}.html" style="padding:10px 20px;text-decoration:none">${t('btn_game_page')}</a>
        ${adminEdit}
        <button class="btn-details" onclick="closeModal()" style="padding:10px 20px">${t('btn_close')}</button>
      </div>
    </div>`;

  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

window.addEventListener('langchange', renderFreeGamesSection);

// ===== ADMIN TOGGLE =====
async function toggleAdmin() {
  if (isAdmin) {
    isAdmin = false;
    document.getElementById('adminBtn').textContent = t('btn_admin');
    document.getElementById('adminBtn').classList.remove('admin-active');
    renderGames();
    return;
  }
  const pwd = prompt(t('admin_pwd_prompt'));
  if (pwd === null) return;
  const hash = await hashPassword(pwd);
  if (hash === ADMIN_HASH) {
    isAdmin = true;
    document.getElementById('adminBtn').textContent = t('btn_admin_on');
    document.getElementById('adminBtn').classList.add('admin-active');
    renderGames();
  } else {
    alert(t('admin_pwd_wrong'));
  }
}

// ===== ADMIN MODAL (modifica nota/played) =====
function openAdminModal(id) {
  const game = games.find(g => g.id === id);
  if (!game || !isAdmin) return;

  document.getElementById('adminGameTitle').textContent = game.title;
  document.getElementById('adminNoteInput').value = game.personalNote || '';
  document.getElementById('adminPlayedInput').checked = game.played || false;
  document.getElementById('adminGameId').value = id;

  document.getElementById('adminOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeAdminModal() {
  document.getElementById('adminOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function saveAdminEdit() {
  const id       = parseInt(document.getElementById('adminGameId').value);
  const note     = document.getElementById('adminNoteInput').value.trim();
  const played   = document.getElementById('adminPlayedInput').checked;
  saveOverride(id, note, played);
  closeAdminModal();
  updateStats();
  renderGames();
}

// ===== WHEEL =====
const WHEEL_COLORS = [
  '#6c63ff','#ff6584','#43e97b','#f7971e','#21d4fd',
  '#a18cd1','#fda085','#84fab0','#f093fb','#4facfe',
  '#43e97b','#fa709a','#fee140','#30cfd0','#667eea'
];

function openWheel() {
  const filtered = getFilteredGames();
  if (filtered.length === 0) return;
  const overlay = document.getElementById('wheelOverlay');
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
  document.getElementById('wheelResult').classList.remove('show');
  document.getElementById('spinBtn').disabled = false;
  drawWheel(filtered, 0);
}

function closeWheelModal() {
  document.getElementById('wheelOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function drawWheel(gameList, rotation) {
  const canvas = document.getElementById('wheelCanvas');
  const dpr = window.devicePixelRatio || 1;
  const size = canvas.offsetWidth || 320;
  canvas.width = size * dpr;
  canvas.height = size * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const cx = size / 2, cy = size / 2, r = size / 2 - 4;
  const n = gameList.length;
  const arc = (2 * Math.PI) / n;

  for (let i = 0; i < n; i++) {
    const start = rotation + i * arc - Math.PI / 2;
    const end = start + arc;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, end);
    ctx.closePath();
    ctx.fillStyle = WHEEL_COLORS[i % WHEEL_COLORS.length];
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.3)';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(start + arc / 2);
    ctx.textAlign = 'right';
    ctx.fillStyle = '#fff';
    ctx.font = `bold ${Math.max(10, Math.min(13, 180 / n))}px sans-serif`;
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 3;
    const label = gameList[i].title.length > 14
      ? gameList[i].title.slice(0, 13) + '…'
      : gameList[i].title;
    ctx.fillText(label, r - 10, 5);
    ctx.restore();
  }

  ctx.beginPath();
  ctx.arc(cx, cy, 22, 0, Math.PI * 2);
  ctx.fillStyle = '#0d0f14';
  ctx.fill();
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = 2;
  ctx.stroke();
}

function spinWheel() {
  if (wheelSpinning) return;
  const filtered = getFilteredGames();
  if (filtered.length === 0) return;

  wheelSpinning = true;
  document.getElementById('spinBtn').disabled = true;
  document.getElementById('wheelResult').classList.remove('show');

  const extraSpins = 6 + Math.random() * 6;
  const winIndex = Math.floor(Math.random() * filtered.length);
  const arc = (2 * Math.PI) / filtered.length;
  const targetAngle = 2 * Math.PI * extraSpins - (winIndex * arc) - arc / 2;
  let start = null, currentRot = 0;
  const duration = 4000 + Math.random() * 1500;

  function easeOut(t_) { return 1 - Math.pow(1 - t_, 4); }

  function animate(ts) {
    if (!start) start = ts;
    const progress = Math.min((ts - start) / duration, 1);
    currentRot = easeOut(progress) * targetAngle;
    drawWheel(filtered, currentRot);
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      wheelSpinning = false;
      document.getElementById('spinBtn').disabled = false;
      const winner = filtered[winIndex];
      document.getElementById('wheelResultTitle').textContent = winner.title;
      document.getElementById('wheelResultSub').textContent =
        winner.categories.join(', ') + ' · ' + winner.players + ' ' + t('wheel_players');
      document.getElementById('wheelResult').classList.add('show');
    }
  }
  requestAnimationFrame(animate);
}

// Close on ESC
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeWheelModal(); closeAdminModal(); }
});

// ===== SCROLL TO TOP =====
(function() {
  const btn = document.getElementById('scrollTopBtn');
  if (!btn) return;
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

// ===== TOOLBAR SCROLL EFFECT =====
(function() {
  const toolbar = document.querySelector('.toolbar');
  if (!toolbar) return;
  window.addEventListener('scroll', () => {
    toolbar.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
})();

// ===== CARD STAGGER ANIMATION =====
(function() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationDelay = entry.target.dataset.delay || '0s';
        entry.target.classList.add('card-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });

  const orig = renderGames;
  renderGames = function() {
    orig();
    document.querySelectorAll('.card').forEach((card, i) => {
      card.style.animationDelay = `${i * 0.04}s`;
      observer.observe(card);
    });
  };
})();

// Particles are now loaded from particles.js
