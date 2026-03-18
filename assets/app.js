// ===== SECURITY: HTML sanitizer =====
function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ===== STATE =====
let activeFilters = new Set();    // genre/category filters (horror, action, etc.)
let activeModeFilters = new Set(); // mode filters (mode_online, mode_local, players_2, etc.)
let searchQuery = '';
let sortMode = 'default'; // 'default' | 'trending' | 'rating' | 'az'
let wheelSpinning = false;
let catalogGames = [];
let featuredIndieGameId = null;
let legacyCatalogScriptPromise = null;

// ===== PLAYED GAMES + NOTE PERSONALI =====
const PLAYED_KEY = 'coophubs_played';
const NOTES_KEY  = 'coophubs_notes';
let showPlayed = false;

function getNotes() { return JSON.parse(localStorage.getItem(NOTES_KEY) || '{}'); }
function getNote(id)  { return getNotes()[String(id)] || ''; }
function saveNote(id, text) {
  const notes = getNotes();
  if (text.trim()) notes[String(id)] = text.trim(); else delete notes[String(id)];
  localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
  renderGames();
}

// ===== FILTER CONFIG =====
const filterSpecial = [{ id: 'all' }, { id: 'trending' }];
const filterGenres  = [
  { id: 'horror' }, { id: 'action' }, { id: 'puzzle' }, { id: 'rpg' },
  { id: 'survival' }, { id: 'factory' }, { id: 'roguelike' }, { id: 'sport' },
  { id: 'strategy' }, { id: 'indie' },
];
const filterFree    = [{ id: 'free' }];
const genreFilters  = [...filterSpecial, ...filterGenres, ...filterFree]; // alias legacy

const modeFilters = [
  { id: 'mode_online',    field: 'coopMode',  value: 'online' },
  { id: 'mode_local',     field: 'coopMode',  value: 'local' },
  { id: 'mode_split',     field: 'coopMode',  value: 'split' },
  { id: 'mode_crossplay', field: 'crossplay', value: true },
  { id: 'players_2',      field: 'maxPlayers', value: 2 },
  { id: 'players_4',      field: 'maxPlayers', value: 4 },
];

// Legacy alias for backward compat
const categories = genreFilters;

// ===== PLAYED HELPERS =====
function getPlayed() { return new Set(JSON.parse(localStorage.getItem(PLAYED_KEY) || '[]')); }
function isPlayed(id) { return getPlayed().has(id); }
function togglePlayed(id) {
  const p = getPlayed();
  p.has(id) ? p.delete(id) : p.add(id);
  localStorage.setItem(PLAYED_KEY, JSON.stringify([...p]));
  renderGames();
  updatePlayedBadge();
}
function toggleShowPlayed() {
  showPlayed = !showPlayed;
  renderGames();
  updatePlayedBadge();
}
function updatePlayedBadge() {
  const badge = document.getElementById('playedBadge');
  if (!badge) return;
  const count = getPlayed().size;
  if (count === 0) { badge.style.display = 'none'; return; }
  badge.style.display = '';
  if (showPlayed) {
    badge.innerHTML = `<button class="played-hide-btn" onclick="toggleShowPlayed()">${t('played_hide')}</button>`;
  } else {
    badge.innerHTML = `<span class="played-count">${count} ${t('played_hidden')}</span> <button class="played-hide-btn" onclick="toggleShowPlayed()">${t('played_show')}</button>`;
  }
}

function getLegacyCatalogFallback() {
  return {
    games: Array.isArray(window.games) ? window.games : [],
    featuredIndieId: Number.isInteger(window.featuredIndieId) ? window.featuredIndieId : null,
  };
}

async function loadLegacyCatalogScript() {
  const existing = getLegacyCatalogFallback();
  if (existing.games.length) return existing;
  if (legacyCatalogScriptPromise) {
    await legacyCatalogScriptPromise;
    return getLegacyCatalogFallback();
  }

  const cacheBucket = Math.floor(Date.now() / 300000);
  legacyCatalogScriptPromise = new Promise(resolve => {
    const script = document.createElement('script');
    script.src = `games.js?v=${cacheBucket}`;
    script.async = true;
    script.onload = resolve;
    script.onerror = resolve;
    document.head.appendChild(script);
  });

  await legacyCatalogScriptPromise;
  return getLegacyCatalogFallback();
}

async function loadCatalogData() {
  const fallback = getLegacyCatalogFallback();
  catalogGames = fallback.games;
  featuredIndieGameId = fallback.featuredIndieId;
  window.catalogGames = catalogGames;

  const cacheBucket = Math.floor(Date.now() / 300000);
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 4000);

  try {
    const response = await fetch(`data/catalog.public.v1.json?v=${cacheBucket}`, {
      cache: 'no-store',
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const payload = await response.json();
    if (!payload || !Array.isArray(payload.games)) {
      throw new Error('Invalid public catalog payload');
    }

    catalogGames = payload.games;
    featuredIndieGameId = Number.isInteger(payload.featuredIndieId) ? payload.featuredIndieId : null;
    window.catalogGames = catalogGames;
    window.dispatchEvent(new Event('catalogloaded'));
  } catch (error) {
    const legacy = await loadLegacyCatalogScript();
    catalogGames = legacy.games;
    featuredIndieGameId = legacy.featuredIndieId;
    window.catalogGames = catalogGames;
    console.warn('Catalog export unavailable, using legacy games.js fallback.', error);
    window.dispatchEvent(new Event('catalogfallback'));
  } finally {
    window.clearTimeout(timeoutId);
  }
}

// ===== LOCALSTORAGE: stub (sistema admin note/played rimosso) =====
function loadOverrides() { /* note e giocati ora gestiti dal sistema pubblico */ }

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
    <article class="free-card" data-store="${storeKey}" role="listitem">
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
  freeSectionTimer = window.setTimeout(() => renderFreeGamesSection(), urgent ? 30000 : 300000);
}

function scheduleFreeBadgeRefresh(activeGames) {
  if (freeBadgeTimer) clearTimeout(freeBadgeTimer);
  if (!activeGames.length) return;
  freeBadgeTimer = window.setTimeout(() => {
    const refreshedGames = getActiveFreeGames();
    renderGames();
    scheduleFreeBadgeRefresh(refreshedGames);
  }, 300000);
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
  if (!featuredIndieGameId) {
    section.innerHTML = '';
    return;
  }
  const game = catalogGames.find(g => g.id === featuredIndieGameId);
  if (!game) { section.innerHTML = ''; return; }
  const safeTitle = esc(game.title);
  const safeDesc = esc((currentLang === 'en' && game.description_en) ? game.description_en : game.description);
  const storeLinks = [
    game.steamUrl ? `<a class="btn-store btn-steam" href="${esc(addUtm(game.steamUrl, 'featured'))}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">Steam ↗</a>` : '',
    game.epicUrl  ? `<a class="btn-store btn-epic"  href="${esc(addUtm(game.epicUrl, 'featured'))}"  target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">Epic ↗</a>`  : '',
    game.itchUrl  ? `<a class="btn-store btn-itch"  href="${esc(addUtm(game.itchUrl, 'featured'))}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">itch.io ↗</a>` : '',
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
  await Promise.all([waitForFreeGamesReady(), loadCatalogData()]);
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
  window.addEventListener('freegamesloaded', () => {
    renderFreeGamesSection();
    renderGames();
  });
});

// ===== STATS =====
function updateStats() {
  document.getElementById('totalGames').textContent = catalogGames.length;
  document.getElementById('playedGames').textContent = getPlayed().size;
  const cats = new Set(catalogGames.flatMap(g => g.categories).filter(c => c !== 'trending'));
  document.getElementById('totalCats').textContent = cats.size;
}

// ===== FILTERS =====
function renderFilters() {
  const container = document.getElementById('filterContainer');
  const modeContainer = document.getElementById('modeFilterContainer');
  const allFiltersActive = activeFilters.size === 0;

  // Genre filters — gruppi separati
  const btnHtml = (cat) =>
    `<button class="filter-btn ${(cat.id === 'all' && allFiltersActive) || activeFilters.has(cat.id) ? 'active' : ''}" data-cat="${cat.id}">${t('cat_' + cat.id)}</button>`;

  container.innerHTML = `
    <div class="filter-group filter-group-special">${filterSpecial.map(btnHtml).join('')}</div>
    <div class="filter-group">
      <span class="filter-group-label">${t('filter_genre')}</span>
      ${filterGenres.map(btnHtml).join('')}
    </div>
    <div class="filter-group">
      <span class="filter-group-label">${t('filter_other')}</span>
      ${filterFree.map(btnHtml).join('')}
    </div>`;

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

    modeContainer.innerHTML = `
      <div class="filter-group">
        <span class="filter-group-label">${t('filter_mode')}</span>
        ${modeFilters.map(f => `<button class="filter-btn filter-mode-btn ${activeModeFilters.has(f.id) ? 'active' : ''}" data-mode="${f.id}">${t(f.id)}</button>`).join('')}
      </div>`;

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
    } else if (filterDef.field === 'crossplay') {
      if (!game.crossplay) return false;
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
  let filtered = catalogGames.filter(game => {
    // Nascondi giochi già giocati (a meno che showPlayed non sia attivo)
    if (!showPlayed && isPlayed(game.id)) return false;
    // Genre/category filters
    if (activeFilters.has('trending') && !game.trending) return false;
    const normalFilters = [...activeFilters].filter(f => f !== 'trending');
    // AND logic: il gioco deve avere TUTTE le categorie selezionate
    const matchesCat = normalFilters.length === 0 || normalFilters.every(c => game.categories.includes(c));
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

  info.innerHTML = t('results_found', filtered.length, catalogGames.length);
  updatePlayedBadge();

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

  const BATCH_SIZE = 30;
  const cards = filtered.map((game, i) => createCard(game, freeLookup.get(normalizeTitle(game.title)), i));

  // Render first batch immediately
  grid.innerHTML = cards.slice(0, BATCH_SIZE).join('');
  attachCardListeners(grid);

  // Render remaining cards in batches via requestIdleCallback
  let offset = BATCH_SIZE;
  function renderNextBatch() {
    if (offset >= cards.length) return;
    const batch = cards.slice(offset, offset + BATCH_SIZE);
    grid.insertAdjacentHTML('beforeend', batch.join(''));
    // Attach listeners only to new cards
    const allCards = grid.querySelectorAll('.card');
    for (let i = offset; i < Math.min(offset + BATCH_SIZE, allCards.length); i++) {
      attachSingleCardListener(allCards[i]);
    }
    offset += BATCH_SIZE;
    if (offset < cards.length) {
      (window.requestIdleCallback || requestAnimationFrame)(renderNextBatch);
    }
  }
  if (offset < cards.length) {
    (window.requestIdleCallback || requestAnimationFrame)(renderNextBatch);
  }
}

function attachSingleCardListener(card) {
  const id = parseInt(card.dataset.id);
  card.addEventListener('click', e => {
    if (e.target.closest('a') || e.target.closest('.btn-played-toggle') || e.target.closest('.btn-note-card')) return;
    openModal(id);
  });
  const playedBtn = card.querySelector('.btn-played-toggle');
  if (playedBtn) playedBtn.addEventListener('click', e => { e.stopPropagation(); togglePlayed(id); });
  card.querySelectorAll('.btn-note-card').forEach(btn => {
    btn.addEventListener('click', e => { e.stopPropagation(); openModal(parseInt(btn.dataset.openModal)); });
  });
}

function attachCardListeners(grid) {
  grid.querySelectorAll('.card').forEach(attachSingleCardListener);
}

// ===== AFFILIATE CONFIG =====
// Inserisci i tuoi ID qui dopo la registrazione ai programmi affiliati.
// Epic: epicgames.com/affiliate → ottieni il tuo Creator Code
// GOG:  gog.com/partner         → ottieni il tuo pp= ID
const AFFILIATE = {
  epic: '',   // es. 'COOPHUBS' → aggiunge ?creator=COOPHUBS
  gog:  '',   // es. '12345'    → aggiunge ?pp=12345
  // Attivi (link di ricerca per gioco):
  ig:   'gamer-ddc4a8',                          // Instant Gaming
  gb:   'fb308ca0-647e-4ce7-9e80-74c2c591eac1',  // GameBillet
  gmg:  'https://greenmangaming.sjv.io/qWzoQy',  // Green Man Gaming (Impact)
  gameseal: 'https://www.tkqlhce.com/click-101708519-17170422', // Gameseal (CJ Affiliate)
};

// ===== UTM TRACKING + AFFILIATE =====
function buildAffiliateBtns(game) {
  if (!AFFILIATE.ig && !AFFILIATE.gb && !AFFILIATE.gmg && !AFFILIATE.gameseal) return '';
  // Giochi gratuiti: nessun link di acquisto affiliato
  if (game.categories && game.categories.includes('free')) return '';
  const q = encodeURIComponent(game.title);
  const btns = [];

  // Instant Gaming: usa link diretto se disponibile in games.js, altrimenti ricerca
  if (AFFILIATE.ig) {
    const igUrl = game.igUrl
      ? game.igUrl
      : `https://www.instant-gaming.com/en/search/?query=${q}&igr=${AFFILIATE.ig}`;
    const discBadge = game.igDiscount > 0
      ? `<span class="affiliate-discount">-${game.igDiscount}%</span>` : '';
    btns.push(`<a class="btn-affiliate btn-ig" href="${esc(igUrl)}" target="_blank" rel="noopener noreferrer sponsored"><span class="affiliate-store">Instant Gaming</span>${discBadge}</a>`);
  }

  // GameBillet: usa link diretto se disponibile, altrimenti ricerca
  if (AFFILIATE.gb) {
    const gbUrl = game.gbUrl
      ? game.gbUrl
      : `https://www.gamebillet.com/search?q=${q}&affiliate=${AFFILIATE.gb}`;
    const gbBadge = game.gbDiscount > 0
      ? `<span class="affiliate-discount">-${game.gbDiscount}%</span>` : '';
    btns.push(`<a class="btn-affiliate btn-gb" href="${esc(gbUrl)}" target="_blank" rel="noopener noreferrer sponsored"><span class="affiliate-store">GameBillet</span>${gbBadge}</a>`);
  }

  // Green Man Gaming: deep link via Impact (sjv.io) — search per titolo
  if (AFFILIATE.gmg && game.steamUrl) {
    const gmgSearch = `https://www.greenmangaming.com/search/?query=${q}`;
    const gmgUrl = `${AFFILIATE.gmg}?u=${encodeURIComponent(gmgSearch)}`;
    btns.push(`<a class="btn-affiliate btn-gmg" href="${esc(gmgUrl)}" target="_blank" rel="noopener noreferrer sponsored"><span class="affiliate-store">Green Man Gaming</span></a>`);
  }

  // Gameseal: link diretto se disponibile, altrimenti search via CJ Affiliate
  if (AFFILIATE.gameseal && game.steamUrl) {
    let gsUrl;
    if (game.gsUrl) {
      gsUrl = game.gsUrl; // link diretto al prodotto (con tracking CJ già incluso)
    } else {
      const gsSearch = `https://gameseal.com/search?search=${q}`;
      gsUrl = `${AFFILIATE.gameseal}?url=${encodeURIComponent(gsSearch)}`;
    }
    const gsBadge = game.gsDiscount ? `<span class="affiliate-discount">-${game.gsDiscount}%</span>` : '';
    btns.push(`<a class="btn-affiliate btn-gameseal" href="${esc(gsUrl)}" target="_blank" rel="noopener noreferrer sponsored"><span class="affiliate-store">Gameseal</span>${gsBadge}</a>`);
  }

  return `<div class="affiliate-section"><div class="affiliate-title">💸 Prezzi alternativi</div><div class="affiliate-btns">${btns.join('')}</div></div>`;
}

function addUtm(url, campaign = 'catalog') {
  if (!url) return '';
  const sep = url.includes('?') ? '&' : '?';
  let result = url + sep + 'utm_source=coophubs&utm_medium=referral&utm_campaign=' + campaign;

  // Aggiungi parametro affiliato se configurato
  if (AFFILIATE.epic && url.includes('epicgames.com')) {
    result += '&creator=' + AFFILIATE.epic;
  }
  if (AFFILIATE.gog && (url.includes('gog.com'))) {
    result += '&pp=' + AFFILIATE.gog;
  }

  return result;
}

// ===== CREATE CARD =====
function createCard(game, freeEntry = null, cardIndex = 99) {
  const tags = game.categories.map(c =>
    `<span class="tag tag-${c}">${categoryLabel(c)}</span>`
  ).join('');

  const safeTitle = esc(game.title);
  const safeDesc = esc((currentLang === 'en' && game.description_en) ? game.description_en : game.description);

  const imgLoading = cardIndex < 6 ? 'eager' : 'lazy';
  const imgHtml = game.image
    ? `<div class="card-img-wrapper"><img class="card-img" src="${esc(game.image)}" alt="${safeTitle}" loading="${imgLoading}" width="460" height="215" decoding="async"
         onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
       <div class="card-img-placeholder" style="display:none">🎮</div></div>`
    : `<div class="card-img-placeholder">🎮</div>`;

  const publicNote = getNote(game.id);
  const noteHtml = isPlayed(game.id) && publicNote
    ? `<div class="personal-note-preview">${esc(publicNote)}</div>` : '';
  const noteBtn = isPlayed(game.id)
    ? `<button class="btn-note-card" data-open-modal="${game.id}" title="${t('note_title')}">✎ ${t('note_title')}</button>`
    : '';

  // Bottone principale: IG → Steam → GOG come fallback
  const isFreeGame = game.categories && game.categories.includes('free');
  let primaryBtn = '';
  if (!isFreeGame && game.igUrl && AFFILIATE.ig) {
    const discLabel = game.igDiscount > 0 ? ` -${game.igDiscount}%` : '';
    primaryBtn = `<a class="btn-store btn-ig-card" href="${esc(game.igUrl)}" target="_blank" rel="noopener noreferrer sponsored">Instant Gaming${discLabel} ↗</a>`;
  } else if (game.steamUrl) {
    primaryBtn = `<a class="btn-store btn-steam" href="${esc(addUtm(game.steamUrl))}" target="_blank" rel="noopener noreferrer">Steam ↗</a>`;
  } else if (game.gogUrl) {
    const gogHref = AFFILIATE.gog ? addUtm(game.gogUrl) + '&pp=' + AFFILIATE.gog : addUtm(game.gogUrl);
    primaryBtn = `<a class="btn-store btn-gog" href="${esc(gogHref)}" target="_blank" rel="noopener noreferrer">GOG ↗</a>`;
  }
  const gbBtn = (!isFreeGame && game.gbUrl && AFFILIATE.gb)
    ? `<a class="btn-store btn-gb-card" href="${esc(game.gbUrl)}" target="_blank" rel="noopener noreferrer sponsored">GameBillet${game.gbDiscount > 0 ? ` -${game.gbDiscount}%` : ''} ↗</a>`
    : '';
  const storeButtons = [
    primaryBtn,
    gbBtn,
    game.epicUrl ? `<a class="btn-store btn-epic" href="${esc(addUtm(game.epicUrl))}" target="_blank" rel="noopener noreferrer">Epic ↗</a>` : '',
    game.itchUrl ? `<a class="btn-store btn-itch" href="${esc(addUtm(game.itchUrl))}" target="_blank" rel="noopener noreferrer">itch.io ↗</a>` : '',
  ].join('');

  const playedToggle = isPlayed(game.id)
    ? `<button class="btn-played-toggle is-played" data-played-id="${game.id}" title="${t('played_unmark')}">✓</button>`
    : `<button class="btn-played-toggle" data-played-id="${game.id}" title="${t('played_mark')}">✓</button>`;
  const freeBadge = freeEntry
    ? `<div class="free-now-badge">${t('free_now_badge')}</div>`
    : '';

  const trendingBadge = game.trending
    ? `<div class="trending-badge">${t('trending_badge')}</div>` : '';

  const ccuHtml = game.ccu > 0
    ? `<span class="ccu-badge" title="${t('ccu_title')}">👥 ${formatCCU(game.ccu)}</span>` : '';

  const ratingHtml = game.rating > 0
    ? `<span class="rating-badge rating-${ratingTier(game.rating)}" title="${game.rating}% ${t('modal_reviews')}">
        ${ratingIcon(game.rating)} ${game.rating}%
      </span>` : '';

  const crossplayHtml = game.crossplay
    ? `<span class="crossplay-badge">${t('mode_crossplay')}</span>` : '';

  return `
    <div class="card ${game.trending ? 'is-trending' : ''} ${freeEntry ? 'is-free-now' : ''} ${showPlayed && isPlayed(game.id) ? 'is-played-card' : ''}" data-id="${game.id}" role="listitem">
      ${playedToggle}
      ${freeBadge}
      ${trendingBadge}
      ${imgHtml}
      <div class="card-body">
        <div class="card-header">
          <div class="card-title">${safeTitle}</div>
          <div class="card-badges">
            ${isPlayed(game.id) ? `<span class="played-badge">${t('played_badge')}</span>` : ''}
            ${ratingHtml}
            ${ccuHtml}
            ${crossplayHtml}
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
        ${noteBtn}
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
  const game = catalogGames.find(g => g.id === id);
  if (!game) return;

  const safeTitle = esc(game.title);
  const safeDesc = esc((currentLang === 'en' && game.description_en) ? game.description_en : game.description);

  const tags = game.categories.map(c =>
    `<span class="tag tag-${c}">${categoryLabel(c)}</span>`
  ).join('');

  const publicNote = getNote(id);
  const noteHtml = isPlayed(id) ? `
    <div class="modal-personal-note">
      <div class="modal-section-title">${t('note_title')}</div>
      <textarea class="admin-textarea note-public-textarea" id="noteTextarea${id}" placeholder="${t('note_placeholder')}" maxlength="1000">${esc(publicNote)}</textarea>
      <button class="btn-details" onclick="saveNote(${id}, document.getElementById('noteTextarea${id}').value)" style="margin-top:8px;padding:8px 16px;font-size:0.82rem">${t('note_save')}</button>
    </div>` : '';

  const storeLinks = [
    game.steamUrl ? `<a class="btn-primary" href="${esc(addUtm(game.steamUrl, 'modal'))}" target="_blank" rel="noopener noreferrer">Steam ↗</a>` : '',
    game.epicUrl  ? `<a class="btn-primary btn-epic-lg" href="${esc(addUtm(game.epicUrl, 'modal'))}"  target="_blank" rel="noopener noreferrer">Epic Games ↗</a>` : '',
    game.itchUrl  ? `<a class="btn-store btn-itch" href="${esc(addUtm(game.itchUrl, 'modal'))}" target="_blank" rel="noopener noreferrer" style="padding:10px 20px;font-size:0.9rem">itch.io ↗</a>` : '',
  ].join('');
  const priceCompare = game.steamUrl ? buildAffiliateBtns(game) : '';


  document.getElementById('modalContent').innerHTML = `
    ${game.image ? `<img class="modal-img" src="${esc(game.image)}" alt="${safeTitle}" width="460" height="215" decoding="async">` : ''}
    <div class="modal-body">
      <div class="modal-header">
        <div class="modal-title">${safeTitle} ${isPlayed(id) ? `<span class="played-badge">${t('played_badge')}</span>` : ''}</div>
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
          ${game.crossplay ? `<span class="modal-crossplay-badge">${t('mode_crossplay')}</span>` : ''}
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
        <button class="btn-details btn-played-modal ${isPlayed(id) ? 'is-played' : ''}" onclick="togglePlayed(${id});closeModal()" style="padding:10px 20px">${isPlayed(id) ? t('played_unmark') : t('played_mark')}</button>
        <button class="btn-details" onclick="closeModal()" style="padding:10px 20px">${t('btn_close')}</button>
      </div>
      ${priceCompare}
    </div>`;

  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

window.addEventListener('langchange', renderFreeGamesSection);


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
      const resultEl = document.getElementById('wheelResult');
      document.getElementById('wheelResultTitle').textContent = winner.title;
      document.getElementById('wheelResultSub').textContent =
        winner.categories.join(', ') + ' · ' + winner.players + ' ' + t('wheel_players');
      resultEl.classList.add('show');
      resultEl.style.cursor = 'pointer';
      resultEl.dataset.tapHint = t('wheel_tap_hint');
      const openWinner = () => { closeWheelModal(); openModal(winner.id); };
      resultEl.onclick = openWinner;
      resultEl.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') openWinner(); };
    }
  }
  requestAnimationFrame(animate);
}

// Close on ESC
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeWheelModal(); }
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
