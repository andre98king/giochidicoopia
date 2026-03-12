// ===== TRANSLATIONS =====
const TRANSLATIONS = {
  it: {
    // Hero
    hero_sub: "Tutti i migliori giochi cooperativi per PC, categorizzati e commentati",
    stat_games: "Giochi",
    stat_played: "Giocati da me",
    stat_cats: "Categorie",
    // Toolbar
    search_placeholder: "Cerca un gioco...",
    sort_default: "📋 Default",
    sort_rating: "⭐ Meglio recensiti",
    sort_trending: "🔥 Più giocati ora",
    sort_az: "🔤 A → Z",
    btn_wheel: "🎡 Gioco Random",
    btn_admin: "🔒 Admin",
    btn_admin_on: "🔓 Admin ON",
    btn_lang: "🇬🇧 EN",
    // Categories
    cat_all: "🎮 Tutti",
    cat_trending: "🔥 Trending",
    cat_horror: "👻 Horror",
    cat_action: "⚔️ Action",
    cat_puzzle: "🧩 Puzzle",
    cat_splitscreen: "🖥️ Splitscreen",
    cat_rpg: "🐉 RPG",
    cat_survival: "🪓 Survival",
    cat_factory: "🏭 Factory",
    cat_roguelike: "🎲 Roguelike",
    cat_sport: "⚽ Sport",
    cat_strategy: "♟️ Strategy",
    cat_indie: "🎮 Indie",
    cat_free: "🆓 Gratis",
    // Featured
    featured_label: "🌟 GIOCO INDIE DELLA SETTIMANA",
    // Results
    results_found: (n, total) => `Trovati <span>${n}</span> giochi su ${total}`,
    // Empty state
    empty_title: "Nessun gioco trovato",
    empty_sub: "Prova a cambiare i filtri o la ricerca",
    // Card
    played_badge: "✓ Giocato",
    card_players: "giocatori",
    btn_details: "Dettagli →",
    ccu_title: "Giocatori online ora",
    trending_badge: "🔥 Trending",
    // Modal
    modal_reviews: "⭐ Recensioni Steam",
    modal_players: "👥 Giocatori",
    modal_desc: "📖 Descrizione",
    modal_experience: "📝 La mia esperienza",
    modal_online: "online ora",
    modal_trending: "🔥 Trending",
    btn_close: "Chiudi",
    btn_edit: "✏️ Modifica",
    // Rating labels
    rating_acclaimed: "Acclamato",
    rating_verypos: "Molto Positivo",
    rating_positive: "Positivo",
    rating_mixed: "Nella Norma",
    rating_mediocre: "Misto",
    rating_negative: "Negativo",
    // Admin
    admin_pwd_prompt: "Password admin:",
    admin_pwd_wrong: "Password errata.",
    admin_played_title: "✓ Hai giocato questo gioco?",
    admin_played_label: "Segna come giocato",
    admin_note_title: "📝 La tua nota personale",
    admin_note_placeholder: "Scrivi la tua esperienza personale con questo gioco...",
    btn_save: "💾 Salva",
    btn_cancel: "Annulla",
    // Wheel
    wheel_title: "🎡 Ruota Gioco Random",
    btn_spin: "🎰 Gira la Ruota!",
    wheel_players: "giocatori",
    footer_sub: "Scopri il tuo prossimo gioco co-op",
  },
  en: {
    // Hero
    hero_sub: "The best co-op games for PC, categorized and reviewed",
    stat_games: "Games",
    stat_played: "Played by me",
    stat_cats: "Categories",
    // Toolbar
    search_placeholder: "Search a game...",
    sort_default: "📋 Default",
    sort_rating: "⭐ Best rated",
    sort_trending: "🔥 Most played now",
    sort_az: "🔤 A → Z",
    btn_wheel: "🎡 Random Game",
    btn_admin: "🔒 Admin",
    btn_admin_on: "🔓 Admin ON",
    btn_lang: "🇮🇹 IT",
    // Categories
    cat_all: "🎮 All",
    cat_trending: "🔥 Trending",
    cat_horror: "👻 Horror",
    cat_action: "⚔️ Action",
    cat_puzzle: "🧩 Puzzle",
    cat_splitscreen: "🖥️ Splitscreen",
    cat_rpg: "🐉 RPG",
    cat_survival: "🪓 Survival",
    cat_factory: "🏭 Factory",
    cat_roguelike: "🎲 Roguelike",
    cat_sport: "⚽ Sport",
    cat_strategy: "♟️ Strategy",
    cat_indie: "🎮 Indie",
    cat_free: "🆓 Free",
    // Featured
    featured_label: "🌟 INDIE GAME OF THE WEEK",
    // Results
    results_found: (n, total) => `Found <span>${n}</span> games out of ${total}`,
    // Empty state
    empty_title: "No games found",
    empty_sub: "Try changing filters or search",
    // Card
    played_badge: "✓ Played",
    card_players: "players",
    btn_details: "Details →",
    ccu_title: "Players online now",
    trending_badge: "🔥 Trending",
    // Modal
    modal_reviews: "⭐ Steam Reviews",
    modal_players: "👥 Players",
    modal_desc: "📖 Description",
    modal_experience: "📝 My experience",
    modal_online: "online now",
    modal_trending: "🔥 Trending",
    btn_close: "Close",
    btn_edit: "✏️ Edit",
    // Rating labels
    rating_acclaimed: "Overwhelmingly Positive",
    rating_verypos: "Very Positive",
    rating_positive: "Mostly Positive",
    rating_mixed: "Mixed",
    rating_mediocre: "Mostly Negative",
    rating_negative: "Overwhelmingly Negative",
    // Admin
    admin_pwd_prompt: "Admin password:",
    admin_pwd_wrong: "Wrong password.",
    admin_played_title: "✓ Have you played this game?",
    admin_played_label: "Mark as played",
    admin_note_title: "📝 Your personal note",
    admin_note_placeholder: "Write your personal experience with this game...",
    btn_save: "💾 Save",
    btn_cancel: "Cancel",
    // Wheel
    wheel_title: "🎡 Random Game Wheel",
    btn_spin: "🎰 Spin the Wheel!",
    wheel_players: "players",
    footer_sub: "Find your next co-op game",
  }
};

// ===== CURRENT LANG =====
let currentLang = localStorage.getItem('coopLang') || 'it';

// ===== TRANSLATE HELPER =====
function t(key, ...args) {
  const dict = TRANSLATIONS[currentLang] || TRANSLATIONS['it'];
  const val = dict[key] !== undefined ? dict[key] : TRANSLATIONS['it'][key];
  if (val === undefined) return key;
  if (typeof val === 'function') return val(...args);
  return val;
}

// ===== SET LANGUAGE =====
function setLang(lang) {
  currentLang = lang;
  localStorage.setItem('coopLang', lang);
  document.documentElement.lang = lang;
  applyStaticTranslations();
  // Re-render dynamic content (defined in app.js)
  renderFilters();
  renderGames();
  updateStats();
  if (typeof renderFeatured === 'function') renderFeatured();
}

// ===== APPLY STATIC TRANSLATIONS =====
function applyStaticTranslations() {
  // Hero
  const heroSub = document.getElementById('heroSub');
  if (heroSub) heroSub.textContent = t('hero_sub');

  // Stat labels
  const statLabels = document.querySelectorAll('.stat-label');
  const statKeys = ['stat_games', 'stat_played', 'stat_cats'];
  statLabels.forEach((el, i) => { if (statKeys[i]) el.textContent = t(statKeys[i]); });

  // Search
  const search = document.getElementById('searchInput');
  if (search) search.placeholder = t('search_placeholder');

  // Sort options
  const sortMap = { default: 'sort_default', rating: 'sort_rating', trending: 'sort_trending', az: 'sort_az' };
  document.querySelectorAll('#sortSelect option').forEach(opt => {
    if (sortMap[opt.value]) opt.textContent = t(sortMap[opt.value]);
  });

  // Buttons
  const wheelBtn = document.getElementById('wheelBtn');
  if (wheelBtn) wheelBtn.textContent = t('btn_wheel');

  const langBtn = document.getElementById('langBtn');
  if (langBtn) langBtn.textContent = t('btn_lang');

  const adminBtn = document.getElementById('adminBtn');
  if (adminBtn) adminBtn.textContent = (typeof isAdmin !== 'undefined' && isAdmin) ? t('btn_admin_on') : t('btn_admin');

  // Wheel modal
  const wheelTitle = document.getElementById('wheelTitle');
  if (wheelTitle) wheelTitle.textContent = t('wheel_title');
  const spinBtn = document.getElementById('spinBtn');
  if (spinBtn) spinBtn.textContent = t('btn_spin');

  // Admin modal
  const adminPlayedTitle = document.getElementById('adminPlayedTitle');
  if (adminPlayedTitle) adminPlayedTitle.textContent = t('admin_played_title');
  const adminPlayedLabel = document.getElementById('adminPlayedLabel');
  if (adminPlayedLabel) adminPlayedLabel.textContent = t('admin_played_label');
  const adminNoteTitle = document.getElementById('adminNoteTitle');
  if (adminNoteTitle) adminNoteTitle.textContent = t('admin_note_title');
  const adminNoteInput = document.getElementById('adminNoteInput');
  if (adminNoteInput) adminNoteInput.placeholder = t('admin_note_placeholder');
  const adminSaveBtn = document.getElementById('adminSaveBtn');
  if (adminSaveBtn) adminSaveBtn.textContent = t('btn_save');
  const adminCancelBtn = document.getElementById('adminCancelBtn');
  if (adminCancelBtn) adminCancelBtn.textContent = t('btn_cancel');

  // Footer
  const footerSub = document.getElementById('footerSub');
  if (footerSub) footerSub.textContent = t('footer_sub');
}
