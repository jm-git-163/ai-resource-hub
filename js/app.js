// Global State
let allResources = [];
let categories = {};
let lastUpdated = '';
let currentFilters = {
    category: 'all',
    platforms: new Set(),
    search: '',
    sort: 'stars-desc'
};
let favorites = new Set(); // stored in localStorage

// Helper Functions
function getPlatformInfo(platform) {
    const map = {
        'github': { label: 'GitHub', color: '#e6edf3' },
        'huggingface': { label: 'HuggingFace', color: '#ff9d00' },
        'arxiv': { label: 'arXiv', color: '#b31b1b' },
        'hackernews': { label: 'HackerNews', color: '#ff6600' },
        'curated': { label: '큐레이션', color: '#4ade80' }
    };
    return map[platform] || { label: platform, color: '#94a3b8' };
}

function getLicenseInfo(license) {
    if (!license) return { label: '확인 필요', class: 'license-unknown' };
    const l = license.toLowerCase();
    if (['mit', 'apache', 'isc', 'bsd', 'unlicense', 'free', 'ofl', 'pixabay', 'unsplash', 'pexels', 'wtfpl', 'cc0'].some(k => l.includes(k)))
        return { label: '✅ 무료', class: 'license-free' };
    if (l.includes('cc-by-nc') || l.includes('non-commercial') || l.includes('personal') || l.includes('remarc'))
        return { label: '⚠️ 비상업', class: 'license-nc' };
    if (l.includes('cc-by') || l.includes('cc '))
        return { label: '📝 출처 필요', class: 'license-cc' };
    if (l.includes('paid') || l.includes('premium'))
        return { label: '💰 유료', class: 'license-paid' };
    if (l === 'n/a' || l === 'various')
        return { label: '확인 필요', class: 'license-unknown' };
    return { label: license, class: 'license-unknown' };
}

function getCatBgColor(category) {
    const colors = {
        trend: '248,113,113', prompt: '96,165,250', skill: '167,139,250',
        workflow: '74,222,128', opensource: '251,146,60', design: '244,114,182',
        video: '34,211,238', asset: '251,191,36', contest: '232,121,249',
        research: '148,163,184'
    };
    return `rgba(${colors[category] || '148,163,184'}, 0.15)`;
}

function formatNumber(n) {
    if (!n && n !== 0) return '0';
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    if (diff === 0) return '오늘';
    if (diff === 1) return '어제';
    if (diff < 7) return `${diff}일 전`;
    if (diff < 30) return `${Math.floor(diff / 7)}주 전`;
    if (diff < 365) return `${Math.floor(diff / 30)}개월 전`;
    return dateStr;
}

function getFreshnessEmoji(label) {
    return { new: '🔥', fresh: '🌿', stale: '⚠️', normal: '' }[label] || '';
}

function getFreshnessText(label) {
    return { new: 'NEW', fresh: '신선', stale: '오래됨', normal: '' }[label] || '';
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function truncate(str, len) {
    return str.length > len ? str.substring(0, len) + '...' : str;
}

// Logic Functions
function calculateFreshness(resource) {
    const now = new Date();
    const updated = new Date(resource.updated_at);
    const firstSeen = new Date(resource.first_seen || resource.updated_at);
    
    const daysSinceUpdate = (now - updated) / (1000 * 60 * 60 * 24);
    const daysSinceFirstSeen = (now - firstSeen) / (1000 * 60 * 60 * 24);
    const stars = resource.stars || 0;
    
    // Activity score (40%)
    let activity = daysSinceUpdate <= 7 ? 100 : daysSinceUpdate <= 30 ? 80 : daysSinceUpdate <= 90 ? 60 : daysSinceUpdate <= 180 ? 30 : 10;
    
    // Age penalty (30%)
    let age = daysSinceFirstSeen <= 30 ? 100 : daysSinceFirstSeen <= 90 ? 70 : daysSinceFirstSeen <= 180 ? 40 : 20;
    
    // Popularity (30%)
    let popularity = stars > 10000 ? 100 : stars > 1000 ? 80 : stars > 100 ? 60 : stars > 10 ? 40 : 20;
    
    const score = Math.round(activity * 0.4 + age * 0.3 + popularity * 0.3);
    
    let label = 'normal';
    if (daysSinceFirstSeen <= 30) label = 'new';
    else if (score > 70) label = 'fresh';
    else if (score < 30) label = 'stale';
    
    return { score, label };
}

function sortResources(resources, sortKey) {
    const sorted = [...resources];
    switch(sortKey) {
        case 'stars-desc': sorted.sort((a, b) => (b.stars||0) - (a.stars||0)); break;
        case 'date-desc': sorted.sort((a, b) => (b.updated_at||'').localeCompare(a.updated_at||'')); break;
        case 'freshness-desc': sorted.sort((a, b) => (b._freshness?.score||0) - (a._freshness?.score||0)); break;
        case 'title-asc': sorted.sort((a, b) => (a.title||'').localeCompare(b.title||'')); break;
    }
    return sorted;
}

function applyFilters() {
    let filtered = [...allResources];
    
    // Category filter
    if (currentFilters.category !== 'all') {
        filtered = filtered.filter(r => r.category === currentFilters.category);
    }
    
    // Platform filter
    if (currentFilters.platforms.size > 0) {
        filtered = filtered.filter(r => currentFilters.platforms.has(r.platform));
    }
    
    // Search filter
    if (currentFilters.search) {
        const q = currentFilters.search.toLowerCase();
        filtered = filtered.filter(r => 
            (r.title || '').toLowerCase().includes(q) ||
            (r.description || '').toLowerCase().includes(q) ||
            (r.description_kr || '').toLowerCase().includes(q) ||
            (r.tags || []).join(' ').toLowerCase().includes(q) ||
            (r.author || '').toLowerCase().includes(q)
        );
    }
    
    // Sort
    filtered = sortResources(filtered, currentFilters.sort);
    
    renderCards(filtered);
    updateResultCount(filtered.length);
}

// Global Actions
window.selectCategory = function(category) {
    currentFilters.category = category;
    
    // Update tabs
    document.querySelectorAll('#tabs-inner .tab').forEach(tab => {
        if (tab.dataset.category === category) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Guide text
    const guideEl = document.getElementById('category-guide');
    const guideText = document.getElementById('guide-text');
    if (guideEl && guideText) {
        if (category !== 'all' && categories[category]) {
            guideText.textContent = categories[category].guide;
            guideEl.style.display = 'flex';
        } else {
            guideEl.style.display = 'none';
        }
    }
    
    applyFilters();
};

window.toggleFavorite = function(id) {
    if (favorites.has(id)) {
        favorites.delete(id);
    } else {
        favorites.add(id);
    }
    saveFavorites();
    applyFilters(); // re-render to update heart icons
};

function loadFavorites() {
    try {
        const saved = localStorage.getItem('ai-hub-favorites');
        if (saved) favorites = new Set(JSON.parse(saved));
    } catch(e) {}
}

function saveFavorites() {
    localStorage.setItem('ai-hub-favorites', JSON.stringify([...favorites]));
}

function updateResultCount(count) {
    const el = document.getElementById('total-count');
    if (el) el.textContent = formatNumber(allResources.length);
    const resultEl = document.getElementById('result-count');
    if (resultEl) resultEl.textContent = `결과: ${count}개`;
}

// Render Functions
function createCardHTML(resource, index) {
    const freshness = resource._freshness || { score: 50, label: 'normal' };
    const platformInfo = getPlatformInfo(resource.platform);
    const catInfo = categories[resource.category] || { icon: '📁', name_kr: '기타' };
    const licenseInfo = getLicenseInfo(resource.license);
    const isFav = favorites.has(resource.id);
    const delay = Math.min(index * 0.03, 0.6); // max 0.6s stagger
    
    return `
    <article class="card" data-category="${resource.category}" style="animation-delay: ${delay}s">
        <div class="card-header">
            <span class="platform-badge">
                <span class="platform-dot" style="background:${platformInfo.color}"></span>
                ${platformInfo.label}
            </span>
            <span class="category-badge" style="background:${getCatBgColor(resource.category)};color:var(--cat-${resource.category})">
                ${catInfo.icon} ${catInfo.name_kr}
            </span>
        </div>
        <div class="card-meta">
            <span class="stars">⭐ ${formatNumber(resource.stars)}</span>
            <span class="date">📅 ${formatDate(resource.updated_at)}</span>
        </div>
        <h3 class="card-title">
            <a href="${resource.url}" target="_blank" rel="noopener">${escapeHtml(resource.title)}</a>
        </h3>
        ${freshness.label !== 'normal' ? `<span class="badge-${freshness.label}">${getFreshnessEmoji(freshness.label)} ${getFreshnessText(freshness.label)}</span>` : ''}
        <p class="desc-kr">${escapeHtml(resource.description_kr || '')}</p>
        <p class="desc-en">${escapeHtml(truncate(resource.description || '', 120))}</p>
        <div class="card-tags">
            ${(resource.tags || []).slice(0, 4).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
        </div>
        <div class="card-footer">
            <span class="author">👤 ${escapeHtml(resource.author || 'unknown')}</span>
            ${licenseInfo ? `<span class="license-badge ${licenseInfo.class}">${licenseInfo.label}</span>` : ''}
        </div>
        <div class="card-actions">
            <a href="${resource.url}" target="_blank" rel="noopener" class="btn-open">열기 →</a>
            ${resource.demo_url ? `<a href="${resource.demo_url}" target="_blank" rel="noopener" class="btn-demo">🌐 데모</a>` : ''}
            <button class="btn-fav ${isFav ? 'active' : ''}" onclick="toggleFavorite('${resource.id}')" title="즐겨찾기">
                ${isFav ? '❤️' : '🤍'}
            </button>
        </div>
    </article>`;
}

function renderCards(resources) {
    const grid = document.getElementById('card-grid');
    if (!grid) return;
    if (resources.length === 0) {
        grid.innerHTML = '<div class="empty-results">검색 결과가 없습니다.</div>';
        return;
    }
    grid.innerHTML = resources.map((r, i) => createCardHTML(r, i)).join('');
}

function renderStats() {
    const statsEl = document.getElementById('stats-categories');
    if (!statsEl) return;
    
    // Count per category
    const counts = {};
    allResources.forEach(r => {
        counts[r.category] = (counts[r.category] || 0) + 1;
    });

    statsEl.innerHTML = Object.entries(categories).map(([catKey, cat]) => {
        const count = counts[catKey] || 0;
        return `
        <div class="stat-item" data-category="${catKey}" onclick="selectCategory('${catKey}')">
            <span class="stat-number" style="color: var(--cat-${catKey})">${formatNumber(count)}</span>
            <span class="stat-label">${cat.icon} ${cat.name_kr}</span>
        </div>`;
    }).join('');
}

function renderCategoryTabs() {
    const tabsInner = document.getElementById('tabs-inner');
    if (!tabsInner) return;
    
    const tabsHtml = Object.entries(categories).map(([catKey, cat]) => `
        <button class="tab" data-category="${catKey}" style="--tab-color: var(--cat-${catKey})">
            ${cat.icon} ${cat.name_kr}
        </button>
    `).join('');
    
    // Add "All" tab at the beginning if needed, assuming it's already there or we can insert adjacent
    tabsInner.insertAdjacentHTML('beforeend', tabsHtml);

    // Attach listeners
    tabsInner.querySelectorAll('.tab').forEach(btn => {
        btn.addEventListener('click', () => {
            selectCategory(btn.dataset.category);
        });
    });
}

function renderAll() {
    // Hide loading
    const loadingEl = document.getElementById('loading-state');
    if (loadingEl) loadingEl.style.display = 'none';

    renderStats();
    renderCategoryTabs();
    applyFilters();
}

function normalizeCategory(category) {
    const map = {
        'prompts': 'prompt',
        'skills': 'skill',
        'tools': 'opensource',
        'workflows': 'workflow',
        'models': 'opensource',
        'learning': 'research'
    };
    return map[category] || category;
}

// Event Listeners initialization
function setupEventListeners() {
    // Search (debounced 300ms)
    let searchTimeout;
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const val = e.target.value;
            if (searchClear) searchClear.style.display = val ? 'block' : 'none';
            searchTimeout = setTimeout(() => {
                currentFilters.search = val;
                applyFilters();
            }, 300);
        });
    }

    if (searchClear) {
        searchClear.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            searchClear.style.display = 'none';
            currentFilters.search = '';
            applyFilters();
        });
    }

    // Platform filters (toggle)
    document.querySelectorAll('#platform-filters .pill').forEach(btn => {
        btn.addEventListener('click', () => {
            const platform = btn.dataset.platform;
            if (platform === 'all') {
                currentFilters.platforms.clear();
                document.querySelectorAll('#platform-filters .pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            } else {
                const allPill = document.querySelector('#platform-filters .pill[data-platform="all"]');
                if (allPill) allPill.classList.remove('active');
                
                if (currentFilters.platforms.has(platform)) {
                    currentFilters.platforms.delete(platform);
                    btn.classList.remove('active');
                } else {
                    currentFilters.platforms.add(platform);
                    btn.classList.add('active');
                }
                
                if (currentFilters.platforms.size === 0 && allPill) {
                    allPill.classList.add('active');
                }
            }
            applyFilters();
        });
    });

    // Sort
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentFilters.sort = e.target.value;
            applyFilters();
        });
    }

    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isLight = document.body.classList.toggle('light');
            themeToggle.textContent = isLight ? '☀️' : '🌙';
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        });
    }

    // Login modal
    const loginBtn = document.getElementById('login-btn');
    const modalClose = document.getElementById('modal-close');
    const loginModal = document.getElementById('login-modal');
    
    if (loginBtn && loginModal) {
        loginBtn.addEventListener('click', () => {
            loginModal.style.display = 'flex';
        });
    }
    
    if (modalClose && loginModal) {
        modalClose.addEventListener('click', () => {
            loginModal.style.display = 'none';
        });
    }
    
    if (loginModal) {
        loginModal.addEventListener('click', (e) => {
            if (e.target === loginModal) loginModal.style.display = 'none';
        });
    }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Load theme
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light');
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) themeToggle.textContent = '☀️';
    }
    
    // Load favorites
    loadFavorites();
    
    // Setup event listeners
    setupEventListeners();
    
    // Fetch data
    fetch('data/resources.json')
        .then(r => r.json())
        .then(data => {
            categories = data.categories || {};
            lastUpdated = data.last_updated || '';
            
            // Map old category formats
            allResources = (data.resources || []).map(r => {
                r.category = normalizeCategory(r.category);
                return r;
            });
            
            // Calculate freshness for each resource
            allResources.forEach(r => {
                r._freshness = calculateFreshness(r);
            });
            
            renderAll();
        })
        .catch(err => {
            console.error('Failed to load resources:', err);
            const loadingEl = document.getElementById('loading-state');
            if (loadingEl) loadingEl.style.display = 'none';
            const emptyEl = document.getElementById('empty-state');
            if (emptyEl) emptyEl.style.display = 'flex';
        });
});
