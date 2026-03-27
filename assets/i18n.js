// ===== TRANSLATIONS =====
const TRANSLATIONS = {
  it: {
    // Shared metadata
    home_meta_title: "Giochi Co-op PC — 551 Giochi Cooperativi Online e Locali | CoopHubs",
    home_meta_description: "Catalogo di 551 giochi co-op per PC: online, locale e split-screen. Filtra per genere, modalità e numero di giocatori. Prezzi, sconti e recensioni Steam.",
    about_meta_title: "Sul progetto — Coophubs",
    about_meta_description: "Coophubs è un progetto indipendente dedicato alla scoperta di videogiochi cooperativi per PC, con informazioni chiare e un catalogo in continuo aggiornamento.",
    contact_meta_title: "Contatti — Coophubs",
    contact_meta_description: "Contatti di Coophubs per segnalazioni, suggerimenti di giochi cooperativi e proposte di miglioramento del sito.",
    free_meta_title: "Giochi Gratis — Coophubs",
    free_meta_description: "Offerte gratuite attive su Epic Games, Steam, GOG e Humble Bundle con countdown in tempo reale e link diretti per riscattarle.",
    privacy_meta_title: "Privacy Policy — Coophubs",
    privacy_meta_description: "Informativa privacy di Coophubs: preferenze salvate in locale, nessun analytics attivo e link esterni verso store di terze parti.",

    // Hero
    hero_sub: "Tutti i migliori giochi cooperativi per PC, categorizzati e commentati",
    stat_games: "Giochi",
    stat_played: "Giocati da me",
    stat_cats: "Categorie",

    // Toolbar and shared UI
    skip_to_content: "Vai al contenuto principale",
    toolbar_aria: "Filtri e ricerca",
    search_placeholder: "Cerca un gioco...",
    search_aria: "Cerca un gioco",
    clear_search_aria: "Cancella ricerca",
    filters_category_aria: "Filtri per categoria",
    filters_mode_aria: "Filtri per modalità",
    mode_filters_toggle: "⚙ Filtri modalità",
    genre_filters_toggle: "🏷 Filtri genere",
    sort_aria: "Ordina giochi",
    sort_default: "📋 Predefinito",
    sort_rating: "⭐ Meglio recensiti",
    sort_trending: "🔥 Più giocati ora",
    sort_newest: "🆕 Più recenti",
    sort_az: "🔤 A → Z",
    year_filter_aria: "Filtra per anno",
    year_all: "📅 Tutti gli anni",
    year_2024: "📅 2024–2025",
    year_2020: "📅 2020–2023",
    year_2015: "📅 2015–2019",
    year_classic: "📅 Prima del 2015",
    btn_wheel: "🎡 Gioco Random",
    btn_wheel_aria: "Gioco random",
    btn_admin: "🔒 Admin",
    btn_admin_on: "🔓 Admin ON",
    btn_admin_aria: "Modalità admin",
    btn_lang: "🇬🇧 EN",
    btn_lang_aria: "Cambia lingua",
    btn_close_aria: "Chiudi",
    featured_section_aria: "Gioco indie della settimana",
    free_section_aria: "Offerte gratuite attive",
    modal_game_aria: "Dettaglio gioco",
    modal_edit_aria: "Modifica gioco",
    modal_random_aria: "Ruota gioco random",
    wheel_canvas_aria: "Ruota della fortuna",
    scroll_top_aria: "Torna su",

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

    // Co-op mode filters
    mode_online: "🌐 Online Co-op",
    mode_local: "🛋️ Local Co-op",
    mode_split: "🖥️ Splitscreen",
    mode_crossplay: "🔄 Crossplay",

    // Player count filters
    players_2: "👫 Per 2",
    players_4: "👥 Per 4+",

    // Filter group labels
    filter_genre: "Genere",
    filter_mode: "Modalità",
    filter_other: "Altro",

    // Generic page labels
    page_back_catalog: "← Torna al catalogo",
    page_back_site: "← Torna al sito",

    // Game page
    max_players: "Max giocatori",
    game_not_found_title: "Gioco non trovato",
    game_not_found_desc: "Il gioco richiesto non esiste nel database.",
    game_not_found_page_title: "Gioco non trovato — Coophubs",
    game_not_found_meta_desc: "La scheda gioco richiesta non è disponibile su Coophubs.",

    // Featured
    featured_label: "🌟 GIOCO INDIE DELLA SETTIMANA",
    free_now: "Gratis Ora",
    free_title: "Giochi Gratis",
    free_subtitle: "Offerte attive su Epic Games, Steam, GOG e Humble Bundle con scadenza aggiornata in tempo reale.",
    expires_in_days: (n) => `Scade tra ${n} giorni`,
    last_hours: (n) => `Ultime ${n}h!`,
    last_hour: "Ultima ora!",
    claim_free: "Riscatta gratis",
    see_all_offers: "Vedi tutte le offerte",
    no_free_games: "Nessuna offerta gratuita al momento. Torna domani!",
    free_now_badge: "Gratis ora!",

    // Results
    results_found: (n, total) => `Trovati <span>${n}</span> giochi su ${total}`,

    // Empty state
    empty_title: "Nessun gioco trovato",
    empty_sub: "Prova a cambiare i filtri o la ricerca",

    // Card — played feature
    played_badge: "✓ Giocato",
    played_mark: "✓ Giocato",
    played_unmark: "✕ Rimuovi dai giocati",
    played_hidden: "nascosti",
    played_show: "Mostra",
    played_hide: "Nascondi giocati",
    // Note personali (pubbliche)
    note_title: "📝 La mia esperienza",
    note_placeholder: "Scrivi la tua esperienza con questo gioco...",
    note_save: "💾 Salva nota",
    card_players: "giocatori",
    btn_details: "Dettagli →",
    btn_buy: "Compra",
    ccu_title: "Giocatori online ora",
    trending_badge: "🔥 Trending",

    // Modal
    modal_reviews: "⭐ Recensioni Steam",
    modal_players: "👥 Giocatori",
    modal_desc: "📖 Descrizione",
    modal_experience: "📝 La mia esperienza",
    modal_online: "online ora",
    modal_trending: "🔥 Trending",
    modal_alt_prices: "Prezzi alternativi",
    btn_close: "Chiudi",
    btn_game_page: "🔗 Pagina gioco",
    admin_edit_title: "Modifica nota",
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
    wheel_tap_hint: "Tocca per vedere i dettagli",

    // Footer
    footer_sub: "Coophubs è un progetto indipendente dedicato alla scoperta di giochi cooperativi per PC.",
    footer_about: "Sul progetto",
    footer_contact: "Contatti",
    footer_free: "Giochi gratis",
    footer_privacy: "Privacy Policy",
    footer_kofi: "☕ Supporta il progetto",
    support_strip_text: "Questo sito è gratuito e senza pubblicità. Se ti è utile, offrimi un caffè ☕",
    footer_copy: "© 2026 Co-op Games Hub — Immagini © rispettivi publisher — Dati da Steam & SteamSpy",

    // About page
    about_title: "Sul progetto",
    about_subtitle: "Un progetto indipendente dedicato alla scoperta di videogiochi cooperativi per PC.",
    about_p1: "Coophubs è un progetto indipendente dedicato alla scoperta di videogiochi cooperativi per PC. L'obiettivo è semplice: rendere più facile trovare giochi co-op adatti ai propri gusti, con informazioni chiare su modalità di gioco, numero di giocatori, generi e altri dettagli utili.",
    about_p2: "Il sito nasce dall'idea che trovare buoni giochi cooperativi non dovrebbe essere complicato. Spesso le informazioni sono sparse, incomplete o poco immediate da consultare. Coophubs prova a raccoglierle in un unico posto, con un'interfaccia semplice, veloce e pensata per aiutare chi vuole scegliere cosa giocare insieme ad altri.",
    about_p3: "Il database viene aggiornato nel tempo e può evolversi con nuovi giochi, correzioni ai dati esistenti e miglioramenti alle funzionalità del sito. L'obiettivo non è solo mostrare un elenco di titoli, ma costruire uno strumento realmente utile per chi cerca nuove esperienze cooperative da giocare con amici, partner o gruppi.",
    about_p4: "Coophubs è un progetto in crescita e continuerà a migliorare progressivamente. Alcune informazioni possono cambiare nel tempo, ma l'idea di fondo resta la stessa: offrire un punto di riferimento semplice e utile per chi ama i giochi co-op.",
    about_p5_html: "Se vuoi segnalare un errore, suggerire un gioco o proporre un miglioramento, puoi contattare il progetto tramite la <a href='contact.html'>pagina Contatti</a>.",

    // Contact page
    contact_title: "Contatti",
    contact_subtitle: "Un canale semplice per segnalazioni, suggerimenti e miglioramenti utili al progetto.",
    contact_p1: "Vuoi segnalare un errore, suggerire un gioco da aggiungere o proporre un miglioramento per il sito? Coophubs è un progetto indipendente in crescita, quindi feedback e segnalazioni possono essere molto utili.",
    contact_p2: "Per contattare il progetto puoi scrivere a:",
    contact_list_intro: "Messaggi utili possono riguardare:",
    contact_li_1: "dati errati o incompleti su un gioco",
    contact_li_2: "suggerimenti di nuovi giochi cooperativi",
    contact_li_3: "problemi tecnici del sito",
    contact_li_4: "proposte di collaborazione o miglioramento",
    contact_p3: "Le segnalazioni pertinenti aiuteranno a migliorare il database e rendere il sito più utile nel tempo.",

    // Privacy page
    privacy_title: "Privacy Policy",
    privacy_date: "Ultimo aggiornamento: Marzo 2026",
    privacy_h1: "1. Titolare del trattamento",
    privacy_p1_html: "Co-op Games Hub (di seguito \"il Sito\") è un progetto personale. Per richieste relative a privacy o contenuti puoi usare i recapiti presenti nella <a href='contact.html'>pagina Contatti</a>.",
    privacy_h2: "2. Cosa fa il sito oggi",
    privacy_p2: "Coophubs è un sito statico informativo dedicato ai giochi cooperativi per PC. Non prevede account utente, aree riservate con registrazione, commenti pubblici, newsletter o moduli di raccolta dati direttamente sul sito.",
    privacy_h3: "3. Dati trattati",
    privacy_p3: "Il Sito tratta solo i dati strettamente necessari al funzionamento della pagina e alcune preferenze salvate localmente nel browser:",
    privacy_li_1_html: "<strong>Preferenza lingua:</strong> viene salvata localmente tramite <code>localStorage</code> con la chiave <code>coopLang</code>.",
    privacy_li_2_html: "<strong>Note e stato “giocato”:</strong> se usi la modalità admin locale, le tue note personali e lo stato dei giochi vengono salvati nel browser tramite <code>localStorage</code> con la chiave <code>coopAdminData</code>.",
    privacy_li_3_html: "<strong>Dati tecnici di consegna:</strong> come per qualsiasi sito web statico, l'infrastruttura di hosting o CDN può trattare dati tecnici di richiesta come indirizzo IP, user-agent, data e ora, per consegnare i file e proteggere il servizio.",
    privacy_p4_html: "Le preferenze salvate in <code>localStorage</code> restano nel tuo browser e non vengono inviate da Coophubs a un backend proprietario, perché il sito non dispone di un server applicativo dedicato.",
    privacy_h4: "4. Cookie, analytics e profilazione",
    privacy_p5_html: "Al momento Coophubs <strong>non integra strumenti di analytics, pixel pubblicitari o sistemi di profilazione</strong> lato applicazione.",
    privacy_li_4_html: "<strong>Nessun analytics attivo:</strong> il sito non carica oggi script come Google Analytics, Plausible, Umami o strumenti equivalenti.",
    privacy_li_5_html: "<strong>Nessun cookie opzionale del sito:</strong> Coophubs non imposta attualmente cookie di marketing o di misurazione propri.",
    privacy_li_6_html: "<strong>Storage locale:</strong> le preferenze descritte sopra vengono salvate tramite <code>localStorage</code>, che puoi cancellare in qualsiasi momento dalle impostazioni del browser.",
    privacy_p6: "Se in futuro verranno introdotti analytics, funzioni affiliate tracciate o altri strumenti non essenziali, questa pagina verrà aggiornata prima o contestualmente alla loro attivazione.",
    privacy_h5: "5. Link esterni e link affiliati",
    privacy_p7: "Il Sito contiene link diretti verso piattaforme di terze parti come Steam, Epic Games e itch.io. Quando clicchi uno di questi link lasci Coophubs e si applicano le privacy policy delle rispettive piattaforme.",
    privacy_p8: "Alcuni link verso store di giochi possono essere link affiliati (es. Instant Gaming, GameBillet, Green Man Gaming, Gameseal). Se acquisti un gioco tramite uno di questi link, Coophubs può ricevere una piccola commissione senza alcun costo aggiuntivo per te. I link affiliati sono contrassegnati con rel=\"sponsored\". Le valutazioni e i contenuti del sito sono indipendenti da qualsiasi relazione commerciale.",
    privacy_h6: "6. Proprietà intellettuale e immagini",
    privacy_p10_ip: "I contenuti originali del sito (testi, descrizioni, codice, design) sono di proprietà di Co-op Games Hub e protetti da copyright. Le immagini dei giochi provengono dalla CDN pubblica di Steam e sono di proprietà dei rispettivi publisher. I dati di gioco (titoli, valutazioni, CCU) provengono da Steam, SteamSpy e itch.io e appartengono ai rispettivi titolari.",
    privacy_h7: "7. Controllo da parte dell'utente",
    privacy_p9_html: "Puoi gestire o cancellare in autonomia i dati salvati localmente dal sito eliminando il <code>localStorage</code> del browser per questo dominio. In questo modo verranno rimossi la lingua preferita e le eventuali note personali salvate in locale.",
    privacy_h8: "8. Sicurezza",
    privacy_p10: "Il Sito è servito tramite HTTPS. Coophubs non raccoglie direttamente dati di pagamento, documenti identificativi o credenziali utente archiviate lato server.",
    privacy_h9: "9. Modifiche",
    privacy_p11: "Questa informativa può essere aggiornata nel tempo per riflettere cambiamenti tecnici o organizzativi del progetto. La data di ultimo aggiornamento è indicata in alto.",
  },

  en: {
    // Shared metadata
    home_meta_title: "PC Co-op Games — 551 Cooperative Games Online & Local | CoopHubs",
    home_meta_description: "Catalog of 551 PC co-op games: online, local and split-screen. Filter by genre, mode and player count. Prices, discounts and Steam ratings.",
    about_meta_title: "About the project — Coophubs",
    about_meta_description: "Coophubs is an independent project focused on discovering co-op PC games, with clear information and a catalog that keeps improving over time.",
    contact_meta_title: "Contact — Coophubs",
    contact_meta_description: "Contact Coophubs for bug reports, co-op game suggestions, and ideas to improve the site.",
    free_meta_title: "Free Games — Coophubs",
    free_meta_description: "Active free offers on Epic Games, Steam, GOG, and Humble Bundle with live countdowns and direct claim links.",
    privacy_meta_title: "Privacy Policy — Coophubs",
    privacy_meta_description: "Coophubs privacy policy: local browser preferences, no active analytics, and outbound links to third-party game stores.",

    // Hero
    hero_sub: "The best co-op games for PC, categorized and reviewed",
    stat_games: "Games",
    stat_played: "Played by me",
    stat_cats: "Categories",

    // Toolbar and shared UI
    skip_to_content: "Skip to main content",
    toolbar_aria: "Filters and search",
    search_placeholder: "Search a game...",
    search_aria: "Search a game",
    clear_search_aria: "Clear search",
    filters_category_aria: "Category filters",
    filters_mode_aria: "Mode filters",
    mode_filters_toggle: "⚙ Mode filters",
    genre_filters_toggle: "🏷 Genre filters",
    sort_aria: "Sort games",
    sort_default: "📋 Default",
    sort_rating: "⭐ Best rated",
    sort_trending: "🔥 Most played now",
    sort_newest: "🆕 Newest",
    sort_az: "🔤 A → Z",
    year_filter_aria: "Filter by year",
    year_all: "📅 All years",
    year_2024: "📅 2024–2025",
    year_2020: "📅 2020–2023",
    year_2015: "📅 2015–2019",
    year_classic: "📅 Before 2015",
    btn_wheel: "🎡 Random Game",
    btn_wheel_aria: "Random game",
    btn_admin: "🔒 Admin",
    btn_admin_on: "🔓 Admin ON",
    btn_admin_aria: "Admin mode",
    btn_lang: "🇮🇹 IT",
    btn_lang_aria: "Change language",
    btn_close_aria: "Close",
    featured_section_aria: "Indie game of the week",
    free_section_aria: "Active free offers",
    modal_game_aria: "Game details",
    modal_edit_aria: "Edit game",
    modal_random_aria: "Random game wheel",
    wheel_canvas_aria: "Wheel of fortune",
    scroll_top_aria: "Back to top",

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

    // Co-op mode filters
    mode_online: "🌐 Online Co-op",
    mode_local: "🛋️ Local Co-op",
    mode_split: "🖥️ Splitscreen",
    mode_crossplay: "🔄 Crossplay",

    // Player count filters
    players_2: "👫 For 2",
    players_4: "👥 For 4+",

    // Filter group labels
    filter_genre: "Genre",
    filter_mode: "Mode",
    filter_other: "Other",

    // Generic page labels
    page_back_catalog: "← Back to catalog",
    page_back_site: "← Back to site",

    // Game page
    max_players: "Max players",
    game_not_found_title: "Game not found",
    game_not_found_desc: "The requested game does not exist in the database.",
    game_not_found_page_title: "Game not found — Coophubs",
    game_not_found_meta_desc: "The requested game page is not available on Coophubs.",

    // Featured
    featured_label: "🌟 INDIE GAME OF THE WEEK",
    free_now: "Free Now",
    free_title: "Free Games",
    free_subtitle: "Active offers on Epic Games, Steam, GOG, and Humble Bundle with live expiry countdowns.",
    expires_in_days: (n) => `Expires in ${n} days`,
    last_hours: (n) => `Last ${n}h!`,
    last_hour: "Last hour!",
    claim_free: "Claim free",
    see_all_offers: "See all offers",
    no_free_games: "No free offers right now. Check back tomorrow!",
    free_now_badge: "Free now!",

    // Results
    results_found: (n, total) => `Found <span>${n}</span> games out of ${total}`,

    // Empty state
    empty_title: "No games found",
    empty_sub: "Try changing filters or search",

    // Card — played feature
    played_badge: "✓ Played",
    played_mark: "✓ Played",
    played_unmark: "✕ Remove from played",
    played_hidden: "hidden",
    played_show: "Show",
    played_hide: "Hide played",
    // Personal notes (public)
    note_title: "📝 My experience",
    note_placeholder: "Write your experience with this game...",
    note_save: "💾 Save note",
    card_players: "players",
    btn_details: "Details →",
    btn_buy: "Buy",
    ccu_title: "Players online now",
    trending_badge: "🔥 Trending",

    // Modal
    modal_reviews: "⭐ Steam Reviews",
    modal_players: "👥 Players",
    modal_desc: "📖 Description",
    modal_experience: "📝 My experience",
    modal_online: "online now",
    modal_trending: "🔥 Trending",
    modal_alt_prices: "Alternative prices",
    btn_close: "Close",
    btn_game_page: "🔗 Game page",
    admin_edit_title: "Edit note",
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
    wheel_tap_hint: "Tap to see details",

    // Footer
    footer_sub: "Coophubs is an independent project dedicated to discovering co-op games for PC.",
    footer_about: "About",
    footer_contact: "Contact",
    footer_free: "Free games",
    footer_privacy: "Privacy Policy",
    footer_kofi: "☕ Support the project",
    support_strip_text: "This site is free and ad-free. If you find it useful, buy me a coffee ☕",
    footer_copy: "© 2026 Co-op Games Hub — Images © respective publishers — Data from Steam & SteamSpy",

    // About page
    about_title: "About the project",
    about_subtitle: "An independent project dedicated to discovering co-op PC games.",
    about_p1: "Coophubs is an independent project dedicated to discovering co-op PC games. The goal is simple: make it easier to find co-op games that match your taste, with clear information about play modes, player counts, genres, and other useful details.",
    about_p2: "The site started from a simple idea: finding good co-op games should not be complicated. Information is often scattered, incomplete, or slow to evaluate. Coophubs tries to gather it in one place, with a simple and fast interface designed to help people choose what to play together.",
    about_p3: "The catalog is updated over time and can evolve with new games, corrections to existing data, and improvements to site features. The goal is not just to show a list of titles, but to build a genuinely useful tool for anyone looking for new co-op experiences to play with friends, partners, or groups.",
    about_p4: "Coophubs is a growing project and will keep improving gradually. Some information may change over time, but the core idea stays the same: offer a simple and useful reference point for people who love co-op games.",
    about_p5_html: "If you want to report an error, suggest a game, or propose an improvement, you can contact the project through the <a href='contact.html'>Contact page</a>.",

    // Contact page
    contact_title: "Contact",
    contact_subtitle: "A simple channel for reports, suggestions, and useful improvements to the project.",
    contact_p1: "Want to report an error, suggest a game to add, or propose an improvement for the site? Coophubs is an independent project in progress, so thoughtful feedback can be genuinely useful.",
    contact_p2: "You can contact the project at:",
    contact_list_intro: "Useful messages can include:",
    contact_li_1: "incorrect or incomplete game data",
    contact_li_2: "suggestions for new co-op games",
    contact_li_3: "technical issues on the site",
    contact_li_4: "collaboration or improvement proposals",
    contact_p3: "Relevant reports will help improve the catalog and make the site more useful over time.",

    // Privacy page
    privacy_title: "Privacy Policy",
    privacy_date: "Last updated: March 2026",
    privacy_h1: "1. Data controller",
    privacy_p1_html: "Co-op Games Hub (the \"Site\") is a personal project. For privacy or content-related requests you can use the details listed on the <a href='contact.html'>Contact page</a>.",
    privacy_h2: "2. What the site does today",
    privacy_p2: "Coophubs is a static informational site focused on co-op PC games. It does not provide user accounts, sign-up areas, public comments, newsletters, or forms that directly collect data on the site.",
    privacy_h3: "3. Data processed",
    privacy_p3: "The Site only processes data strictly required to serve the page and a few preferences stored locally in the browser:",
    privacy_li_1_html: "<strong>Language preference:</strong> stored locally through <code>localStorage</code> under the key <code>coopLang</code>.",
    privacy_li_2_html: "<strong>Personal notes and “played” status:</strong> if you use the local admin mode, your notes and played flags are stored in the browser through <code>localStorage</code> under the key <code>coopAdminData</code>.",
    privacy_li_3_html: "<strong>Technical delivery data:</strong> as with any static website, the hosting or CDN infrastructure may process technical request data such as IP address, user agent, date, and time in order to deliver files and protect the service.",
    privacy_p4_html: "Preferences saved in <code>localStorage</code> remain in your browser and are not sent by Coophubs to a proprietary backend, because the site does not run its own application server.",
    privacy_h4: "4. Cookies, analytics, and profiling",
    privacy_p5_html: "At the moment Coophubs <strong>does not integrate analytics tools, advertising pixels, or profiling systems</strong> at the application level.",
    privacy_li_4_html: "<strong>No active analytics:</strong> the site does not currently load scripts such as Google Analytics, Plausible, Umami, or equivalent tools.",
    privacy_li_5_html: "<strong>No optional site cookies:</strong> Coophubs does not currently set its own marketing or measurement cookies.",
    privacy_li_6_html: "<strong>Local storage:</strong> the preferences described above are stored through <code>localStorage</code>, which you can clear at any time from your browser settings.",
    privacy_p6: "If analytics, tracked affiliate features, or other non-essential tools are introduced in the future, this page will be updated before or at the same time as their activation.",
    privacy_h5: "5. External links and affiliate links",
    privacy_p7: "The Site contains direct links to third-party platforms such as Steam, Epic Games, and itch.io. When you click one of those links you leave Coophubs and the privacy policies of those platforms apply.",
    privacy_p8: "Some links to game stores may be affiliate links (e.g. Instant Gaming, GameBillet, Green Man Gaming, Gameseal). If you purchase a game through one of these links, Coophubs may receive a small commission at no additional cost to you. Affiliate links are marked with rel=\"sponsored\". Ratings and site content are independent of any commercial relationship.",
    privacy_h6: "6. Intellectual property and images",
    privacy_p10_ip: "Original site content (text, descriptions, code, design) is owned by Co-op Games Hub and protected by copyright. Game images come from Steam's public CDN and are owned by the respective publishers. Game data (titles, ratings, CCU) comes from Steam, SteamSpy, and itch.io and belongs to their respective owners.",
    privacy_h7: "7. User control",
    privacy_p9_html: "You can manage or remove the data stored locally by the site by clearing the domain's <code>localStorage</code> in your browser. This removes the preferred language and any personal notes saved locally.",
    privacy_h8: "8. Security",
    privacy_p10: "The Site is served over HTTPS. Coophubs does not directly collect payment data, identity documents, or user credentials stored on a server.",
    privacy_h9: "9. Changes",
    privacy_p11: "This notice may be updated over time to reflect technical or organizational changes to the project. The latest update date is shown above.",
  }
};

const PAGE_METADATA = {
  home: {
    url: "https://coophubs.net/",
    titleKey: "home_meta_title",
    descriptionKey: "home_meta_description",
    schemaBuilder: (_, description) => ({
      "@context": "https://schema.org",
      "@type": "WebSite",
      name: "Co-op Games Hub",
      url: "https://coophubs.net/",
      description,
      inLanguage: ["it", "en"],
      potentialAction: {
        "@type": "SearchAction",
        target: "https://coophubs.net/?q={search_term_string}",
        "query-input": "required name=search_term_string",
      },
    }),
  },
  about: {
    url: "https://coophubs.net/about.html",
    titleKey: "about_meta_title",
    descriptionKey: "about_meta_description",
    schemaBuilder: (title, description) => ({
      "@context": "https://schema.org",
      "@type": "AboutPage",
      name: title,
      url: "https://coophubs.net/about.html",
      description,
    }),
  },
  contact: {
    url: "https://coophubs.net/contact.html",
    titleKey: "contact_meta_title",
    descriptionKey: "contact_meta_description",
    schemaBuilder: (title, description) => ({
      "@context": "https://schema.org",
      "@type": "ContactPage",
      name: title,
      url: "https://coophubs.net/contact.html",
      description,
      email: "coophubs@gmail.com",
    }),
  },
  free: {
    url: "https://coophubs.net/free.html",
    titleKey: "free_meta_title",
    descriptionKey: "free_meta_description",
    schemaBuilder: (title, description) => ({
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      name: title,
      url: "https://coophubs.net/free.html",
      description,
    }),
  },
  privacy: {
    url: "https://coophubs.net/privacy.html",
    titleKey: "privacy_meta_title",
    descriptionKey: "privacy_meta_description",
    schemaBuilder: (title, description) => ({
      "@context": "https://schema.org",
      "@type": "WebPage",
      name: title,
      url: "https://coophubs.net/privacy.html",
      description,
    }),
  },
};

// ===== CURRENT LANG =====
let currentLang = localStorage.getItem("coopLang") || document.documentElement.dataset.defaultLang || "it";

// ===== TRANSLATE HELPER =====
function t(key, ...args) {
  const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.it;
  const val = dict[key] !== undefined ? dict[key] : TRANSLATIONS.it[key];
  if (val === undefined) return key;
  if (typeof val === "function") return val(...args);
  return val;
}

function setMetaContent(selector, content) {
  const meta = document.querySelector(selector);
  if (meta) meta.content = content;
}

function applyDeclarativeTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });

  root.querySelectorAll("[data-i18n-html]").forEach((el) => {
    el.innerHTML = t(el.dataset.i18nHtml);
  });

  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });

  root.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel));
  });

  root.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = t(el.dataset.i18nTitle);
  });
}

function applyPageMetadata() {
  const page = document.body?.dataset.page;
  const config = PAGE_METADATA[page];
  if (!config) return;

  const title = t(config.titleKey);
  const description = t(config.descriptionKey);

  document.title = title;
  setMetaContent('meta[name="description"]', description);
  setMetaContent('meta[property="og:title"]', title);
  setMetaContent('meta[property="og:description"]', description);
  setMetaContent('meta[property="og:url"]', config.url);
  setMetaContent('meta[name="twitter:title"]', title);
  setMetaContent('meta[name="twitter:description"]', description);

  const canonical = document.querySelector('link[rel="canonical"]');
  if (canonical) canonical.href = config.url;

  const ogLocale = document.querySelector('meta[property="og:locale"]');
  if (ogLocale) ogLocale.content = currentLang === "en" ? "en_US" : "it_IT";

  const ogAlternate = document.querySelector('meta[property="og:locale:alternate"]');
  if (ogAlternate) ogAlternate.content = currentLang === "en" ? "it_IT" : "en_US";

  const jsonLd = document.getElementById("pageJsonLd");
  if (jsonLd && typeof config.schemaBuilder === "function") {
    jsonLd.textContent = JSON.stringify(config.schemaBuilder(title, description), null, 2);
  }
}

// ===== SET LANGUAGE =====
function setLang(lang) {
  currentLang = lang;
  localStorage.setItem("coopLang", lang);
  document.documentElement.lang = lang;
  applyStaticTranslations();

  if (typeof renderFilters === "function") renderFilters();
  if (typeof renderGames === "function") renderGames();
  if (typeof updateStats === "function") updateStats();
  if (typeof renderFeatured === "function") renderFeatured();
  window.dispatchEvent(new Event("langchange"));
}

// ===== APPLY STATIC TRANSLATIONS =====
function applyStaticTranslations() {
  document.documentElement.lang = currentLang;
  applyDeclarativeTranslations();
  applyPageMetadata();

  const heroSub = document.getElementById("heroSub");
  if (heroSub) heroSub.textContent = t("hero_sub");

  const statLabels = document.querySelectorAll(".stat-label");
  const statKeys = ["stat_games", "stat_played", "stat_cats"];
  statLabels.forEach((el, i) => {
    if (statKeys[i]) el.textContent = t(statKeys[i]);
  });

  const search = document.getElementById("searchInput");
  if (search) {
    search.placeholder = t("search_placeholder");
    search.setAttribute("aria-label", t("search_aria"));
  }

  const searchClear = document.getElementById("searchClear");
  if (searchClear) searchClear.setAttribute("aria-label", t("clear_search_aria"));

  const sortMap = {
    default: "sort_default",
    rating: "sort_rating",
    trending: "sort_trending",
    newest: "sort_newest",
    az: "sort_az",
  };
  document.querySelectorAll("#sortSelect option").forEach((opt) => {
    if (sortMap[opt.value]) opt.textContent = t(sortMap[opt.value]);
  });

  const yearMap = { all: "year_all", "2024": "year_2024", "2020": "year_2020", "2015": "year_2015", classic: "year_classic" };
  document.querySelectorAll("#yearFilter option").forEach((opt) => {
    if (yearMap[opt.value]) opt.textContent = t(yearMap[opt.value]);
  });

  const wheelBtn = document.getElementById("wheelBtn");
  if (wheelBtn) {
    wheelBtn.textContent = t("btn_wheel");
    wheelBtn.setAttribute("aria-label", t("btn_wheel_aria"));
  }

  const langBtn = document.getElementById("langBtn");
  if (langBtn) {
    langBtn.textContent = t("btn_lang");
    langBtn.setAttribute("aria-label", t("btn_lang_aria"));
  }

  const adminBtn = document.getElementById("adminBtn");
  if (adminBtn) {
    adminBtn.textContent =
      typeof isAdmin !== "undefined" && isAdmin ? t("btn_admin_on") : t("btn_admin");
    adminBtn.setAttribute("aria-label", t("btn_admin_aria"));
  }

  const wheelTitle = document.getElementById("wheelTitle");
  if (wheelTitle) wheelTitle.textContent = t("wheel_title");

  const spinBtn = document.getElementById("spinBtn");
  if (spinBtn) spinBtn.textContent = t("btn_spin");

  const adminPlayedTitle = document.getElementById("adminPlayedTitle");
  if (adminPlayedTitle) adminPlayedTitle.textContent = t("admin_played_title");

  const adminPlayedLabel = document.getElementById("adminPlayedLabel");
  if (adminPlayedLabel) adminPlayedLabel.textContent = t("admin_played_label");

  const adminNoteTitle = document.getElementById("adminNoteTitle");
  if (adminNoteTitle) adminNoteTitle.textContent = t("admin_note_title");

  const adminNoteInput = document.getElementById("adminNoteInput");
  if (adminNoteInput) adminNoteInput.placeholder = t("admin_note_placeholder");

  const adminSaveBtn = document.getElementById("adminSaveBtn");
  if (adminSaveBtn) adminSaveBtn.textContent = t("btn_save");

  const adminCancelBtn = document.getElementById("adminCancelBtn");
  if (adminCancelBtn) adminCancelBtn.textContent = t("btn_cancel");
}

document.addEventListener("DOMContentLoaded", () => {
  applyStaticTranslations();
});
