// Main games.js - now using bundle loading
// Original size: 1.1MB, New size: ~1.4KB

// Keep original variables (core.js is redundant, we include it here)
const featuredIndieId = 180;

// Async loading system for games data
let gamesDataLoaded = false;
let gamesDataPromise = null;

function loadGamesData() {
    if (gamesDataPromise) return gamesDataPromise;
    
    gamesDataPromise = new Promise((resolve, reject) => {
        if (gamesDataLoaded && typeof window.games !== 'undefined') {
            resolve(window.games);
            return;
        }
        
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
            reject(new Error('Failed to load games data: ' + error.message));
        };
        
        document.head.appendChild(script);
    });
    
    return gamesDataPromise;
}

function getGames() {
    return loadGamesData();
}

async function getGameById(id) {
    const games = await loadGamesData();
    return games.find(game => game.id === id) || null;
}

async function getGamesByCategory(category) {
    const games = await loadGamesData();
    return games.filter(game => 
        game.categories?.includes(category) || 
        game.genres?.includes(category)
    );
}

async function getFeaturedIndieGame() {
    return getGameById(featuredIndieId);
}

window.loadGamesData = loadGamesData;
window.getGames = getGames;
window.getGameById = getGameById;
window.getGamesByCategory = getGamesByCategory;
window.getFeaturedIndieGame = getFeaturedIndieGame;
window.featuredIndieId = featuredIndieId;
window.games = [];

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
