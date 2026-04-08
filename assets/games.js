// Main games.js - now using bundle loading
// Original size: 1.1MB, New size: ~1.4KB

// Keep original variables (core.js is redundant, we include it here)
const featuredIndieId = 180;

// Async loading system for games data
let gamesDataLoaded = false;
let gamesDataPromise = null;

/**
 * Load games data asynchronously
 * @returns {Promise<Array>} Promise resolving to games array
 */
function loadGamesData() {
    if (gamesDataPromise) return gamesDataPromise;
    
    gamesDataPromise = new Promise((resolve, reject) => {
        // Check if already loaded
        if (gamesDataLoaded && typeof window.games !== 'undefined') {
            resolve(window.games);
            return;
        }
        
        // Load the bundle
        const script = document.createElement('script');
        script.src = '/assets/bundles/games-data.js';
        script.async = true;
        
        script.onload = () => {
            if (typeof window.games !== 'undefined') {
                gamesDataLoaded = true;
                resolve(window.games);
            } else {
                reject(new Error('Games data not available after loading'));
            }
        };
        
        script.onerror = (error) => {
            reject(new Error(`Failed to load games data: ${error.message}`));
        };
        
        document.head.appendChild(script);
    });
    
    return gamesDataPromise;
}

/**
 * Get games data - main entry point for other scripts
 * @returns {Promise<Array>} Promise resolving to games array
 */
function getGames() {
    return loadGamesData();
}

/**
 * Get a specific game by ID
 * @param {number} id - Game ID
 * @returns {Promise<Object>} Promise resolving to game object
 */
async function getGameById(id) {
    const games = await loadGamesData();
    return games.find(game => game.id === id) || null;
}

/**
 * Get games filtered by category
 * @param {string} category - Category to filter by
 * @returns {Promise<Array>} Promise resolving to filtered games array
 */
async function getGamesByCategory(category) {
    const games = await loadGamesData();
    return games.filter(game => 
        game.categories?.includes(category) || 
        game.genres?.includes(category)
    );
}

/**
 * Get featured indie game
 * @returns {Promise<Object>} Promise resolving to featured indie game
 */
async function getFeaturedIndieGame() {
    return getGameById(featuredIndieId);
}

// Export for use in other scripts
window.loadGamesData = loadGamesData;
window.getGames = getGames;
window.getGameById = getGameById;
window.getGamesByCategory = getGamesByCategory;
window.getFeaturedIndieGame = getFeaturedIndieGame;
window.featuredIndieId = featuredIndieId;

// Legacy support: provide empty games array initially
window.games = [];

// Auto-load games data if needed for backward compatibility
if (typeof window.autoLoadGames !== 'undefined' && window.autoLoadGames === true) {
    loadGamesData().then(games => {
        window.games = games;
        if (typeof window.onGamesLoaded === 'function') {
            window.onGamesLoaded(games);
        }
    }).catch(error => {
        console.error('Failed to auto-load games:', error);
    });
}

console.log('Games.js loader initialized - using async bundle loading');