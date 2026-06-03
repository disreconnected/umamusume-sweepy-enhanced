(() => {
const state = {
    needs2fa: false,
    isLoading: false,
    account: null,
    isDeletingCareer: false,
    isFinishingCareer: false,
    isFetchingFriends: false,
    isStartingCareer: false,
    umaMoeCharas: null,
    presets: [],
    selectedPreset: "",
    runnerTimer: 0,
    isSavingPreset: false,
    raceData: [],
    selectedRaces: [],
    scenarioType: "Mant",
    burnClocks: false,
    umaMoeSearchResults: [],
    umaMoeSearchTotal: 0,
    umaMoeSearchCharaName: "",
    umaMoeSortKey: "score",
    umaMoeSortDir: "desc",
    displayedClocksUsed: 0,
    devEnabled: false,
    consecutiveRunnerFails: 0,
    lastSessionCache: null,
    isRefillingTp: false,
    deckEditor: { open: false, id: "", name: "", cards: [], inspectCard: null },
    eventBoost: { enabled: false, story_event_id: 0, tp_multiplier: 2 },
    isManagingFollow: false,
    advisorRecommendations: [],
    filters: {
        decks: { query: '' },
        trainees: { query: '' },
        friends: {
            query: '',
            type: 'all',
            rarity: { SSR: true, SR: true, R: true },
            limitBreak: 'all'
        },
        ownedCards: {
            query: '',
            type: 'all',
            rarity: { SSR: true, SR: true, R: true }
        },
        parents: {
            query: '',
            rank: 'all',
            criteria: []
        },
        friendVets: {
            query: '',
            rank: 'all',
            criteria: []
        }
    },
    uniqueFactors: []
};
const els = {
    loadingScreen: document.getElementById('loading-screen'),
    navbar: document.querySelector('.navbar'),
    themeToggle: document.getElementById('theme-toggle'),
    brandMark: document.querySelector('.title span'),
    loginBtn: document.getElementById('login-btn'),
    logoutBtn: document.getElementById('logout-btn'),
    turnDelayMin: document.getElementById('turn-delay-min'),
    turnDelayMax: document.getElementById('turn-delay-max'),
    temptFateBtn: document.getElementById('tempt-fate-btn'),
    burnClocksBtn: document.getElementById('burn-clocks-btn'),
    devBtn: document.getElementById('dev-career-btn'),
    loginView: document.getElementById('login-view'),
    lastSessionBanner: document.getElementById('last-session-banner'),
    dashboardView: document.getElementById('dashboard-view'),
    errorMsg: document.getElementById('error-msg'),
    standardFields: document.getElementById('standard-fields'),
    faFields: document.getElementById('2fa-fields'),
    umaGrid: document.getElementById('uma-grid'),
    cardGrid: document.getElementById('card-grid'),
    cardGridWrapper: document.getElementById('card-grid-wrapper'),
    cardsToggle: document.getElementById('cards-toggle'),
    cardsChevron: document.getElementById('cards-chevron'),
    parentGrid: document.getElementById('parent-grid'),
    friendGrid: document.getElementById('friend-grid'),
    friendVetGrid: document.getElementById('friend-vet-grid'),
    friendVetCount: document.getElementById('friend-vet-count'),
    friendVetStatus: document.getElementById('friend-vet-status'),

    // Library Filters Cache
    deckSearch: document.getElementById('deck-search-input'),
    traineeSearch: document.getElementById('trainee-search-input'),
    
    friendSearch: document.getElementById('friend-search-input'),
    friendType: document.getElementById('friend-type-select'),
    friendRarityRow: document.getElementById('friend-rarity-row'),
    
    parentSearch: document.getElementById('parent-search-input'),
    parentRank: document.getElementById('parent-rank-select'),
    parentSparkToggle: document.getElementById('parent-spark-toggle'),
    parentSparkDrawer: document.getElementById('parent-spark-drawer'),
    
    friendVetSearch: document.getElementById('friend-vet-search-input'),
    friendVetRank: document.getElementById('friend-vet-rank-select'),
    friendVetSparkToggle: document.getElementById('friend-vet-spark-toggle'),
    friendVetSparkDrawer: document.getElementById('friend-vet-spark-drawer'),
    
    cardSearch: document.getElementById('card-search-input'),
    cardType: document.getElementById('card-type-select'),
    cardRarityRow: document.getElementById('card-rarity-row'),
    friendVetRefreshBtn: document.getElementById('friend-vet-refresh-btn'),
    friendVetsToggle: document.getElementById('friend-vets-toggle'),
    friendVetsChevron: document.getElementById('friend-vets-chevron'),
    friendVetsBody: document.getElementById('friend-vets-body'),
    deckList: document.getElementById('deck-list'),
    deckEditorNewBtn: document.getElementById('deck-editor-new-btn'),
    deckEditorSaveBtn: document.getElementById('deck-editor-save-btn'),
    deckEditorName: document.getElementById('deck-editor-name'),
    deckEditorStatus: document.getElementById('deck-editor-status'),
    deckEditorPanel: document.getElementById('deck-editor-panel'),
    umaCount: document.getElementById('uma-count'),
    cardCount: document.getElementById('card-count'),
    parentCount: document.getElementById('parent-count'),
    friendCount: document.getElementById('friend-count'),
    friendStatus: document.getElementById('friend-status'),
    friendManageStatus: document.getElementById('friend-manage-status'),
    friendRefreshBtn: document.getElementById('friend-refresh-btn'),
    friendIdInput: document.getElementById('friend-id-input'),
    friendPreviewBtn: document.getElementById('friend-preview-btn'),
    friendFollowIdBtn: document.getElementById('friend-follow-id-btn'),
    friendPreviewPanel: document.getElementById('friend-preview-panel'),
    friendFollowList: document.getElementById('friend-follow-list'),
    advisorPanel: document.getElementById('advisor-panel'),
    presetSelect: document.getElementById('preset-select'),
    startCareerBtn: document.getElementById('start-career-btn'),
    startStatus: document.getElementById('start-status'),
    eventBoostCheckbox: document.getElementById('event-boost-checkbox'),
    eventBoostEventId: document.getElementById('event-boost-event-id'),
    eventBoostStatus: document.getElementById('event-boost-status'),
    accountStrip: document.getElementById('account-strip'),
    careerModal: document.getElementById('career-modal'),
    careerModalTitle: document.getElementById('career-modal-title'),
    careerModalCopy: document.getElementById('career-modal-copy'),
    careerCancelBtn: document.getElementById('career-cancel-btn'),
    careerDeleteBtn: document.getElementById('career-delete-btn'),
    careerFinishBtn: document.getElementById('career-finish-btn'),
    raceToggle: document.getElementById('race-toggle'),
    raceChevron: document.getElementById('race-chevron'),
    raceBody: document.getElementById('race-body'),
    saveRacesBtn: document.getElementById('save-races-btn'),
    raceOptionsContent: document.getElementById('race-options-content'),
    racePopupOverlay: document.getElementById('race-slot-popup-overlay'),
    racePopupTitle: document.getElementById('race-slot-popup-title'),
    racePopupBody: document.getElementById('race-slot-popup-body'),
    racePopupClose: document.getElementById('race-slot-popup-close'),
    masterDataPath: document.getElementById('master-data-path'),
    masterDataSaveBtn: document.getElementById('master-data-save-btn'),
    masterDataStatus: document.getElementById('master-data-status'),
    presetSection: document.getElementById('preset-section'),
    presetAddBtn: document.getElementById('preset-add-btn'),
    presetDelBtn: document.getElementById('preset-del-btn'),
    presetRunningStyle: document.getElementById('preset-running-style'),
    presetSkillThreshold: document.getElementById('preset-skill-threshold'),
    presetEditSkillsBtn: document.getElementById('preset-edit-skills-btn'),
    presetMinStats: {
        speed: document.getElementById('preset-min-speed'),
        stamina: document.getElementById('preset-min-stamina'),
        power: document.getElementById('preset-min-power'),
        guts: document.getElementById('preset-min-guts'),
        wit: document.getElementById('preset-min-wit'),
    },
    presetMaxStats: {
        speed: document.getElementById('preset-max-speed'),
        stamina: document.getElementById('preset-max-stamina'),
        power: document.getElementById('preset-max-power'),
        guts: document.getElementById('preset-max-guts'),
        wit: document.getElementById('preset-max-wit'),
    },
    umaMoeTrainerId: document.getElementById('uma-moe-trainer-id'),
    umaMoePreviewBtn: document.getElementById('uma-moe-preview-btn'),
    umaMoeImportBtn: document.getElementById('uma-moe-import-btn'),
    umaMoeStatus: document.getElementById('uma-moe-status'),
    umaMoePreview: document.getElementById('uma-moe-preview'),
    umaMoeSearchChara: document.getElementById('uma-moe-search-chara'),
    umaMoeSearchBtn: document.getElementById('uma-moe-search-btn'),
    umaMoeSortBtns: Array.from(document.querySelectorAll('.uma-moe-sort-btn')),
    umaMoeSortDirBtn: document.getElementById('uma-moe-sort-dir-btn'),
    umaMoeSearchStatus: document.getElementById('uma-moe-search-status'),
    umaMoeSearchResults: document.getElementById('uma-moe-search-results'),
    skillModal: document.getElementById('skill-modal'),
    skillSearch: document.getElementById('skill-search'),
    skillList: document.getElementById('skill-list'),
    skillTiersContainer: document.getElementById('skill-tiers-container'),
    skillBlacklistContainer: document.getElementById('skill-blacklist-container'),
    skillAddTierBtn: document.getElementById('skill-add-tier-btn'),
    skillModalClose: document.getElementById('skill-modal-close')
};
        const delaySettingsStorageKey = 'uma_turn_delay_settings';
        const burnClocksStorageKey = 'uma_burn_clocks';
        const devStorageKey = 'uma_dev_career';
        function syncDevControls() {
            if (!els.devBtn) return;
            els.devBtn.classList.toggle('is-active', state.devEnabled);
            els.devBtn.innerText = `DEV: ${state.devEnabled ? 'ON' : 'OFF'}`;
        }
        function setDevEnabled(value, options = {}) {
            state.devEnabled = Boolean(value);
            syncDevControls();
            if (options.persist) {
                localStorage.setItem(devStorageKey, String(state.devEnabled));
            }
        }

        window.addEventListener('storage', event => {
            if (event.key === devStorageKey && event.newValue !== null) {
                setDevEnabled(event.newValue === 'true', { persist: false });
            }
        });
        const storedDev = localStorage.getItem(devStorageKey);
        if (storedDev !== null) setDevEnabled(storedDev === 'true', { persist: false });

        if (els.devBtn) {
            els.devBtn.addEventListener('click', () => {
                setDevEnabled(!state.devEnabled, { persist: true });
            });
        }

        function setLoadingScreen(visible) {
            if (!els.loadingScreen) return;
            els.loadingScreen.classList.toggle('hidden', !visible);
        }
        function hideNavbar() {
            document.body.classList.add('pre-login');
            if (els.brandMark) els.brandMark.classList.remove('is-entrance');
        }
        function showNavbar() {
            document.body.classList.remove('pre-login');
        }
        function playBrandIntro() {
            if (!els.brandMark) return;
            els.brandMark.classList.remove('is-entrance');
            void els.brandMark.offsetWidth;
            els.brandMark.classList.add('is-entrance');
            window.setTimeout(() => els.brandMark.classList.remove('is-entrance'), 950);
        }
        hideNavbar();
        function syncDashboardHeight() {
            const navbar = document.querySelector('.navbar');
            const navbarHeight = navbar ? navbar.getBoundingClientRect().height : 0;
            const availableHeight = Math.max(360, Math.floor(window.innerHeight - navbarHeight));
            document.documentElement.style.setProperty('--dashboard-height', `${availableHeight}px`);
            syncDashboardCollapseState(false);
        }
        window.addEventListener('resize', syncDashboardHeight);
        window.addEventListener('orientationchange', syncDashboardHeight);
        syncDashboardHeight();
        const panelToggleSyncers = [];
        const dashboardMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        let dashboardLayoutAnimation = 0;
        const dashboardAnimationMs = 420;
        function isCompactDashboard() {
            return window.matchMedia('(max-width: 850px)').matches;
        }
        function getPanelLayoutTarget(setupCollapsed, contentCollapsed) {
            const compact = isCompactDashboard();
            const gutter = document.querySelector('.split-gutter-controls');
            const dashboardRect = els.dashboardView.getBoundingClientRect();
            const gutterRect = gutter.getBoundingClientRect();
            const gutterSize = compact ? gutterRect.height : gutterRect.width;
            const available = Math.max(0, (compact ? dashboardRect.height : dashboardRect.width) - gutterSize);
            if (compact) {
                const setupSize = setupCollapsed ? 0 : contentCollapsed ? available : available * 0.34;
                const contentSize = contentCollapsed ? 0 : setupCollapsed ? available : Math.max(340, available - setupSize);
                return { compact, gutterSize, setupSize, contentSize };
            }
            const setupSize = setupCollapsed ? 0 : contentCollapsed ? available : Math.min(available * 0.62, available - 340);
            const contentSize = contentCollapsed ? 0 : setupCollapsed ? available : Math.max(340, available - setupSize);
            return { compact, gutterSize, setupSize, contentSize };
        }
        function setDashboardTemplate(layout, setupSize, contentSize) {
            const safeSetup = Math.max(0, setupSize);
            const safeContent = Math.max(0, contentSize);
            if (layout.compact) {
                els.dashboardView.style.gridTemplateColumns = '';
                els.dashboardView.style.gridTemplateRows = `${safeSetup}px ${layout.gutterSize}px ${safeContent}px`;
            } else {
                els.dashboardView.style.gridTemplateRows = '';
                els.dashboardView.style.gridTemplateColumns = `${safeSetup}px ${layout.gutterSize}px ${safeContent}px`;
            }
        }
        function easeDashboardLayout(t) {
            return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        }
        function syncDashboardCollapseState(animate = false) {
            const setupPanel = document.getElementById('setup-panel');
            const contentPanel = document.getElementById('content-panel');
            if (!setupPanel || !contentPanel || !els.dashboardView) return;
            if (setupPanel.classList.contains('collapsed') && contentPanel.classList.contains('collapsed')) {
                contentPanel.classList.remove('collapsed');
            }
            const setupCollapsed = setupPanel.classList.contains('collapsed');
            const contentCollapsed = contentPanel.classList.contains('collapsed');
            els.dashboardView.classList.toggle('setup-collapsed', setupCollapsed);
            els.dashboardView.classList.toggle('content-collapsed', contentCollapsed);
            if (!els.dashboardView.classList.contains('active')) return;
            const layout = getPanelLayoutTarget(setupCollapsed, contentCollapsed);
            if (dashboardLayoutAnimation) {
                cancelAnimationFrame(dashboardLayoutAnimation);
                dashboardLayoutAnimation = 0;
            }
            els.dashboardView.style.transition = 'none';
            if (!animate || dashboardMotion.matches) {
                setDashboardTemplate(layout, layout.setupSize, layout.contentSize);
                return;
            }
            const compact = layout.compact;
            const setupRect = setupPanel.getBoundingClientRect();
            const contentRect = contentPanel.getBoundingClientRect();
            const startSetup = compact ? setupRect.height : setupRect.width;
            const startContent = compact ? contentRect.height : contentRect.width;
            const targetSetup = layout.setupSize;
            const targetContent = layout.contentSize;
            if (Math.abs(startSetup - targetSetup) < 0.5 && Math.abs(startContent - targetContent) < 0.5) {
                setDashboardTemplate(layout, targetSetup, targetContent);
                return;
            }
            const startedAt = performance.now();
            const step = now => {
                const t = Math.min(1, (now - startedAt) / dashboardAnimationMs);
                const eased = easeDashboardLayout(t);
                setDashboardTemplate(
                    layout,
                    startSetup + (targetSetup - startSetup) * eased,
                    startContent + (targetContent - startContent) * eased
                );
                if (t < 1) {
                    dashboardLayoutAnimation = requestAnimationFrame(step);
                } else {
                    setDashboardTemplate(layout, targetSetup, targetContent);
                    dashboardLayoutAnimation = 0;
                }
            };
            setDashboardTemplate(layout, startSetup, startContent);
            dashboardLayoutAnimation = requestAnimationFrame(step);
        }
        function syncPanelToggleButtons() {
            panelToggleSyncers.forEach(sync => sync());
        }
        function makePanelToggle(panelId, btnId, collapseIcon, expandIcon) {
            const panel = document.getElementById(panelId);
            const btn = document.getElementById(btnId);
            const label = (btn.dataset.panelLabel || 'panel').toLowerCase();
            const renderChevrons = icon => `
                <span class="panel-collapse-btn-chevron-stack" aria-hidden="true">
                    <span>${icon}</span>
                    <span>${icon}</span>
                    <span>${icon}</span>
                </span>
            `;
            const syncButton = () => {
                const isCollapsed = panel.classList.contains('collapsed');
                const icon = isCollapsed ? expandIcon : collapseIcon;
                btn.classList.toggle('is-collapsed', isCollapsed);
                btn.innerHTML = renderChevrons(icon);
                btn.setAttribute('title', `${isCollapsed ? 'Expand' : 'Collapse'} ${label}`);
                btn.setAttribute('aria-label', `${isCollapsed ? 'Expand' : 'Collapse'} ${label}`);
                btn.setAttribute('aria-expanded', String(!isCollapsed));
            };
            panelToggleSyncers.push(syncButton);
            btn.addEventListener('click', () => {
                panel.classList.toggle('collapsed');
                syncDashboardCollapseState(true);
                syncPanelToggleButtons();
            });
            syncDashboardCollapseState(false);
            syncButton();
        }
        makePanelToggle('setup-panel',   'setup-collapse-btn',   '&lt;', '&gt;');
        makePanelToggle('content-panel', 'content-collapse-btn', '&gt;', '&lt;');
        function makeSectionToggle(toggleId, chevronId, bodyId, startExpanded) {
            const toggle  = document.getElementById(toggleId);
            const chevron = document.getElementById(chevronId);
            const body    = document.getElementById(bodyId);
            if (!toggle || !body) return;
            const setInitial = () => {
                const expanded = body.classList.contains('expanded');
                body.style.height = expanded ? 'auto' : '0px';
                chevron.classList.toggle('expanded', expanded);
            };
            const expand = () => {
                body.classList.add('expanded');
                chevron.classList.add('expanded');
                body.style.height = '0px';
                body.offsetHeight;
                body.style.height = `${body.scrollHeight}px`;
            };
            const collapse = () => {
                body.style.height = `${body.scrollHeight}px`;
                body.offsetHeight;
                body.classList.remove('expanded');
                chevron.classList.remove('expanded');
                body.style.height = '0px';
            };
            body.addEventListener('transitionend', event => {
                if (event.propertyName === 'height' && body.classList.contains('expanded')) body.style.height = 'auto';
            });
            toggle.addEventListener('click', () => {
                if (body.classList.contains('expanded')) collapse();
                else expand();
            });
            setInitial();
        }
        makeSectionToggle('decks-toggle',    'decks-chevron',    'decks-body',    true);
        makeSectionToggle('friends-toggle',  'friends-chevron',  'friends-body',  true);
        makeSectionToggle('trainees-toggle', 'trainees-chevron', 'trainees-body', true);
        makeSectionToggle('parents-toggle',  'parents-chevron',  'parents-body',  true);
        makeSectionToggle('friend-vets-toggle', 'friend-vets-chevron', 'friend-vets-body', true);
        makeSectionToggle('cards-toggle',    'cards-chevron',    'card-grid-wrapper', false);
        const applyTheme = theme => {
            const nextTheme = theme === 'blue' ? 'blue' : 'pink';
            document.documentElement.dataset.theme = nextTheme;
            document.documentElement.classList.toggle('theme-blue', nextTheme === 'blue');
            document.body.classList.toggle('theme-blue', nextTheme === 'blue');
            return nextTheme;
        };
        applyTheme(localStorage.getItem('theme'));
        const savedUsername = localStorage.getItem('saved_username');
        const savedPassword = localStorage.getItem('saved_password');
        const savedProxyUrl = localStorage.getItem('saved_proxy_url');
        if (savedUsername) document.getElementById('username').value = savedUsername;
        if (savedPassword) document.getElementById('password').value = savedPassword;
        if (savedProxyUrl && document.getElementById('proxy-url')) document.getElementById('proxy-url').value = savedProxyUrl;
        let themeToggleClicks = 0;
        els.themeToggle.addEventListener('click', () => {
            const nextTheme = document.body.classList.contains('theme-blue') ? 'pink' : 'blue';
            applyTheme(nextTheme);
            localStorage.setItem('theme', nextTheme);
            themeToggleClicks++;
            if (themeToggleClicks >= 11 && els.devBtn) {
                els.devBtn.style.display = 'inline-block';
            }
        });
        window.iwillnotabusethis = function() {
            if (els.devBtn) els.devBtn.style.display = 'inline-block';
            setDevEnabled(true, { persist: true });
        };
        const sleep = ms => new Promise(resolve => window.setTimeout(resolve, ms));
        const nextFrame = () => new Promise(resolve => requestAnimationFrame(resolve));
        async function waitForDomPaint(frames = 2) {
            for (let i = 0; i < frames; i++) await nextFrame();
        }
        async function apiJson(url, options = {}) {
            const res = await fetch(url, options);
            return res.json();
        }
        function setMasterDataStatus(message, stateName = '') {
            if (!els.masterDataStatus) return;
            els.masterDataStatus.textContent = message || '';
            els.masterDataStatus.className = `master-data-status ${stateName}`.trim();
        }
        function applyMasterDataStatus(data) {
            if (!data) return;
            if (els.masterDataPath && data.master_mdb_path) {
                els.masterDataPath.value = data.master_mdb_path;
            }
            if (els.masterDataPath) {
                els.masterDataPath.classList.toggle('needs-action', !data.exists);
            }
            if (data.exists) {
                if (data.generation_error) {
                    setMasterDataStatus(data.generation_error, 'needs-action');
                } else if (data.generated) {
                    setMasterDataStatus('master.mdb found; data generated', 'ok');
                } else {
                    setMasterDataStatus('master.mdb found', 'ok');
                }
            } else {
                setMasterDataStatus(data.access_error || 'master.mdb not found; update the path', 'needs-action');
            }
        }
        async function loadMasterDataStatus() {
            if (!els.masterDataPath) return;
            try {
                applyMasterDataStatus(await apiJson('/api/master-data/status'));
            } catch (e) {
                setMasterDataStatus('Unable to read master data status', 'needs-action');
            }
        }
        async function saveMasterDataPath() {
            if (!els.masterDataPath) return null;
            const master_mdb_path = els.masterDataPath.value.trim();
            if (!master_mdb_path) {
                setMasterDataStatus('Enter the full path to master.mdb', 'needs-action');
                els.masterDataPath.classList.add('needs-action');
                return null;
            }
            if (els.masterDataSaveBtn) els.masterDataSaveBtn.disabled = true;
            setMasterDataStatus('Saving path and generating data...', 'working');
            const data = await apiJson('/api/master-data/path', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ master_mdb_path })
            });
            applyMasterDataStatus(data);
            if (data.exists && !data.generation_error) {
                await loadRaceData();
            }
            if (els.masterDataSaveBtn) els.masterDataSaveBtn.disabled = false;
            return data;
        }
        function bindMasterDataControls() {
            if (!els.masterDataPath) return;
            if (els.masterDataSaveBtn) {
                els.masterDataSaveBtn.addEventListener('click', async () => {
                    try {
                        await saveMasterDataPath();
                    } catch (e) {
                        setMasterDataStatus(e.message || 'Unable to save master.mdb path', 'needs-action');
                        if (els.masterDataPath) els.masterDataPath.classList.add('needs-action');
                    } finally {
                        if (els.masterDataSaveBtn) els.masterDataSaveBtn.disabled = false;
                    }
                });
            }
            els.masterDataPath.addEventListener('input', () => {
                els.masterDataPath.classList.remove('needs-action');
            });
            loadMasterDataStatus();
        }
        function writeLocalSetting(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {}
        }
        function readLocalSetting(value, fallback = null) {
            if (!value) return fallback;
            try {
                return JSON.parse(value);
            } catch (e) {
                return fallback;
            }
        }
        function escapeHtml(value) {
            return String(value ?? '').replace(/[&<>"']/g, char => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[char]));
        }
        function escapeAttr(value) {
            return escapeHtml(value);
        }
        function normalizeDelayBounds(min, max, disabled = false, restoreMin = null, restoreMax = null) {
            const fallbackMin = Number.isFinite(Number(restoreMin)) ? Number(restoreMin) : 1.6;
            const fallbackMax = Number.isFinite(Number(restoreMax)) ? Number(restoreMax) : 3.7;
            if (disabled) return { min: 0, max: 0, restoreMin: fallbackMin, restoreMax: fallbackMax, disabled: true };
            const left = Math.max(0, Number.isFinite(Number(min)) ? Number(min) : fallbackMin);
            let right = Math.max(0, Number.isFinite(Number(max)) ? Number(max) : fallbackMax);
            if (left > right) right = left;
            return { min: left, max: right, restoreMin: left, restoreMax: right, disabled: false };
        }
        function setDelayControls(settings) {
            if (!els.turnDelayMin || !els.turnDelayMax || !els.temptFateBtn) return;
            const disabled = Boolean(settings.disabled);
            const restoreMin = Number.isFinite(Number(settings.restoreMin)) ? Number(settings.restoreMin) : Number(settings.restore_min);
            const restoreMax = Number.isFinite(Number(settings.restoreMax)) ? Number(settings.restoreMax) : Number(settings.restore_max);
            els.turnDelayMin.value = String(settings.min);
            els.turnDelayMax.value = String(settings.max);
            els.turnDelayMin.dataset.restoreValue = String(Number.isFinite(restoreMin) ? restoreMin : settings.min);
            els.turnDelayMax.dataset.restoreValue = String(Number.isFinite(restoreMax) ? restoreMax : settings.max);
            els.turnDelayMin.disabled = disabled;
            els.turnDelayMax.disabled = disabled;
            els.temptFateBtn.classList.toggle('is-active', disabled);
            els.temptFateBtn.innerText = disabled ? 'FATE TEMPTED' : 'TEMPT FATE';
        }
        async function saveDelaySettings(settings) {
            setDelayControls(settings);
            const data = await apiJson('/api/settings/turn-delay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            const normalized = normalizeDelayBounds(data.min, data.max, data.disabled, data.restore_min, data.restore_max);
            setDelayControls(normalized);
            writeLocalSetting(delaySettingsStorageKey, normalized);
        }
        async function loadDelaySettings() {
            if (!els.turnDelayMin || !els.turnDelayMax || !els.temptFateBtn) return;
            try {
                const data = await apiJson('/api/settings/turn-delay');
                setDelayControls(normalizeDelayBounds(data.min, data.max, data.disabled, data.restore_min, data.restore_max));
            } catch (e) {
                setDelayControls({ min: 1.6, max: 3.7, restoreMin: 1.6, restoreMax: 3.7, disabled: false });
            }
        }
        function bindDelayControls() {
            if (!els.turnDelayMin || !els.turnDelayMax || !els.temptFateBtn) return;
            const sync = () => {
                saveDelaySettings(normalizeDelayBounds(els.turnDelayMin.value, els.turnDelayMax.value, false));
            };
            els.turnDelayMin.addEventListener('input', sync);
            els.turnDelayMax.addEventListener('input', sync);
            els.temptFateBtn.addEventListener('click', () => {
                const active = els.temptFateBtn.classList.contains('is-active');
                const restoreMin = Number(els.turnDelayMin.dataset.restoreValue || 1.6);
                const restoreMax = Number(els.turnDelayMax.dataset.restoreValue || 3.7);
                saveDelaySettings(active
                    ? normalizeDelayBounds(restoreMin, restoreMax, false)
                    : normalizeDelayBounds(0, 0, true, restoreMin, restoreMax)
                );
            });
            loadDelaySettings();
        }
        window.addEventListener('storage', event => {
            if (event.key !== delaySettingsStorageKey || !event.newValue) return;
            const settings = readLocalSetting(event.newValue);
            if (settings) setDelayControls(normalizeDelayBounds(settings.min, settings.max, settings.disabled, settings.restoreMin, settings.restoreMax));
        });
        window.addEventListener('storage', event => {
            if (event.key !== burnClocksStorageKey || !event.newValue) return;
            setBurnClocks(readLocalSetting(event.newValue, false));
        });
        function resetLoginState() {
            state.isLoading = false;
            els.loginBtn.innerText = state.needs2fa ? 'VALIDATE' : 'LOGIN';
        }
        function showLoginError(message) {
            setLoadingScreen(false);
            els.errorMsg.innerText = String(message || 'FAIL').toUpperCase();
            els.errorMsg.style.display = 'block';
            resetLoginState();
        }
        function showTwoFactorPrompt() {
            setLoadingScreen(false);
            state.needs2fa = true;
            state.isLoading = false;
            els.standardFields.style.display = 'none';
            els.faFields.style.display = 'block';
            els.loginBtn.innerText = 'VALIDATE';
            els.errorMsg.innerText = '2FA REQUIRED';
            els.errorMsg.style.display = 'block';
        }
        function readLoginPayload() {
            return {
                username: document.getElementById('username').value,
                password: document.getElementById('password').value,
                code: document.getElementById('code').value,
                proxy_url: document.getElementById('proxy-url') ? document.getElementById('proxy-url').value.trim() : ""
            };
        }
        function resetSelection() {
            selection.deck = null;
            selection.friend = null;
            selection.trainee = null;
            selection.veterans = [];
            selection.rentalParent = null;
        }
        function hideBrokenImage(img) {
            img.onerror = null;
            img.style.display = 'none';
        }
        const loginForm = document.getElementById('login-form');
        loginForm.addEventListener('submit', async event => {
            event.preventDefault();
            if (state.isLoading) return;
            state.isLoading = true;
            setLoadingScreen(true);
            els.loginBtn.innerText = 'WORKING...';
            els.errorMsg.style.display = 'none';
            const payload = readLoginPayload();
            try {
                const data = await apiJson('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (data.needs_2fa) {
                    showTwoFactorPrompt();
                } else if (data.success) {
                    localStorage.setItem('saved_username', payload.username);
                    localStorage.setItem('saved_password', payload.password);
                    localStorage.setItem('saved_proxy_url', payload.proxy_url);
                    try {
                        await apiJson('/api/session-cache', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                steam_username: payload.username,
                                steam_password: payload.password,
                                proxy_url: payload.proxy_url
                            })
                        });
                    } catch (ex) {}
                    await renderDashboard(data, { animateIntro: true, waitForIntro: true });
                    state.isLoading = false;
                } else {
                    showLoginError(data.detail || 'FAIL');
                }
            } catch (e) {
                showLoginError('NETWORK ERROR');
            }
        });

        els.logoutBtn.addEventListener('click', async () => {
            setLoadingScreen(false);
            try {
                await apiJson('/api/logout', { method: 'POST' });
            } catch (e) {}
            document.body.classList.remove('dashboard-mode');
            hideNavbar();
            els.loginView.style.display = 'flex';
            els.dashboardView.style.display = 'none';
            els.dashboardView.classList.remove('active');
            els.logoutBtn.style.display = 'none';
            els.standardFields.style.display = 'block';
            els.faFields.style.display = 'none';
            els.loginBtn.innerText = 'LOGIN';
            els.accountStrip.style.display = 'none';
            els.accountStrip.innerHTML = '';
            state.account = null;
            state.needs2fa = false;
            dashData = null;
            resetSelection();
            syncDashboardHeight();
            loginForm.reset();
            loadAndRenderSessionCache();
        });

        const formatNumber = value => Number(value || 0).toLocaleString();
        const CAREER_MODAL_DEFAULT_COPY = '<strong>FINISH</strong>: spends leftover SP on skills then saves the trained character so you can start a new run.<br><strong>DELETE</strong>: aborts the current career without saving (force delete).';
        function setCareerModalCopy(html) {
            if (!els.careerModalCopy) return;
            els.careerModalCopy.innerHTML = html;
        }
        function closeCareerModal() {
            els.careerModal.style.display = 'none';
            setCareerModalCopy(CAREER_MODAL_DEFAULT_COPY);
            els.careerDeleteBtn.innerText = 'DELETE';
            els.careerDeleteBtn.disabled = false;
            if (els.careerFinishBtn) {
                els.careerFinishBtn.innerText = 'FINISH';
                els.careerFinishBtn.disabled = false;
            }
            state.isDeletingCareer = false;
            state.isFinishingCareer = false;
        }
        function openCareerModal() {
            const career = state.account && state.account.career;
            if (!career || !career.active) return;
            setCareerModalCopy(CAREER_MODAL_DEFAULT_COPY);
            els.careerModal.style.display = 'flex';
        }
        function lockCareerModalButtons() {
            els.careerDeleteBtn.disabled = true;
            if (els.careerFinishBtn) els.careerFinishBtn.disabled = true;
        }
        async function deleteCareer() {
            const career = state.account && state.account.career;
            if (!career || !career.active || state.isDeletingCareer || state.isFinishingCareer) return;
            state.isDeletingCareer = true;
            lockCareerModalButtons();
            els.careerDeleteBtn.innerText = 'DELETING';
            setCareerModalCopy('Force-deleting ongoing career...');
            try {
                const data = await apiJson('/api/career/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ current_turn: career.turn || 0 })
                });
                if (!data.success) throw new Error(data.detail || 'Delete failed');
                renderAccountStrip(data.account);
                closeCareerModal();
            } catch (e) {
                setCareerModalCopy(escapeHtml(e.message || 'Delete failed'));
                els.careerDeleteBtn.innerText = 'RETRY';
                els.careerDeleteBtn.disabled = false;
                if (els.careerFinishBtn) els.careerFinishBtn.disabled = false;
                state.isDeletingCareer = false;
            }
        }
        async function finishCareer() {
            const career = state.account && state.account.career;
            if (!career || !career.active || state.isFinishingCareer || state.isDeletingCareer) return;
            state.isFinishingCareer = true;
            lockCareerModalButtons();
            els.careerFinishBtn.innerText = 'FINISHING';
            setCareerModalCopy('Buying remaining skills and saving the trained character...');
            try {
                const data = await apiJson('/api/career/finish', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_turn: career.turn || 0,
                        preset_name: state.selectedPreset || '',
                        buy_skills: true,
                    })
                });
                if (!data.success) throw new Error(data.detail || 'Finish failed');
                renderAccountStrip(data.account);
                const skills = Number(data.skills_bought || 0);
                const before = Number(data.sp_before || 0);
                const after = Number(data.sp_after || 0);
                setCareerModalCopy(`Career saved. Skills bought: <strong>${skills}</strong> · SP spent: <strong>${Math.max(0, before - after)}</strong> (was ${before}, now ${after}).`);
                setTimeout(closeCareerModal, 1800);
            } catch (e) {
                setCareerModalCopy(escapeHtml(e.message || 'Finish failed'));
                els.careerFinishBtn.innerText = 'RETRY';
                els.careerFinishBtn.disabled = false;
                els.careerDeleteBtn.disabled = false;
                state.isFinishingCareer = false;
            }
        }
        els.careerCancelBtn.addEventListener('click', closeCareerModal);
        els.careerDeleteBtn.addEventListener('click', deleteCareer);
        if (els.careerFinishBtn) els.careerFinishBtn.addEventListener('click', finishCareer);
        els.careerModal.addEventListener('click', event => {
            if (event.target === els.careerModal) closeCareerModal();
        });
        function syncBurnClocksControls() {
            if (!els.burnClocksBtn) return;
            const clocks = state.account ? Number(state.account.clocks || 0) : 0;
            const disabled = clocks <= 11;

            if (disabled) {
                state.burnClocks = false;
                els.burnClocksBtn.disabled = true;
                els.burnClocksBtn.classList.remove('is-active');
                els.burnClocksBtn.innerText = `BURN CLOCKS: LOW (${clocks})`;
            } else {
                els.burnClocksBtn.disabled = false;
                els.burnClocksBtn.classList.toggle('is-active', state.burnClocks);
                els.burnClocksBtn.innerText = `BURN CLOCKS: ${state.burnClocks ? 'ON' : 'OFF'}`;
            }
        }
        function setBurnClocks(value, options = {}) {
            state.burnClocks = Boolean(value);
            syncBurnClocksControls();
            if (options.persist) writeLocalSetting(burnClocksStorageKey, state.burnClocks);
        }
        function loadStoredBurnClocks() {
            if (state.runner && state.runner.running) return;
            const stored = readLocalSetting(localStorage.getItem(burnClocksStorageKey));
            if (stored !== null) setBurnClocks(stored);
        }

        function renderAccountStrip(account) {
            state.account = account || null;
            if (!account) {
                els.accountStrip.style.display = 'none';
                els.accountStrip.innerHTML = '';
                return;
            }
            const tp = account.tp || {};
            const career = account.career;
            const careerHtml = career && career.active ? `
                <div id="career-pill" class="account-pill pill-career account-pill-clickable">
                    <span class="label">CAREER</span>
                    <strong>ONGOING</strong>
                </div>
            ` : `<div class="account-pill" style="opacity: 0.25;">
                    <span class="label">CAREER</span>
                    <strong>NONE</strong>
                </div>`;
            const carrots = account.carrots || {};
            const canRefillTp = !state.isRefillingTp && Number(tp.current || 0) < Number(tp.max || 0);
            els.accountStrip.innerHTML = `
                <div class="account-pill pill-tp">
                    <span class="label">TP</span>
                    <strong>${tp.current || 0}/${tp.max || 0}</strong>
                    <button id="tp-refill-btn" class="pill-mini-btn" type="button" ${canRefillTp ? '' : 'disabled'}>${state.isRefillingTp ? '...' : 'REFILL'}</button>
                </div>
                <div class="account-pill pill-carrots">
                    <span class="label">CARROTS</span>
                    <strong>${formatNumber(carrots.total)}</strong>
                </div>
                <div class="account-pill pill-gold">
                    <span class="label">GOLD</span>
                    <strong>${formatNumber(account.gold)}</strong>
                </div>
                <div class="account-pill pill-clk">
                    <span class="label">CLOCKS</span>
                    <strong>${formatNumber(account.clocks)}</strong>
                </div>
                ${careerHtml}
            `;
            els.accountStrip.style.display = 'flex';
            const careerPill = document.getElementById('career-pill');
            if (careerPill) careerPill.addEventListener('click', openCareerModal);
            const tpRefillBtn = document.getElementById('tp-refill-btn');
            if (tpRefillBtn) tpRefillBtn.addEventListener('click', refillTp);
            loadStoredBurnClocks();
            syncBurnClocksControls();
        }

        async function refillTp(event) {
            if (event) event.stopPropagation();
            if (state.isRefillingTp) return;
            state.isRefillingTp = true;
            renderAccountStrip(state.account);
            try {
                const data = await apiJson('/api/tp/refill', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ to_max: true })
                });
                if (!data.success) throw new Error(data.detail || 'TP refill failed');
                if (data.account) renderAccountStrip(data.account);
            } catch (e) {
                console.error('TP refill failed', e);
                if (els.startStatus) {
                    els.startStatus.innerText = e.message || 'TP refill failed';
                    els.startStatus.classList.add('error');
                }
            } finally {
                state.isRefillingTp = false;
                renderAccountStrip(state.account);
            }
        }

        els.burnClocksBtn.addEventListener('click', async () => {
            setBurnClocks(!state.burnClocks, { persist: true });
            if (state.runner && state.runner.running) {
                try {
                    const data = await apiJson('/api/career/runner/burn_clocks', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ burn_clocks: state.burnClocks })
                    });
                    if (!data.success) throw new Error(data.detail || 'Failed to update burn_clocks');
                    if (data.runner) applyRunnerSnapshot(data.runner);
                } catch (e) {
                    console.error("Failed to update burn_clocks mid-run", e);
                    if (state.runner && state.runner.burn_clocks !== undefined) {
                        setBurnClocks(state.runner.burn_clocks, { persist: true });
                    }
                }
            }
        });

        // ---- Event Boost (TP Usage x2) -------------------------------------------------
        // Mirrors the in-game "Event Boost" checkbox. When enabled, the career start
        // payload sets is_boost=1 + boost_story_event_id=<configured> and doubles
        // use_tp so the backend's "not enough TP" guard matches the server-side cost.
        const SCENARIO_BASE_TP_COST = 30;
        let eventBoostSaveTimer = 0;
        function syncEventBoostControls() {
            if (!els.eventBoostCheckbox || !els.eventBoostEventId) return;
            const cfg = state.eventBoost || { enabled: false, story_event_id: 0, tp_multiplier: 2 };
            els.eventBoostCheckbox.checked = !!cfg.enabled;
            const idStr = String(cfg.story_event_id || 0);
            if (document.activeElement !== els.eventBoostEventId) {
                els.eventBoostEventId.value = idStr === '0' ? '' : idStr;
            }
            renderEventBoostStatus();
        }
        function renderEventBoostStatus() {
            if (!els.eventBoostStatus) return;
            const cfg = state.eventBoost || {};
            if (!cfg.enabled) {
                els.eventBoostStatus.innerText = '';
                els.eventBoostStatus.classList.remove('error', 'is-active');
                return;
            }
            if (!cfg.story_event_id) {
                els.eventBoostStatus.innerText = 'Set the story event ID to activate boost.';
                els.eventBoostStatus.classList.remove('is-active');
                els.eventBoostStatus.classList.add('error');
                return;
            }
            const mult = Number(cfg.tp_multiplier || 2);
            els.eventBoostStatus.innerText = `Boost ON · TP usage x${mult} (${SCENARIO_BASE_TP_COST * mult}/career) · event #${cfg.story_event_id}`;
            els.eventBoostStatus.classList.remove('error');
            els.eventBoostStatus.classList.add('is-active');
        }
        function resolveEventBoostForStart() {
            const cfg = state.eventBoost || {};
            const enabled = !!cfg.enabled && Number(cfg.story_event_id || 0) > 0;
            const mult = Math.max(1, Number(cfg.tp_multiplier || 2));
            return {
                isBoost: enabled ? 1 : 0,
                storyEventId: enabled ? Number(cfg.story_event_id) : 0,
                useTp: enabled ? SCENARIO_BASE_TP_COST * mult : SCENARIO_BASE_TP_COST,
            };
        }
        async function fetchEventBoostSettings() {
            try {
                const data = await apiJson('/api/settings/event-boost');
                if (data && data.success) {
                    state.eventBoost = {
                        enabled: !!data.enabled,
                        story_event_id: Number(data.story_event_id || 0),
                        tp_multiplier: Number(data.tp_multiplier || 2),
                    };
                }
            } catch (e) {
                console.error('Failed to load event boost settings', e);
            }
            syncEventBoostControls();
        }
        async function saveEventBoostSettings() {
            const cfg = state.eventBoost || {};
            try {
                const data = await apiJson('/api/settings/event-boost', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        enabled: !!cfg.enabled,
                        story_event_id: Number(cfg.story_event_id || 0),
                    })
                });
                if (data && data.success) {
                    state.eventBoost = {
                        enabled: !!data.enabled,
                        story_event_id: Number(data.story_event_id || 0),
                        tp_multiplier: Number(data.tp_multiplier || 2),
                    };
                    syncEventBoostControls();
                }
            } catch (e) {
                console.error('Failed to save event boost settings', e);
            }
        }
        function queueEventBoostSave() {
            if (eventBoostSaveTimer) clearTimeout(eventBoostSaveTimer);
            eventBoostSaveTimer = setTimeout(() => {
                eventBoostSaveTimer = 0;
                saveEventBoostSettings();
            }, 400);
        }
        if (els.eventBoostCheckbox) {
            els.eventBoostCheckbox.addEventListener('change', () => {
                state.eventBoost = {
                    ...(state.eventBoost || {}),
                    enabled: !!els.eventBoostCheckbox.checked,
                };
                renderEventBoostStatus();
                saveEventBoostSettings();
            });
        }
        if (els.eventBoostEventId) {
            els.eventBoostEventId.addEventListener('input', () => {
                const parsed = Math.max(0, Math.floor(Number(els.eventBoostEventId.value || 0)));
                state.eventBoost = {
                    ...(state.eventBoost || {}),
                    story_event_id: parsed,
                };
                renderEventBoostStatus();
                queueEventBoostSave();
            });
            els.eventBoostEventId.addEventListener('blur', () => {
                if (eventBoostSaveTimer) {
                    clearTimeout(eventBoostSaveTimer);
                    eventBoostSaveTimer = 0;
                    saveEventBoostSettings();
                }
            });
        }

        const rankMap = {
            1: 'G', 2: 'G+', 3: 'F', 4: 'F+', 5: 'E', 6: 'E+',
            7: 'D', 8: 'D+', 9: 'C', 10: 'C+', 11: 'B', 12: 'B+',
            13: 'A', 14: 'A+', 15: 'S', 16: 'S+', 17: 'SS', 18: 'SS+',
            19: 'UG', 20: 'UF', 21: 'UE', 22: 'UD'
        };
        let dashData = null;
        const selection = { deck: null, friend: null, trainee: null, veterans: [], rentalParent: null };

        async function syncSelectionToServer() {
            try {
                const payload = {
                    deck: selection.deck,
                    friend: selection.friend,
                    trainee: selection.trainee,
                    veterans: selection.veterans,
                    rentalParent: selection.rentalParent
                };
                await apiJson('/api/selection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ selection: payload })
                });
            } catch (e) {}
        }

        function deselect(action, idx) {
            if (action === 'deck') {
                document.querySelectorAll('.deck-container.selected').forEach(el => el.classList.remove('selected'));
                selection.deck = null;
            } else if (action === 'friend') {
                document.querySelectorAll('#friend-grid .grid-card.selected').forEach(el => el.classList.remove('selected'));
                selection.friend = null;
            } else if (action === 'trainee') {
                document.querySelectorAll('#uma-grid .grid-card.selected').forEach(el => el.classList.remove('selected'));
                selection.trainee = null;
            } else if (action === 'vet') {
                const vet = selection.veterans[idx];
                if (vet != null) {
                    const card = document.querySelectorAll('#parent-grid .grid-card')[vet._gridIdx];
                    if (card) card.classList.remove('selected');
                }
                selection.veterans.splice(idx, 1);
                updateVetSelectability();
            } else if (action === 'rental') {
                selection.rentalParent = null;
                syncFriendVeteranSelection();
                savePresetRentalChara();
                updateVetSelectability();
            }
            renderTeamPanel();
            syncSelectionToServer();
        }
        function getStartMissingReason() {
            const activeCareer = state.account && state.account.career && state.account.career.active;
            if (!state.selectedPreset) return 'Select a preset';
            if (activeCareer) return '';
            if (!selection.deck) return 'Select a deck';
            if (!selection.friend) return 'Select a friend support';
            if (!selection.trainee) return 'Select a trainee';
            const ownParentCount = selection.veterans.length;
            const totalParentCount = ownParentCount + (selection.rentalParent ? 1 : 0);
            if (ownParentCount < 1) return 'Select at least one parent';
            if (totalParentCount < 2) return 'Select a second parent (own or borrowed)';
            const parentError = getParentSelectionError();
            if (parentError) return parentError;
            const tp = state.account && state.account.tp ? Number(state.account.tp.current || 0) : 0;
            if (state.account && tp < 30 && !state.devEnabled) return `Not enough TP: ${tp}/30`;
            return '';
        }
        function getParentLineageCards(parent) {
            if (!parent || !parent.tree) return [];
            return ['self', 'p1', 'p2', 'gp1', 'gp2', 'gp3', 'gp4']
                .map(key => Number(parent.tree[key] && parent.tree[key].card_id))
                .filter(Boolean);
        }
        function getParentSelectionError() {
            if (!selection.trainee) return '';
            const traineeId = Number(selection.trainee.id);
            const lineages = selection.veterans.map(getParentLineageCards);
            if (lineages.length < 2) return '';
            if (lineages.some(cards => cards[0] === traineeId)) return 'Direct parent is trainee';
            return '';
        }
        function syncStartButton() {
            const reason = getStartMissingReason();
            els.startCareerBtn.disabled = Boolean(reason) || state.isStartingCareer;
            if (state.isStartingCareer) {
                els.startCareerBtn.innerText = 'RUNNING...';
                els.startStatus.innerText = 'Starting runner...';
                els.startStatus.classList.remove('error');
            } else {
                const activeCareer = state.account && state.account.career && state.account.career.active;
                els.startCareerBtn.innerText = activeCareer ? 'RESUME CAREER' : 'RUN CAREER';
                els.startStatus.innerText = reason;
                els.startStatus.classList.toggle('error', false);
            }
        }
        function currentRunningStyle() {
            const preset = getCurrentPreset();
            return Number((preset && preset.running_style) || els.presetRunningStyle?.value || 0);
        }
        function selectedCandidateIds() {
            const ids = new Set();
            (selection.veterans || []).forEach(parent => {
                if (parent && parent.instance_id) ids.add(`owned:${parent.instance_id}`);
            });
            const rental = selection.rentalParent;
            if (rental && rental.viewer_id && rental.trained_chara_id) {
                ids.add(`rental:${rental.viewer_id}:${rental.trained_chara_id}`);
            }
            return ids;
        }
        function renderAdvisorPanel() {
            if (!els.advisorPanel) return;
            const rows = state.advisorRecommendations || [];
            if (!selection.trainee) {
                els.advisorPanel.innerHTML = '<div class="advisor-muted">Select a trainee to score parent quality.</div>';
                return;
            }
            if (!rows.length) {
                els.advisorPanel.innerHTML = '<div class="advisor-muted">Parent advisor will appear after friend/parent data loads.</div>';
                return;
            }
            const selectedIds = selectedCandidateIds();
            const selectedRows = rows.filter(row => selectedIds.has(row.candidate_id));
            const topRows = rows.slice(0, 5);
            const selectedWarnings = selectedRows.flatMap(row => (row.advisor && row.advisor.warnings) || []);
            const renderRow = row => {
                const score = row.advisor ? row.advisor.score : 0;
                const name = row.name || row.chara_name || row.trainer_name || 'Unknown';
                const source = row.source === 'rental' ? 'borrow' : 'owned';
                const reasons = ((row.advisor && row.advisor.reasons) || []).join(' · ');
                return `<div class="advisor-row ${selectedIds.has(row.candidate_id) ? 'is-selected' : ''}">
                    <span class="advisor-score">${Number(score || 0).toFixed(1)}</span>
                    <span class="advisor-name">${escapeHtml(name)}</span>
                    <span class="advisor-source">${escapeHtml(source)}</span>
                    <span class="advisor-reason">${escapeHtml(reasons)}</span>
                </div>`;
            };
            els.advisorPanel.innerHTML = `
                <div class="advisor-title">Runtime Advisor</div>
                ${selectedWarnings.length ? `<div class="advisor-warning">${Array.from(new Set(selectedWarnings)).map(escapeHtml).join(' · ')}</div>` : '<div class="advisor-ok">No obvious selected-parent warning.</div>'}
                <div class="advisor-subtitle">Best parent candidates</div>
                <div class="advisor-list">${topRows.map(renderRow).join('')}</div>
            `;
        }
        async function updateAdvisorRecommendations() {
            renderAdvisorPanel();
            if (!dashData || !selection.trainee) return;
            try {
                const res = await apiJson('/api/advisor/recommendations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        trainee_card_id: Number(selection.trainee.id || 0),
                        running_style: currentRunningStyle(),
                    })
                });
                if (res.success) {
                    state.advisorRecommendations = res.recommendations || [];
                    renderAdvisorPanel();
                }
            } catch (e) {}
        }
        function renderTeamPanel() {
            document.getElementById('dashboard-view').classList.add('active');
            function setSlot(id, role, content, action, idx, emptyText = 'select') {
                const el = document.getElementById(id);
                el.className = content ? 'team-item filled' : 'team-item';
                el.onclick = content ? () => deselect(action, idx) : null;
                const clear = content ? '<span class="team-item-clear">clear</span>' : '';
                const empty = `<div class="team-item-empty">${emptyText}</div>`;
                el.innerHTML = `
                    <div class="team-item-head">
                        <span class="team-item-role">${role}</span>
                        ${clear}
                    </div>
                    ${content || empty}
                `;
            }
            if (selection.deck) {
                const thumbs = selection.deck.cards.map(c =>
                    `<img class="team-item-thumb" src="/api/images/${c.id || '10001'}.png" onerror="hideBrokenImage(this)">`
                ).join('');
                setSlot('team-slot-deck', 'Deck', `
                    <div class="team-item-body">
                        <div class="team-item-thumbs">${thumbs}</div>
                        <div class="team-item-text">
                            <span class="team-item-name">${selection.deck.name}</span>
                            <span class="team-item-sub">Slot ${selection.deck.id}</span>
                        </div>
                    </div>
                `, 'deck', null, 'select deck');
            } else {
                setSlot('team-slot-deck', 'Deck', null, 'deck', null, 'select deck');
            }
            if (selection.friend) {
                setSlot('team-slot-friend', 'Friend', `
                    <div class="team-item-body">
                        <img class="team-item-portrait" src="/api/images/${selection.friend.support_card_id || '10001'}.png" onerror="hideBrokenImage(this)">
                        <div class="team-item-text">
                            <span class="team-item-name">${selection.friend.support_name || 'Unknown'}</span>
                            <span class="team-item-sub">${selection.friend.type || '?'} | LB${selection.friend.limit_break_count ?? '?'}</span>
                        </div>
                    </div>
                `, 'friend', null, 'select friend');
            } else {
                setSlot('team-slot-friend', 'Friend', null, 'friend', null, 'select friend');
            }
            if (selection.trainee) {
                setSlot('team-slot-trainee', 'Trainee', `
                    <div class="team-item-body">
                        <img class="team-item-portrait" src="/api/images/${selection.trainee.id || '100101'}.png" onerror="hideBrokenImage(this)">
                        <div class="team-item-text">
                            <span class="team-item-name">${selection.trainee.name || 'Unknown'}</span>
                        </div>
                    </div>
                `, 'trainee', null, 'select trainee');
            } else {
                setSlot('team-slot-trainee', 'Trainee', null, 'trainee', null, 'select trainee');
            }
            ['team-slot-vet1', 'team-slot-vet2'].forEach((id, i) => {
                const vet = selection.veterans[i];
                if (vet) {
                    setSlot(id, `Parent ${i + 1}`, `
                        <div class="team-item-body">
                            <img class="team-item-portrait" src="/api/images/${vet.card_id || '100101'}.png" onerror="hideBrokenImage(this)">
                            <div class="team-item-text">
                                <span class="team-item-name">${vet.name || 'Unknown'}</span>
                                <span class="team-item-sub">${rankMap[vet.rank] || '??'}</span>
                            </div>
                        </div>
                    `, 'vet', i, 'select parent');
                    return;
                }
                const rental = selection.rentalParent;
                if (rental && i === 1) {
                    const rentalName = rental.chara_name || rental.name || 'Unknown';
                    const rentalRank = rental.rank ? (rankMap[rental.rank] || '??') : '';
                    const trainer = rental.trainer_name ? ` &middot; ${escapeHtml(rental.trainer_name)}` : '';
                    setSlot(id, `Parent ${i + 1}`, `
                        <div class="team-item-body">
                            <img class="team-item-portrait" src="/api/images/${rental.card_id || '100101'}.png" onerror="hideBrokenImage(this)">
                            <div class="team-item-text">
                                <span class="team-item-name">${escapeHtml(rentalName)} <span class="team-item-tag">borrowed</span></span>
                                <span class="team-item-sub">${rentalRank}${trainer}</span>
                            </div>
                        </div>
                    `, 'rental', null, 'select parent');
                    return;
                }
                setSlot(id, `Parent ${i + 1}`, null, 'vet', i, 'select parent');
            });
            syncStartButton();
            renderAdvisorPanel();
        }
                function updateVetSelectability() {
            const full = selection.veterans.length >= 2;
            document.querySelectorAll('#parent-grid .grid-card').forEach(card => {
                if (card.classList.contains('selected')) {
                    card.classList.remove('vet-full');
                } else {
                    card.classList.toggle('vet-full', full);
                }
            });
            syncStartButton();
        }
        function clampValue(value, min, max) {
            return Math.min(Math.max(value, min), max);
        }
        let activeSparkCard = null;
        let activeSparkTooltip = null;
        function positionSparkTooltip(card, tooltip = card.querySelector('.sparks-tooltip')) {
            if (!card || !tooltip) return;
            const rect = card.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            const tooltipWidth = Math.min(tooltipRect.width || 620, window.innerWidth - 16);
            const tooltipHeight = tooltipRect.height || 320;
            const x = clampValue(rect.left + rect.width / 2, tooltipWidth / 2 + 8, window.innerWidth - tooltipWidth / 2 - 8);
            const y = Math.max(8, rect.top - tooltipHeight - 10);
            tooltip.style.setProperty('--tooltip-left', `${x}px`);
            tooltip.style.setProperty('--tooltip-top', `${y}px`);
        }
        function bindSparkTooltips() {
            document.querySelectorAll('body > .sparks-tooltip').forEach(tooltip => tooltip.remove());
            document.querySelectorAll('#parent-grid .grid-card').forEach(card => {
                const tooltip = card.querySelector('.sparks-tooltip');
                if (!tooltip) return;
                card.classList.add('has-sparks');
                const show = () => {
                    if (tooltip.parentElement !== document.body) document.body.appendChild(tooltip);
                    activeSparkCard = card;
                    activeSparkTooltip = tooltip;
                    positionSparkTooltip(card, tooltip);
                    tooltip.classList.add('is-visible');
                };
                const hide = () => {
                    if (activeSparkCard === card) {
                        activeSparkCard = null;
                        activeSparkTooltip = null;
                    }
                    tooltip.classList.remove('is-visible');
                };
                tooltip.addEventListener('click', event => event.stopPropagation());
                tooltip.addEventListener('mousedown', event => event.stopPropagation());
                card.addEventListener('mouseenter', show);
                card.addEventListener('mouseleave', hide);
                card.addEventListener('focusin', show);
                card.addEventListener('focusout', hide);
            });
        }
        document.addEventListener('scroll', () => {
            if (activeSparkCard && activeSparkTooltip) positionSparkTooltip(activeSparkCard, activeSparkTooltip);
        }, true);
        window.addEventListener('resize', () => {
            if (activeSparkCard && activeSparkTooltip) positionSparkTooltip(activeSparkCard, activeSparkTooltip);
        });
        function friendKey(friend) {
            return `${friend.viewer_id}:${friend.support_card_id}`;
        }
        function normalizedCardName(value) {
            return String(value || '').toLowerCase().replace(/\([^)]*\)/g, '').replace(/[^a-z0-9]+/g, '');
        }
        function friendAllowed(friend) {
            if (!friend) return false;
            const friendId = String(friend.support_card_id || '');
            const friendName = normalizedCardName(friend.support_name);
            if (selection.deck) {
                const deckIds = new Set(selection.deck.cards.map(card => String(card.id || '')));
                if (deckIds.has(friendId)) return false;
                const deckNames = new Set(selection.deck.cards.map(card => normalizedCardName(card.name)));
                if (friendName && deckNames.has(friendName)) return false;
            }
            if (selection.trainee && friendName && normalizedCardName(selection.trainee.name) === friendName) return false;
            return true;
        }
        function friendStateLabel(value) {
            const stateId = Number(value || 0);
            if (stateId >= 3) return 'mutual';
            if (stateId === 2) return 'following';
            if (stateId === 1) return 'follower';
            return 'not followed';
        }
        function friendManageRows() {
            const byViewer = new Map();
            ((dashData && dashData.friends) || []).forEach(friend => {
                const viewerId = String(friend.viewer_id || '');
                if (!viewerId) return;
                const existing = byViewer.get(viewerId);
                const existingState = existing ? Number(existing.friend_state || 0) : -1;
                if (!existing || Number(friend.friend_state || 0) >= existingState) {
                    byViewer.set(viewerId, friend);
                }
            });
            return Array.from(byViewer.values())
                .filter(friend => Number(friend.friend_state || 0) > 0)
                .sort((a, b) => String(a.name || '').localeCompare(String(b.name || '')));
        }
        function renderFriendManageList() {
            if (!els.friendFollowList) return;
            const rows = friendManageRows();
            if (!rows.length) {
                els.friendFollowList.innerHTML = '<div class="friend-follow-list-empty">No loaded following/follower entries yet. Refresh friends after following someone.</div>';
                return;
            }
            els.friendFollowList.innerHTML = `
                <div class="friend-follow-list-title">Loaded relationships</div>
                ${rows.map(friend => {
                    const viewerId = escapeAttr(String(friend.viewer_id || ''));
                    const name = escapeHtml(friend.name || `Trainer ${viewerId}`);
                    const support = escapeHtml(friend.support_name || 'Unknown support');
                    const relation = escapeHtml(friendStateLabel(friend.friend_state));
                    return `<div class="friend-follow-row">
                        <div class="friend-follow-row-main">
                            <span class="friend-follow-row-name">${name}</span>
                            <span class="friend-follow-row-meta">${viewerId} · ${support} · ${relation}</span>
                        </div>
                        <button class="btn btn-sm friend-follow-row-action" type="button" data-viewer-id="${viewerId}">UNFOLLOW</button>
                    </div>`;
                }).join('')}
            `;
            els.friendFollowList.querySelectorAll('.friend-follow-row-action').forEach(btn => {
                btn.addEventListener('click', () => manageFollow('unfollow', Number(btn.dataset.viewerId || 0)));
            });
        }
        function renderSupportDeckStrip(cardsOrIds, className = 'support-deck-strip') {
            const cards = (cardsOrIds || []).map(item => {
                if (item && typeof item === 'object') return item;
                return { id: item };
            }).filter(card => card && (card.id || card.support_card_id));
            if (!cards.length) return '';
            return `<div class="${className}">${cards.slice(0, 6).map(card => {
                const id = card.id || card.support_card_id;
                const title = escapeAttr(`${card.name || id} ${card.type ? '(' + card.type + ')' : ''}`);
                return `<img src="/api/images/${escapeAttr(String(id))}.png" title="${title}" onerror="hideBrokenImage(this)">`;
            }).join('')}</div>`;
        }
        function getVisibleFriends() {
            const friends = (dashData && dashData.friends) || [];
            const allowed = friends.filter(friendAllowed);
            
            const query = (state.filters.friends.query || '').toLowerCase().trim();
            const type = state.filters.friends.type;
            const lb = state.filters.friends.limitBreak;
            
            return allowed.filter(friend => {
                if (query) {
                    const cName = String(friend.support_name || '').toLowerCase();
                    const tName = String(friend.trainer_name || '').toLowerCase();
                    const fId = String(friend.viewer_id || '').toLowerCase();
                    if (!cName.includes(query) && !tName.includes(query) && !fId.includes(query)) return false;
                }
                if (type !== 'all' && friend.type !== type) return false;
                if (!state.filters.friends.rarity[friend.rarity]) return false;
                if (lb !== 'all') {
                    if (lb === '4' && Number(friend.limit_break_count || 0) < 4) return false;
                }
                return true;
            });
        }
        function clearInvalidFriendSelection() {
            if (selection.friend && !friendAllowed(selection.friend)) {
                selection.friend = null;
            }
        }
        function syncFriendSelection() {
            const visibleFriends = (dashData && dashData.visibleFriends) || [];
            document.querySelectorAll('#friend-grid .grid-card').forEach((el, i) => {
                const friend = visibleFriends[i];
                el.classList.toggle('selected', Boolean(selection.friend && friend && friendKey(selection.friend) === friendKey(friend)));
            });
        }
        function findDeckIndexForCareer(activeCareer) {
            const decks = (dashData && dashData.validDecks) || [];
            if (!activeCareer || !decks.length) return -1;
            if (activeCareer.deck_id) {
                const deckIdx = decks.findIndex(d => Number(d.id) === Number(activeCareer.deck_id));
                if (deckIdx >= 0) return deckIdx;
            }
            const supportIds = (activeCareer.support_card_ids || []).map(id => String(id)).filter(Boolean);
            if (!supportIds.length) return -1;
            const careerSet = new Set(supportIds);
            return decks.findIndex(deck => {
                const deckIds = (deck.cards || []).map(card => String(card.id || '')).filter(Boolean);
                return deckIds.length === careerSet.size && deckIds.every(id => careerSet.has(id));
            });
        }
        function selectCareerDeck(activeCareer) {
            const deckIdx = findDeckIndexForCareer(activeCareer);
            if (deckIdx >= 0) {
                selection.deck = dashData.validDecks[deckIdx];
                const deckEls = document.querySelectorAll('.deck-container');
                if (deckEls[deckIdx]) deckEls[deckIdx].classList.add('selected');
                return;
            }
            const supportCards = (activeCareer && activeCareer.support_cards) || [];
            if (supportCards.length) {
                selection.deck = {
                    id: activeCareer.deck_id || 'active',
                    name: activeCareer.deck_id ? `Deck ${activeCareer.deck_id}` : 'Active career deck',
                    cards: supportCards
                };
            }
        }
        function selectCareerFriend(activeCareer) {
            if (!activeCareer || !activeCareer.friend_viewer_id || !activeCareer.friend_card_id) return;
            state.pendingFriendSelection = {
                viewer_id: String(activeCareer.friend_viewer_id),
                support_card_id: String(activeCareer.friend_card_id)
            };
            if (activeCareer.friend) {
                selection.friend = {
                    ...activeCareer.friend,
                    viewer_id: String(activeCareer.friend_viewer_id),
                    support_card_id: String(activeCareer.friend_card_id)
                };
            }
        }
        async function loadRaceData() {
            try {
                const raceRes = await fetch('/assets/data/uma_race_data.json');
                const data = await raceRes.json();
                state.raceData = Array.isArray(data.races) ? data.races : [];
                syncSelectedPresetRaces();
                renderRaces();
            } catch (e) {}
        }

        function getCurrentPreset() {
            return (state.presets || []).find(p => p.name === state.selectedPreset);
        }

        function normalizePresetName(value) {
            return String(value || '').trim().replace(/[^a-zA-Z0-9._ -]+/g, '').replace(/\s+/g, ' ').trim();
        }

        function presetNameExists(name) {
            const normalized = normalizePresetName(name).toLowerCase();
            return Boolean(normalized && (state.presets || []).some(p => p.name.toLowerCase() === normalized));
        }

        function syncSelectedPresetRaces() {
            const current = getCurrentPreset();
            state.selectedRaces = (current?.extra_race_list || [])
                .map(id => parseInt(id, 10))
                .filter(id => Number.isFinite(id));
        }

        function getYearSlots(yearIdx) {
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const periods = ['Early', 'Late'];
            const yearLabels = ['Junior Year', 'Classic Year', 'Senior Year'];
            const slots = [];
            for (const month of months) {
                for (const period of periods) {
                    const label = period + ' ' + month;
                    const datePrefix = yearLabels[yearIdx] + ' ' + label;
                    const races = state.raceData.filter(r => r.date.includes(datePrefix));
                    slots.push({ period: label, races: races, yearIdx: yearIdx });
                }
            }
            return slots;
        }

        function raceKeys(race) {
            // Presets may store any of: the full UI id (e.g. 100629), one of the
            // legacy_ids (e.g. 2004), or the bare program_id (e.g. 629 — what the
            // uma.moe importer writes). Treat all three as equivalent for selector
            // highlighting and toggling.
            const keys = [race.id, race.program_id, ...(race.legacy_ids || [])];
            return keys.map(id => parseInt(id)).filter(id => Number.isFinite(id));
        }

        function raceSelected(race) {
            return raceKeys(race).some(id => state.selectedRaces.includes(id));
        }

        function renderRaces() {
            if (!els.raceOptionsContent) return;
            els.raceOptionsContent.innerHTML = '';

            const yearLabels = ['Junior Year', 'Classic Year', 'Senior Year'];
            yearLabels.forEach((label, yi) => {
                const block = document.createElement('div');
                block.className = 'race-year-block';
                block.innerHTML = `<div class="race-year-title">${label}</div>`;

                const grid = document.createElement('div');
                grid.className = 'race-time-grid';

                const slots = getYearSlots(yi);
                slots.forEach((slot, si) => {
                    const cell = document.createElement('div');
                    cell.className = 'race-time-cell';

                    const slotIds = slot.races.flatMap(r => raceKeys(r));
                    const selectedInSlot = state.selectedRaces.filter(id => slotIds.includes(id));
                    const mainRaceId = selectedInSlot[0];
                    const selected = slot.races.find(r => raceKeys(r).includes(mainRaceId));

                    let html = `<div class="race-time-label">${slot.period}</div>`;
                    if (selected) {
                        html += `
                            <div class="race-cell-selected-img">
                                <img src="/races/${encodeURIComponent(selected.name)}.png" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">
                                <div class="race-image-fallback" style="display:none">${selected.type}</div>
                                <span class="race-cell-selected-grade badge-${selected.type.toLowerCase().replace('-', '')}">${selected.type}</span>
                            </div>
                            <div class="race-cell-selected-name">${escapeHtml(selected.name)}</div>
                        `;
                    } else {
                        html += `<div class="race-time-plus">+</div>`;
                    }

                    cell.innerHTML = html;
                    cell.onclick = () => openSlotPopup(slot, yi);
                    grid.appendChild(cell);
                });

                block.appendChild(grid);
                els.raceOptionsContent.appendChild(block);
            });
        }

        function openSlotPopup(slot, yearIdx) {
            const yearLabels = ['Junior Year', 'Classic Year', 'Senior Year'];
            els.racePopupTitle.textContent = `${yearLabels[yearIdx]} - ${slot.period}`;
            els.racePopupBody.innerHTML = '';

            if (slot.races.length === 0) {
                els.racePopupBody.innerHTML = '<div class="race-slot-popup-empty">No races available</div>';
            } else {
                const list = document.createElement('div');
                list.className = 'race-slot-popup-list';

                const slotIds = slot.races.flatMap(r => raceKeys(r));

                slot.races.forEach(race => {
                    const myIds = raceKeys(race);
                    const selectedInSlot = state.selectedRaces.filter(id => slotIds.includes(id));
                    const selIndex = selectedInSlot.findIndex(id => myIds.includes(id));
                    const isSelected = selIndex !== -1;

                    let badgeHtml = '<div class="race-slot-popup-check">✓</div>';
                    if (isSelected && state.scenarioType === "Mant" && selectedInSlot.length > 0) {
                        if (selIndex === 0) {
                            badgeHtml = '<div class="race-slot-popup-check main-race" style="font-size: 0.7rem; font-weight: bold; width: auto; padding: 0 8px; border-radius: 12px; background: rgba(255,255,255,0.2);">MAIN</div>';
                        } else {
                            badgeHtml = `<div class="race-slot-popup-check overwrite-race" style="font-size: 0.7rem; font-weight: bold; width: auto; padding: 0 8px; border-radius: 12px; background: rgba(255,255,255,0.1);">RIVAL OVERWRITE ${selIndex}</div>`;
                        }
                    }

                    const item = document.createElement('div');
                    item.className = `race-slot-popup-item ${isSelected ? 'on' : ''}`;
                    item.innerHTML = `
                        <div class="race-slot-popup-img">
                            <img src="/races/${encodeURIComponent(race.name)}.png" onerror="this.src='/broom.png'">
                        </div>
                        <div class="race-slot-popup-info">
                            <div class="race-slot-popup-name-row">
                                <span class="race-slot-popup-grade badge-${race.type.toLowerCase().replace('-', '')}">${race.type}</span>
                                <span class="race-slot-popup-name">${escapeHtml(race.name)}</span>
                            </div>
                            <div class="race-slot-popup-meta">
                                <span class="race-slot-popup-terrain ${race.terrain.toLowerCase()}">${race.terrain}</span>
                                <span class="race-slot-popup-distance">${race.distance}</span>
                            </div>
                        </div>
                        ${badgeHtml}
                    `;
                    item.onclick = async () => {
                        const isMant = state.scenarioType === "Mant";

                        if (isSelected) {
                            state.selectedRaces = state.selectedRaces.filter(id => !myIds.includes(id));
                        } else {
                            if (!isMant) {
                                state.selectedRaces = state.selectedRaces.filter(id => !slotIds.includes(id));
                            }
                            state.selectedRaces.push(parseInt(race.id));
                        }

                        openSlotPopup(slot, yearIdx);
                        renderRaces();
                        await autoSaveRaces();
                    };
                    list.appendChild(item);
                });
                els.racePopupBody.appendChild(list);
            }
            els.racePopupOverlay.style.display = 'flex';
        }

        async function autoSaveRaces() {
            try {
                const current = getCurrentPreset();
                if (current) current.extra_race_list = [...state.selectedRaces];
                await apiJson('/api/presets/save_races', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        preset_name: state.selectedPreset,
                        races: state.selectedRaces
                    })
                });
            } catch (e) {}
        }

        function getTurnFromDate(dateStr) {
            const match = dateStr.match(/(\d+)年(\d+)月(前|後)半/);
            if (!match) return 0;
            const year = parseInt(match[1]);
            const month = parseInt(match[2]);
            const half = match[3] === '前' ? 0 : 1;
            return (year - 1) * 24 + (month - 1) * 2 + half + 1;
        }

        function bindRaceHandlers() {
            els.racePopupClose?.addEventListener('click', () => {
                els.racePopupOverlay.style.display = 'none';
            });
            els.racePopupOverlay?.addEventListener('click', (e) => {
                if (e.target === els.racePopupOverlay) els.racePopupOverlay.style.display = 'none';
            });

            makeSectionToggle('race-toggle', 'race-chevron', 'race-body', false);
        }

        let skillDataCache = null;
        let activeEditTier = null;
        let activeSkillFilter = null;
        let activeColorFilter = null;

        const SKILL_FILTERS = [
            { id: 101, label: 'Front' },
            { id: 102, label: 'Pace' },
            { id: 103, label: 'Late' },
            { id: 104, label: 'End' },
            { id: 201, label: 'Short' },
            { id: 202, label: 'Mile' },
            { id: 203, label: 'Medium' },
            { id: 204, label: 'Long' },
            { id: 502, label: 'Dirt' },
            { id: 'turf', label: 'Turf' }
        ];

        const COLOR_FILTERS = [
            { id: 'green', label: 'Green', color: '#4ade80', iconPrefixes: ['1001', '1002', '1003', '1004', '1005', '1006'] },
            { id: 'blue', label: 'Blue', color: '#60a5fa', iconPrefixes: ['2002'] },
            { id: 'yellow', label: 'Yellow', color: '#fbbf24', iconPrefixes: ['2001', '2004', '2005', '2006', '2009'] },
            { id: 'red', label: 'Red', color: '#f87171', iconPrefixes: ['3001', '3002', '3004', '3005', '3007'] }
        ];

        async function loadSkillData() {
            if (skillDataCache) return skillDataCache;
            try {
                const res = await apiJson('/api/skills');
                if (res.success && res.skills) {
                    const uniqueMap = new Map();
                    Object.entries(res.skills).forEach(([id, s]) => {
                        if (!uniqueMap.has(s.name)) {
                            uniqueMap.set(s.name, { id, ...s, tags: new Set(s.tags || []) });
                        } else {
                            const existing = uniqueMap.get(s.name);
                            if (s.rarity > existing.rarity) existing.rarity = s.rarity;
                            (s.tags || []).forEach(t => existing.tags.add(t));
                        }
                    });
                    skillDataCache = Array.from(uniqueMap.values()).map(s => ({ ...s, tags: Array.from(s.tags) }));
                    skillDataCache.sort((a, b) => a.name.localeCompare(b.name));
                    return skillDataCache;
                }
            } catch (e) {}
            return [];
        }

        function renderSkillFilters() {
            const container = document.getElementById('skill-filters');
            if (!container) return;
            
            let html = '<div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 4px;">';
            for (const filter of SKILL_FILTERS) {
                const isActive = activeSkillFilter === filter.id;
                const bg = isActive ? 'rgba(var(--accent-primary-rgb), 0.2)' : 'rgba(255,255,255,0.05)';
                const border = isActive ? 'var(--accent-primary)' : 'transparent';
                const color = isActive ? 'var(--text-main)' : '#a1a1aa';
                html += `<div class="skill-filter-chip affinity-filter" data-id="${filter.id}" style="padding: 0.35rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; cursor: pointer; background: ${bg}; border: 1px solid ${border}; color: ${color}; font-weight: bold; transition: all 0.1s;">${filter.label}</div>`;
            }
            html += '</div><div style="display: flex; flex-wrap: wrap; gap: 4px;">';
            
            for (const filter of COLOR_FILTERS) {
                const isActive = activeColorFilter === filter.id;
                const bg = isActive ? `${filter.color}33` : 'rgba(255,255,255,0.05)';
                const border = isActive ? filter.color : 'transparent';
                const color = isActive ? 'var(--text-main)' : filter.color;
                html += `<div class="skill-filter-chip color-filter" data-color="${filter.id}" style="padding: 0.35rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; cursor: pointer; background: ${bg}; border: 1px solid ${border}; color: ${color}; font-weight: bold; transition: all 0.1s;">${filter.label}</div>`;
            }
            html += '</div>';
            
            container.innerHTML = html;
            
            container.querySelectorAll('.affinity-filter').forEach(el => {
                el.addEventListener('click', () => {
                    let tagId = el.getAttribute('data-id');
                    if (tagId !== 'turf') tagId = Number(tagId);
                    
                    if (activeSkillFilter === tagId) activeSkillFilter = null;
                    else activeSkillFilter = tagId;
                    
                    renderSkillFilters();
                    renderSkillList();
                });
            });

            container.querySelectorAll('.color-filter').forEach(el => {
                el.addEventListener('click', () => {
                    const colorId = el.getAttribute('data-color');
                    
                    if (activeColorFilter === colorId) activeColorFilter = null;
                    else activeColorFilter = colorId;
                    
                    renderSkillFilters();
                    renderSkillList();
                });
            });
        }

        function renderSkillList() {
            const query = (els.skillSearch?.value || '').toLowerCase();
            const skills = skillDataCache || [];
            
            let count = 0;
            let html = '';
            for (const s of skills) {
                if (query && !s.name.toLowerCase().includes(query)) continue;
                
                if (activeSkillFilter !== null) {
                    const skillTags = s.tags || [];
                    if (activeSkillFilter === 'turf') {
                        if (skillTags.includes(502)) continue;
                    } else {
                        if (!skillTags.includes(activeSkillFilter)) continue;
                    }
                }
                
                if (activeColorFilter !== null) {
                    const iconId = String(s.icon_id || '');
                    const colorFilter = COLOR_FILTERS.find(filter => filter.id === activeColorFilter);
                    const skillColor = colorFilter && colorFilter.iconPrefixes.some(prefix => iconId.startsWith(prefix)) ? activeColorFilter : 'none';
                    
                    if (skillColor !== activeColorFilter) continue;
                }
                
                count++;
                
                html += `<div class="skill-list-item" data-name="${escapeAttr(s.name)}" style="padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: background 0.1s;">
                    <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-main); font-size: 0.85rem;">${escapeHtml(s.name)}</span>
                </div>`;
            }
            
            if (els.skillList) {
                if (count === 0) {
                    els.skillList.innerHTML = `<div style="padding: 1rem; color: #a1a1aa; font-size: 0.85rem;">No skills found.</div>`;
                } else {
                    els.skillList.innerHTML = html;
                    els.skillList.querySelectorAll('.skill-list-item').forEach(el => {
                        el.addEventListener('click', () => {
                            const name = el.getAttribute('data-name');
                            addSkillToFocusedArea(name);
                        });
                        el.addEventListener('mouseenter', () => el.style.background = 'rgba(255,255,255,0.1)');
                        el.addEventListener('mouseleave', () => el.style.background = 'rgba(255,255,255,0.03)');
                    });
                }
            }
        }

        function renderSkillEditorRightSide() {
            const current = getCurrentPreset();
            if (!current) {
                if (els.skillTiersContainer) els.skillTiersContainer.innerHTML = '';
                if (els.skillBlacklistContainer) els.skillBlacklistContainer.innerHTML = '';
                return;
            }

            let tiersHtml = '';
            const storedTiers = current.learn_skill_list || [];
            const tiers = storedTiers.length > 0 ? storedTiers : [[]];
            tiers.forEach((tier, i) => {
                const isActive = activeEditTier === i;
                const itemsHtml = tier.map(s =>
                    `<div class="skill-tag">
                        ${escapeHtml(s)} <span class="skill-tag-del" data-tier="${i}" data-skill="${escapeAttr(s)}">&times;</span>
                    </div>`
                ).join('');

                tiersHtml += `
                <div class="skill-tier-dropzone ${isActive ? 'is-active' : ''}" data-tier="${i}">
                    <div class="skill-tier-header">
                        <span class="skill-tier-label">TIER ${i+1}</span>
                        <button class="btn btn-sm btn-danger-soft skill-editor-action tier-del-btn" data-tier="${i}">DEL</button>
                    </div>
                    <div class="skill-tag-list">
                        ${itemsHtml}
                    </div>
                </div>`;
            });
            if (els.skillTiersContainer) els.skillTiersContainer.innerHTML = tiersHtml;

            if (els.skillBlacklistContainer) {
                const isBlActive = activeEditTier === null;
                els.skillBlacklistContainer.classList.toggle('is-active', isBlActive);

                const blacklist = current.learn_skill_blacklist || [];
                els.skillBlacklistContainer.innerHTML = blacklist.map(s =>
                    `<div class="skill-tag blacklist">
                        ${escapeHtml(s)} <span class="skill-tag-del" data-blacklist="true" data-skill="${escapeAttr(s)}">&times;</span>
                    </div>`
                ).join('');
            }

            els.skillTiersContainer?.querySelectorAll('.skill-tier-dropzone').forEach(el => {
                el.addEventListener('click', (e) => {
                    if (e.target.classList.contains('tier-del-btn') || e.target.classList.contains('skill-tag-del')) return;
                    activeEditTier = parseInt(el.getAttribute('data-tier'));
                    renderSkillEditorRightSide();
                });
            });
            if (els.skillBlacklistContainer) {
                els.skillBlacklistContainer.onclick = (e) => {
                    if (e.target.classList.contains('skill-tag-del')) return;
                    activeEditTier = null;
                    renderSkillEditorRightSide();
                };
            }

            els.skillTiersContainer?.querySelectorAll('.tier-del-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const idx = parseInt(btn.getAttribute('data-tier'));
                    current.learn_skill_list = current.learn_skill_list || [];
                    current.learn_skill_list.splice(idx, 1);
                    if (activeEditTier === idx) activeEditTier = null;
                    else if (activeEditTier > idx) activeEditTier--;
                    await savePresetConfig();
                    renderSkillEditorRightSide();
                });
            });

            document.querySelectorAll('.skill-tag-del').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const skillName = btn.getAttribute('data-skill');
                    if (btn.hasAttribute('data-blacklist')) {
                        current.learn_skill_blacklist = current.learn_skill_blacklist.filter(s => s !== skillName);
                    } else {
                        const tierIdx = parseInt(btn.getAttribute('data-tier'));
                        current.learn_skill_list[tierIdx] = current.learn_skill_list[tierIdx].filter(s => s !== skillName);
                    }
                    await savePresetConfig();
                    renderSkillEditorRightSide();
                });
            });
        }

        async function addSkillToFocusedArea(name) {
            const current = getCurrentPreset();
            if (!current) return;

            if (activeEditTier === null) {
                if (!current.learn_skill_blacklist) current.learn_skill_blacklist = [];
                if (!current.learn_skill_blacklist.includes(name)) {
                    current.learn_skill_blacklist.push(name);
                }
            } else {
                if (!current.learn_skill_list) current.learn_skill_list = [];
                if (!current.learn_skill_list[activeEditTier]) current.learn_skill_list[activeEditTier] = [];
                if (!current.learn_skill_list[activeEditTier].includes(name)) {
                    current.learn_skill_list[activeEditTier].push(name);
                }
            }
            await savePresetConfig();
            renderSkillEditorRightSide();
        }

        function initSkillEditor() {
            if (!state.selectedPreset) return;
            activeEditTier = 0;

            els.skillModal.style.display = 'flex';
            if (els.skillSearch) els.skillSearch.value = '';
            activeSkillFilter = null;
            activeColorFilter = null;

            loadSkillData().then(() => {
                renderSkillFilters();
                renderSkillList();
            });
            renderSkillEditorRightSide();
        }

        const STAT_KEYS_ORDERED = ['speed', 'stamina', 'power', 'guts', 'wit'];
        const STAT_MIN_DEFAULT = [0, 0, 0, 0, 0];
        const STAT_MAX_DEFAULT = [1200, 1200, 1200, 1200, 1200];

        function readStatInputs(inputs) {
            return STAT_KEYS_ORDERED.map(k => {
                const raw = inputs[k]?.value;
                const n = parseInt(raw);
                return Number.isFinite(n) ? Math.max(0, Math.min(1200, n)) : 0;
            });
        }

        function writeStatInputs(inputs, values, defaults) {
            const arr = Array.isArray(values) ? values : defaults;
            STAT_KEYS_ORDERED.forEach((k, idx) => {
                const el = inputs[k];
                if (!el) return;
                const fallback = defaults[idx] ?? 0;
                const v = Number.isFinite(arr[idx]) ? arr[idx] : fallback;
                el.value = v;
            });
        }

        async function savePresetConfig() {
            if (!state.selectedPreset || !state.presets) return;
            const current = getCurrentPreset();
            if (!current) return;

            current.learn_skill_threshold = parseInt(els.presetSkillThreshold.value) || 888;
            current.running_style = parseInt(els.presetRunningStyle?.value) || 1;
            current.min_stats = readStatInputs(els.presetMinStats);
            current.max_stats = readStatInputs(els.presetMaxStats);

            try {
                await apiJson('/api/presets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ preset: current })
                });
            } catch (e) {}
        }

        function populatePresetUI() {
            if (!state.selectedPreset || !state.presets) return;
            const current = getCurrentPreset();
            if (!current) return;

            els.presetSkillThreshold.value = current.learn_skill_threshold || 888;
            if (els.presetRunningStyle) els.presetRunningStyle.value = current.running_style || 1;
            writeStatInputs(els.presetMinStats, current.min_stats, STAT_MIN_DEFAULT);
            writeStatInputs(els.presetMaxStats, current.max_stats, STAT_MAX_DEFAULT);
            clearUmaMoePreview();
        }

        const STYLE_NAMES = { 1: 'Front Runner', 2: 'Pace Chaser', 3: 'Late Surger', 4: 'End Closer' };

        function clearUmaMoePreview() {
            state.umaMoePendingPatch = null;
            if (els.umaMoePreview) {
                els.umaMoePreview.style.display = 'none';
                els.umaMoePreview.innerHTML = '';
            }
            if (els.umaMoeImportBtn) els.umaMoeImportBtn.disabled = true;
            setUmaMoeStatus('', '');
        }

        function setUmaMoeStatus(text, kind = '') {
            if (!els.umaMoeStatus) return;
            els.umaMoeStatus.textContent = text || '';
            els.umaMoeStatus.classList.remove('is-error', 'is-ok');
            if (kind === 'error') els.umaMoeStatus.classList.add('is-error');
            else if (kind === 'ok') els.umaMoeStatus.classList.add('is-ok');
        }

        function normalizeTrainerId(raw) {
            return String(raw || '').replace(/\D+/g, '').trim();
        }
        function normalizeFriendId(raw) {
            return String(raw || '').replace(/\D+/g, '').trim();
        }
        function renderFriendPreview(html = '') {
            if (!els.friendPreviewPanel) return;
            els.friendPreviewPanel.innerHTML = html;
            els.friendPreviewPanel.style.display = html ? '' : 'none';
        }
        async function previewFriendId() {
            const viewerId = normalizeFriendId(els.friendIdInput?.value);
            if (!viewerId) {
                renderFriendPreview('<div class="friend-preview-error">Enter a numeric friend/trainer id first.</div>');
                return;
            }
            const local = ((dashData && dashData.friends) || []).find(friend => String(friend.viewer_id) === viewerId);
            if (local) {
                renderFriendPreview(`
                    <div class="friend-preview-card">
                        <img src="/api/images/${escapeAttr(String(local.support_card_id || '10001'))}.png" onerror="hideBrokenImage(this)">
                        <div>
                            <div class="friend-preview-title">${escapeHtml(local.name || `Trainer ${viewerId}`)}</div>
                            <div class="friend-preview-meta">${escapeHtml(viewerId)} · ${escapeHtml(friendStateLabel(local.friend_state))}</div>
                            <div class="friend-preview-meta">${escapeHtml(local.support_name || 'Unknown support')} · ${escapeHtml(local.type || '?')} LB${local.limit_break_count ?? '?'}</div>
                        </div>
                    </div>
                `);
                return;
            }
            renderFriendPreview('<div class="friend-preview-loading">Looking up public uma.moe trainer profile...</div>');
            try {
                const res = await apiJson(`/api/uma-moe/trainer/${encodeURIComponent(viewerId)}`);
                if (!res.success) throw new Error(res.detail || 'Preview failed');
                const patch = res.patch || {};
                const support = patch.friend_support || {};
                renderFriendPreview(`
                    <div class="friend-preview-card">
                        <img src="/api/images/${escapeAttr(String(patch.trainee_card_id || support.support_card_id || '100101'))}.png" onerror="hideBrokenImage(this)">
                        <div>
                            <div class="friend-preview-title">${escapeHtml(patch.imported_trainer_name || `Trainer ${viewerId}`)}</div>
                            <div class="friend-preview-meta">${escapeHtml(viewerId)} · uma.moe public profile</div>
                            <div class="friend-preview-meta">${escapeHtml(patch.trainee_name || 'Unknown trainee')} · ${escapeHtml(STYLE_NAMES[patch.running_style] || '?')}</div>
                            <div class="friend-preview-meta">Shared support: ${escapeHtml(support.name || 'unknown')}</div>
                        </div>
                    </div>
                `);
            } catch (e) {
                renderFriendPreview(`<div class="friend-preview-error">No loaded friend/public preview found for ${escapeHtml(viewerId)}. You can still try FOLLOW.</div>`);
            }
        }
        async function followFriendId() {
            const viewerId = Number(normalizeFriendId(els.friendIdInput?.value) || 0);
            if (!viewerId) {
                renderFriendPreview('<div class="friend-preview-error">Enter a numeric friend/trainer id first.</div>');
                return;
            }
            await manageFollow('follow', viewerId);
        }

        function renderUmaMoePreview(patch) {
            if (!els.umaMoePreview) return;
            const races = patch.extra_race_preview || [];
            const factors = patch.learn_skill_preview || [];
            const skillTier = (patch.learn_skill_list && patch.learn_skill_list[0]) || [];
            const stars = patch.blue_stars_per_stat || [0,0,0,0,0];
            const support = patch.friend_support || {};
            const knownRaces = races.filter(r => r.known).length;
            const unknownRaces = races.length - knownRaces;

            const raceTagsHtml = races.map(r => {
                const label = r.name ? escapeHtml(r.name) : `p${r.program_id}`;
                const cls = r.known ? 'uma-moe-preview-tag' : 'uma-moe-preview-tag is-warn';
                return `<span class="${cls}" title="uma.moe id ${r.uma_moe_id} -> program ${r.program_id}">${label}</span>`;
            }).join('');

            const skillTagsHtml = skillTier.map(name => `<span class="uma-moe-preview-tag">${escapeHtml(name)}</span>`).join('');

            const warnings = [];
            if ((patch.extra_race_pruned_count || 0) > 0) {
                warnings.push(`${patch.extra_race_pruned_count} lower-priority imported race(s) were pruned to keep the route near UG training budget.`);
            }
            if ((patch.extra_race_unmatched_count || 0) > 0) {
                warnings.push(`${patch.extra_race_unmatched_count} race(s) could not be matched to local race_map.`);
            }
            if (unknownRaces > 0) warnings.push(`${unknownRaces} race(s) could not be matched to local race_map.`);
            const skillCount = factors.filter(f => f.category === 'skill' || f.category === 'unique').length;
            if (skillCount > skillTier.length) warnings.push(`${skillCount - skillTier.length} factor(s) had no name in factor_map.`);

            els.umaMoePreview.innerHTML = `
                <dl class="uma-moe-preview-grid">
                    <dt>Trainer</dt><dd>${escapeHtml(patch.imported_trainer_name || '?')} <span style="opacity:.55">(${escapeHtml(patch.imported_from_trainer_id || '')})</span></dd>
                    <dt>Trainee</dt><dd>${escapeHtml(patch.trainee_name || '?')} <span style="opacity:.55">card ${patch.trainee_card_id || '?'}</span></dd>
                    <dt>Style</dt><dd>${escapeHtml(STYLE_NAMES[patch.running_style] || '?')}</dd>
                    <dt>Friend</dt><dd>${escapeHtml(support.name || (patch.friend_card_id ? '(unknown card ' + patch.friend_card_id + ')' : 'n/a'))} ${support.type ? `<span style="opacity:.55">${escapeHtml(support.type)} LB${support.limit_break_count ?? 0}</span>` : ''}</dd>
                    <dt>Stars</dt><dd>SPD ${stars[0]||0} / STA ${stars[1]||0} / PWR ${stars[2]||0} / GUT ${stars[3]||0} / WIT ${stars[4]||0} <span style="opacity:.55">(blue ${patch.blue_stars_total||0}, white ${patch.white_stars_total||0})</span></dd>
                    <dt>Races</dt><dd><span style="opacity:.65">${races.length}${patch.extra_race_original_count ? ` kept from ${patch.extra_race_original_count}` : ''}</span><div class="uma-moe-preview-tags">${raceTagsHtml || '<span style="opacity:.55">none</span>'}</div></dd>
                    <dt>Skills</dt><dd><div class="uma-moe-preview-tags">${skillTagsHtml || '<span style="opacity:.55">none</span>'}</div></dd>
                </dl>
                ${warnings.length ? `<div class="uma-moe-preview-warning">${warnings.map(escapeHtml).join(' &middot; ')}</div>` : ''}
            `;
            els.umaMoePreview.style.display = 'flex';
        }

        async function umaMoePreviewTrainer() {
            const tid = normalizeTrainerId(els.umaMoeTrainerId?.value);
            if (!tid) {
                setUmaMoeStatus('Enter a numeric trainer id.', 'error');
                return;
            }
            setUmaMoeStatus('Fetching from uma.moe...', '');
            if (els.umaMoeImportBtn) els.umaMoeImportBtn.disabled = true;
            try {
                const res = await apiJson(`/api/uma-moe/trainer/${encodeURIComponent(tid)}`);
                if (!res.success) throw new Error(res.detail || 'Fetch failed');
                state.umaMoePendingPatch = res.patch || null;
                renderUmaMoePreview(res.patch || {});
                setUmaMoeStatus('Preview ready. IMPORT creates a new preset by default; runtime tuning stays in scripts.', 'ok');
                if (els.umaMoeImportBtn) els.umaMoeImportBtn.disabled = false;
            } catch (e) {
                state.umaMoePendingPatch = null;
                clearUmaMoePreview();
                setUmaMoeStatus(e?.message || String(e), 'error');
            }
        }

        async function umaMoeImportTrainer() {
            const tid = normalizeTrainerId(els.umaMoeTrainerId?.value);
            if (!tid) {
                setUmaMoeStatus('Enter a numeric trainer id.', 'error');
                return;
            }
            const suggestedName = state.umaMoePendingPatch?.imported_trainer_name
                ? `uma.moe ${state.umaMoePendingPatch.imported_trainer_name} ${Date.now()}`
                : `uma.moe ${tid} ${Date.now()}`;
            const targetName = prompt('Create new preset name for this imported reference plan:', suggestedName);
            if (!targetName || !targetName.trim()) {
                setUmaMoeStatus('Import cancelled.', '');
                return;
            }
            setUmaMoeStatus('Importing...', '');
            try {
                const res = await apiJson('/api/uma-moe/import', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        trainer_id: tid,
                        preset_name: targetName.trim(),
                        create_only: true,
                        overwrite_races: true,
                        overwrite_skills: true,
                        overwrite_running_style: true,
                        overwrite_supports: true,
                        overwrite_trainee: true,
                    }),
                });
                if (!res.success) throw new Error(res.detail || 'Import failed');
                setUmaMoeStatus(`Imported into preset '${res.preset?.name || targetName}'.`, 'ok');
                state.selectedPreset = res.preset?.name || targetName.trim();
                localStorage.setItem('uma_selected_preset', state.selectedPreset);
                persistSelectedPresetToCache(state.selectedPreset);
                await loadPresets();
                if (els.presetSelect) els.presetSelect.value = state.selectedPreset;
                syncSelectedPresetRaces();
                populatePresetUI();
                renderRaces();
                clearUmaMoePreview();
                setUmaMoeStatus(`Imported into preset '${state.selectedPreset}'.`, 'ok');
            } catch (e) {
                setUmaMoeStatus(e?.message || String(e), 'error');
            }
        }

        const UMA_MOE_STYLE_PILL_CLASS = {
            1: 'uma-moe-style-front',
            2: 'uma-moe-style-pace',
            3: 'uma-moe-style-late',
            4: 'uma-moe-style-end',
        };

        function numericSortValue(...values) {
            for (const value of values) {
                if (value === null || value === undefined || value === '') continue;
                const parsed = Number(String(value).replace(/,/g, ''));
                if (Number.isFinite(parsed)) return parsed;
            }
            return 0;
        }

        function umaMoeSortValue(result, key) {
            if (key === 'g1') return numericSortValue(result.g1_win_count);
            if (key === 'date') {
                const ts = Date.parse(result.last_updated || '');
                return Number.isFinite(ts) ? ts : 0;
            }
            return numericSortValue(
                result.score,
                result.parent_score,
                result.parent_rank,
                result.rank_score,
                result.affinity_score
            );
        }

        function sortedUmaMoeResults(results) {
            const key = state.umaMoeSortKey || 'score';
            const dir = state.umaMoeSortDir === 'asc' ? 1 : -1;
            return [...(results || [])].sort((a, b) => {
                const av = umaMoeSortValue(a, key);
                const bv = umaMoeSortValue(b, key);
                if (av !== bv) return (av - bv) * dir;
                return numericSortValue(b.score, b.parent_rank, b.rank_score, b.affinity_score) -
                    numericSortValue(a.score, a.parent_rank, a.rank_score, a.affinity_score);
            });
        }

        function syncUmaMoeSortControls() {
            (els.umaMoeSortBtns || []).forEach(btn => {
                btn.classList.toggle('is-active', btn.dataset.sortKey === state.umaMoeSortKey);
            });
            if (els.umaMoeSortDirBtn) {
                els.umaMoeSortDirBtn.dataset.sortDir = state.umaMoeSortDir;
                els.umaMoeSortDirBtn.textContent = state.umaMoeSortDir === 'asc' ? 'ASC' : 'DESC';
            }
        }

        function setUmaMoeSearchStatus(text, kind = '') {
            if (!els.umaMoeSearchStatus) return;
            els.umaMoeSearchStatus.textContent = text || '';
            els.umaMoeSearchStatus.classList.remove('is-error', 'is-ok');
            if (kind === 'error') els.umaMoeSearchStatus.classList.add('is-error');
            else if (kind === 'ok') els.umaMoeSearchStatus.classList.add('is-ok');
        }

        async function loadUmaMoeCharaPicker() {
            if (state.umaMoeCharas) return state.umaMoeCharas;
            const sel = els.umaMoeSearchChara;
            try {
                const res = await apiJson('/api/uma-moe/charas');
                const charas = (res && res.charas) || {};
                state.umaMoeCharas = charas;
                if (!sel) return charas;
                const entries = Object.entries(charas)
                    .filter(([id, name]) => id && name)
                    .sort((a, b) => String(a[1]).localeCompare(String(b[1])));
                const fragments = ['<option value="">— pick a uma —</option>'];
                for (const [id, name] of entries) {
                    fragments.push(`<option value="${escapeAttr(id)}">${escapeHtml(name)}</option>`);
                }
                sel.innerHTML = fragments.join('');
                return charas;
            } catch (e) {
                setUmaMoeSearchStatus(`Failed to load chara list: ${e?.message || e}`, 'error');
                return {};
            }
        }

        function renderUmaMoeSearchResults(results, total, charaName) {
            if (!els.umaMoeSearchResults) return;
            syncUmaMoeSortControls();
            const sortedResults = sortedUmaMoeResults(results);
            if (!results || results.length === 0) {
                els.umaMoeSearchResults.innerHTML = '<div class="uma-moe-search-empty">No trainers found for this uma yet.</div>';
                els.umaMoeSearchResults.style.display = 'block';
                return;
            }
            const totalLabel = typeof total === 'string' ? total : formatNumber(total || sortedResults.length);
            const items = sortedResults.map(r => {
                const tid = escapeAttr(r.trainer_id || '');
                const name = escapeHtml(r.trainer_name || '(no name)');
                const trainee = escapeHtml(r.trainee_name || (r.main_parent_id ? `card ${r.main_parent_id}` : '?'));
                const stars = r.blue_stars_per_stat || [0, 0, 0, 0, 0];
                const styleLabel = r.running_style ? escapeHtml(r.running_style_name || `style ${r.running_style}`) : '—';
                const styleClass = UMA_MOE_STYLE_PILL_CLASS[r.running_style] || '';
                const support = r.support_card_name ? escapeHtml(r.support_card_name) : '—';
                const supportLb = r.support_card_id ? `LB${r.support_limit_break_count || 0}` : '';
                const followers = Number(r.follower_num || 0);
                const rank = r.parent_rank ? formatNumber(r.parent_rank) : '—';
                const affinity = r.affinity_score ? formatNumber(r.affinity_score) : '—';
                const portraitId = r.main_parent_id || '';
                const updatedTs = Date.parse(r.last_updated || '');
                const updatedAt = Number.isFinite(updatedTs) ? new Date(updatedTs).toLocaleDateString() : '—';
                return `
                <div class="uma-moe-search-result" data-trainer-id="${tid}" tabindex="0" role="button">
                    <div class="uma-moe-search-result-portrait" style="background-image: url('/api/images/${escapeAttr(String(portraitId))}.png')"></div>
                    <div class="uma-moe-search-result-body">
                        <div class="uma-moe-search-result-top">
                            <div class="uma-moe-search-result-name">${name}</div>
                            <div class="uma-moe-search-result-tid">${tid}</div>
                        </div>
                        <div class="uma-moe-search-result-mid">
                            <span class="uma-moe-search-result-trainee">${trainee}</span>
                            <span class="uma-moe-search-result-pill ${styleClass}">${styleLabel}</span>
                        </div>
                        <div class="uma-moe-search-result-stats">
                            <span title="Affinity score">A&nbsp;${affinity}</span>
                            <span title="Parent rank">R&nbsp;${rank}</span>
                            <span title="Win count">W&nbsp;${r.win_count || 0}</span>
                            <span title="G1 win count">G1&nbsp;${r.g1_win_count || 0}</span>
                            <span title="uma.moe followers">F&nbsp;${followers.toLocaleString()}</span>
                            <span title="Career/update date">D&nbsp;${escapeHtml(updatedAt)}</span>
                            <span title="Blue / Pink / White star totals">★&nbsp;${r.blue_stars_sum || 0}/${r.pink_stars_sum || 0}/${r.white_stars_sum || 0}</span>
                        </div>
                        <div class="uma-moe-search-result-blue" title="Blue stars per stat">
                            <span>SPD&nbsp;${stars[0] || 0}</span>
                            <span>STA&nbsp;${stars[1] || 0}</span>
                            <span>PWR&nbsp;${stars[2] || 0}</span>
                            <span>GUT&nbsp;${stars[3] || 0}</span>
                            <span>WIT&nbsp;${stars[4] || 0}</span>
                        </div>
                        <div class="uma-moe-search-result-support">${support}${supportLb ? ` <span class="uma-moe-search-result-lb">${supportLb}</span>` : ''}</div>
                    </div>
                </div>`;
            }).join('');
            const headerName = charaName ? ` for <strong>${escapeHtml(charaName)}</strong>` : '';
            const sortLabel = state.umaMoeSortKey === 'g1' ? 'G1 wins' : state.umaMoeSortKey === 'date' ? 'career date' : 'score';
            els.umaMoeSearchResults.innerHTML = `
                <div class="uma-moe-search-results-head">${sortedResults.length} of ${escapeHtml(String(totalLabel))} trainers${headerName} · sorted by ${escapeHtml(sortLabel)} ${state.umaMoeSortDir} · click one to preview &amp; import</div>
                <div class="uma-moe-search-results-list">${items}</div>
            `;
            els.umaMoeSearchResults.style.display = 'block';
            els.umaMoeSearchResults.querySelectorAll('.uma-moe-search-result').forEach(card => {
                const pick = () => {
                    const tid = card.getAttribute('data-trainer-id') || '';
                    if (!tid) return;
                    els.umaMoeSearchResults.querySelectorAll('.uma-moe-search-result.is-active').forEach(el => el.classList.remove('is-active'));
                    card.classList.add('is-active');
                    if (els.umaMoeTrainerId) els.umaMoeTrainerId.value = tid;
                    umaMoePreviewTrainer();
                };
                card.addEventListener('click', pick);
                card.addEventListener('keydown', ev => {
                    if (ev.key === 'Enter' || ev.key === ' ') {
                        ev.preventDefault();
                        pick();
                    }
                });
            });
        }

        async function umaMoeSearchByChara() {
            const charaId = els.umaMoeSearchChara?.value || '';
            if (!charaId) {
                setUmaMoeSearchStatus('Pick a uma first.', 'error');
                return;
            }
            const charaName = (state.umaMoeCharas || {})[charaId] || charaId;
            setUmaMoeSearchStatus(`Searching uma.moe for ${charaName}...`, '');
            if (els.umaMoeSearchBtn) els.umaMoeSearchBtn.disabled = true;
            try {
                const res = await apiJson(`/api/uma-moe/search?chara_id=${encodeURIComponent(charaId)}&limit=15`);
                if (!res.success) throw new Error(res.detail || 'Search failed');
                const resultsList = res.results || [];
                state.umaMoeSearchResults = resultsList;
                state.umaMoeSearchTotal = res.total;
                state.umaMoeSearchCharaName = res.chara_name || charaName;
                renderUmaMoeSearchResults(state.umaMoeSearchResults, state.umaMoeSearchTotal, state.umaMoeSearchCharaName);
                const totalLabel = typeof res.total === 'string' ? res.total : formatNumber(res.total || resultsList.length);
                if (resultsList.length === 0) {
                    setUmaMoeSearchStatus(`No public uma.moe records for ${charaName} yet.`, '');
                } else {
                    setUmaMoeSearchStatus(`${resultsList.length} of ${totalLabel} trainers shown.`, 'ok');
                }
            } catch (e) {
                setUmaMoeSearchStatus(e?.message || String(e), 'error');
                if (els.umaMoeSearchResults) {
                    els.umaMoeSearchResults.style.display = 'none';
                    els.umaMoeSearchResults.innerHTML = '';
                }
            } finally {
                if (els.umaMoeSearchBtn) els.umaMoeSearchBtn.disabled = !els.umaMoeSearchChara?.value;
            }
        }

        function bindPresetHandlers() {
            if (els.presetSelect) {
                els.presetSelect.addEventListener('change', async (e) => {
                    state.selectedPreset = e.target.value;
                    localStorage.setItem('uma_selected_preset', state.selectedPreset);
                    persistSelectedPresetToCache(state.selectedPreset);
                    syncSelectedPresetRaces();
                    populatePresetUI();
                    renderRaces();
                    applyPresetRentalSelection();
                    updateAdvisorRecommendations();
                });
            }

            const saveHandler = () => {
                savePresetConfig();
                updateAdvisorRecommendations();
            };
            els.presetSkillThreshold?.addEventListener('change', saveHandler);
            els.presetRunningStyle?.addEventListener('change', saveHandler);
            Object.values(els.presetMinStats || {}).forEach(el => el?.addEventListener('change', saveHandler));
            Object.values(els.presetMaxStats || {}).forEach(el => el?.addEventListener('change', saveHandler));

            els.umaMoePreviewBtn?.addEventListener('click', () => umaMoePreviewTrainer());
            els.umaMoeImportBtn?.addEventListener('click', () => umaMoeImportTrainer());
            els.umaMoeTrainerId?.addEventListener('input', () => {
                if (els.umaMoeImportBtn) els.umaMoeImportBtn.disabled = true;
                clearUmaMoePreview();
            });
            els.umaMoeTrainerId?.addEventListener('keydown', e => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    umaMoePreviewTrainer();
                }
            });

            if (els.umaMoeSearchChara) {
                loadUmaMoeCharaPicker();
                els.umaMoeSearchChara.addEventListener('change', () => {
                    if (els.umaMoeSearchBtn) els.umaMoeSearchBtn.disabled = !els.umaMoeSearchChara.value;
                });
            }
            els.umaMoeSearchBtn?.addEventListener('click', () => umaMoeSearchByChara());
            (els.umaMoeSortBtns || []).forEach(btn => {
                btn.addEventListener('click', () => {
                    state.umaMoeSortKey = btn.dataset.sortKey || 'score';
                    renderUmaMoeSearchResults(state.umaMoeSearchResults, state.umaMoeSearchTotal, state.umaMoeSearchCharaName);
                });
            });
            els.umaMoeSortDirBtn?.addEventListener('click', () => {
                state.umaMoeSortDir = state.umaMoeSortDir === 'asc' ? 'desc' : 'asc';
                renderUmaMoeSearchResults(state.umaMoeSearchResults, state.umaMoeSearchTotal, state.umaMoeSearchCharaName);
            });

            els.presetEditSkillsBtn?.addEventListener('click', () => {
                if (!state.selectedPreset) return;
                activeEditTier = 0;

                els.skillModal.style.display = 'flex';
                if (els.skillSearch) els.skillSearch.value = '';
                activeSkillFilter = null;

                loadSkillData().then(() => {
                    renderSkillFilters();
                    renderSkillList();
                });
                renderSkillEditorRightSide();
            });
            els.skillModalClose?.addEventListener('click', () => { els.skillModal.style.display = 'none'; });

            els.skillSearch?.addEventListener('input', renderSkillList);

            els.skillAddTierBtn?.addEventListener('click', async () => {
                const current = getCurrentPreset();
                if (!current) return;
                if (!current.learn_skill_list) current.learn_skill_list = [];
                current.learn_skill_list.push([]);
                activeEditTier = current.learn_skill_list.length - 1;
                await savePresetConfig();
                renderSkillEditorRightSide();
            });

            document.getElementById('skill-select-all-btn')?.addEventListener('click', async () => {
                const current = getCurrentPreset();
                if (!current) return;
                const visibleNodes = els.skillList?.querySelectorAll('.skill-list-item') || [];
                let changed = false;

                visibleNodes.forEach(node => {
                    const name = node.getAttribute('data-name');
                    if (activeEditTier === null) {
                        if (!current.learn_skill_blacklist) current.learn_skill_blacklist = [];
                        if (!current.learn_skill_blacklist.includes(name)) {
                            current.learn_skill_blacklist.push(name);
                            changed = true;
                        }
                    } else {
                        if (!current.learn_skill_list) current.learn_skill_list = [];
                        if (!current.learn_skill_list[activeEditTier]) current.learn_skill_list[activeEditTier] = [];
                        if (!current.learn_skill_list[activeEditTier].includes(name)) {
                            current.learn_skill_list[activeEditTier].push(name);
                            changed = true;
                        }
                    }
                });
                if (changed) {
                    await savePresetConfig();
                    renderSkillEditorRightSide();
                }
            });

            document.getElementById('skill-deselect-all-btn')?.addEventListener('click', async () => {
                const current = getCurrentPreset();
                if (!current) return;
                const visibleNodes = els.skillList?.querySelectorAll('.skill-list-item') || [];
                let changed = false;

                const namesToRemove = Array.from(visibleNodes).map(node => node.getAttribute('data-name'));

                if (activeEditTier === null) {
                    if (current.learn_skill_blacklist) {
                        const originalLen = current.learn_skill_blacklist.length;
                        current.learn_skill_blacklist = current.learn_skill_blacklist.filter(s => !namesToRemove.includes(s));
                        if (current.learn_skill_blacklist.length !== originalLen) changed = true;
                    }
                } else {
                    if (current.learn_skill_list && current.learn_skill_list[activeEditTier]) {
                        const originalLen = current.learn_skill_list[activeEditTier].length;
                        current.learn_skill_list[activeEditTier] = current.learn_skill_list[activeEditTier].filter(s => !namesToRemove.includes(s));
                        if (current.learn_skill_list[activeEditTier].length !== originalLen) changed = true;
                    }
                }

                if (changed) {
                    await savePresetConfig();
                    renderSkillEditorRightSide();
                }
            });

            document.getElementById('skill-blacklist-all-btn')?.addEventListener('click', async () => {
                const current = getCurrentPreset();
                if (!current) return;
                const visibleNodes = els.skillList?.querySelectorAll('.skill-list-item') || [];
                let changed = false;

                if (!current.learn_skill_blacklist) current.learn_skill_blacklist = [];
                visibleNodes.forEach(node => {
                    const name = node.getAttribute('data-name');
                    if (!current.learn_skill_blacklist.includes(name)) {
                        current.learn_skill_blacklist.push(name);
                        changed = true;
                    }
                });

                if (changed) {
                    await savePresetConfig();
                    renderSkillEditorRightSide();
                }
            });
            document.getElementById('skill-clear-blacklist-btn')?.addEventListener('click', async () => {
                const current = getCurrentPreset();
                if (!current) return;
                if (current.learn_skill_blacklist && current.learn_skill_blacklist.length > 0) {
                    current.learn_skill_blacklist = [];
                    await savePresetConfig();
                    renderSkillEditorRightSide();
                }
            });

            els.presetAddBtn?.addEventListener('click', async () => {
                const newName = prompt("Enter new preset name:");
                if (!newName || !newName.trim()) return;
                const normalizedName = normalizePresetName(newName);
                if (!normalizedName) {
                    alert("Preset name cannot be empty.");
                    return;
                }
                if (presetNameExists(normalizedName)) {
                    alert("A preset with that name already exists.");
                    return;
                }

                const newPreset = {
                    name: normalizedName,
                    running_style: 1,
                    learn_skill_list: [],
                    learn_skill_blacklist: [],
                    extra_race_list: [],
                    learn_skill_threshold: 888
                };

                try {
                    const res = await apiJson('/api/presets', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ preset: newPreset })
                    });
                    if (!res.success || !res.preset?.name) {
                        alert(res.detail || "Failed to save new preset.");
                        return;
                    }
                    state.selectedPreset = res.preset.name;
                    localStorage.setItem('uma_selected_preset', state.selectedPreset);
                    persistSelectedPresetToCache(state.selectedPreset);
                    await loadPresets();
                    if (els.presetSelect) els.presetSelect.value = state.selectedPreset;
                    syncSelectedPresetRaces();
                    populatePresetUI();
                    renderRaces();
                } catch (e) { alert("Failed to save new preset."); }
            });

            els.presetDelBtn?.addEventListener('click', async () => {
                if (!state.selectedPreset) return;
                const deletedName = state.selectedPreset;
                if (!confirm(`Are you sure you want to delete preset '${deletedName}'?`)) return;

                try {
                    const res = await apiJson('/api/presets/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: deletedName })
                    });
                    if (!res.success) {
                        alert(res.detail || "Failed to delete preset.");
                        return;
                    }
                    await loadPresets();
                } catch (e) { alert("Failed to delete preset."); }
            });
        }

        async function loadPresets() {
            try {
                const res = await apiJson('/api/presets');
                if (res.success && res.presets && res.presets.length > 0) {
                    state.presets = res.presets;
                    if (els.presetSelect) {
                        els.presetSelect.innerHTML = state.presets.map(p => `<option value="${escapeAttr(p.name)}">${escapeHtml(p.name)}</option>`).join('');
                    }
                    const saved = localStorage.getItem('uma_selected_preset');
                    const cached = state.lastSessionCache && state.lastSessionCache.selected_preset;
                    if (saved && state.presets.some(p => p.name === saved)) {
                        state.selectedPreset = saved;
                    } else if (cached && state.presets.some(p => p.name === cached)) {
                        state.selectedPreset = cached;
                    } else {
                        state.selectedPreset = state.presets[0].name;
                    }
                    localStorage.setItem('uma_selected_preset', state.selectedPreset);
                    persistSelectedPresetToCache(state.selectedPreset);
                    if (els.presetSelect) els.presetSelect.value = state.selectedPreset;
                    populatePresetUI();
                } else {
                    state.presets = [];
                    state.selectedPreset = "";
                    localStorage.removeItem('uma_selected_preset');
                    if (els.presetSelect) els.presetSelect.innerHTML = "";
                    populatePresetUI();
                }
            } catch(e) {
                state.presets = [];
                state.selectedPreset = "";
                localStorage.removeItem('uma_selected_preset');
                populatePresetUI();
            }
            syncStartButton();
            await loadRaceData();
        }

        function renderFriends() {
            const friends = (dashData && dashData.friends) || [];
            clearInvalidFriendSelection();
            const visibleFriends = getVisibleFriends();
            if (dashData) dashData.visibleFriends = visibleFriends;

            if (state.pendingFriendSelection) {
                const f = visibleFriends.find(v =>
                    String(v.viewer_id) === state.pendingFriendSelection.viewer_id &&
                    String(v.support_card_id) === state.pendingFriendSelection.support_card_id
                );
                if (f) {
                    selection.friend = f;
                    state.pendingFriendSelection = null;
                }
            }

            els.friendCount.innerText = `(${visibleFriends.length}/${friends.length})`;
            els.friendGrid.innerHTML = visibleFriends.map(friend => {
                const imgId = friend.support_card_id || '10001';
                const lb = friend.limit_break_count ?? '?';
                const relation = friendStateLabel(friend.friend_state);
                const canUnfollow = Number(friend.friend_state || 0) > 0;
                return `<div class="grid-card friend-card">
                    <img src="/api/images/${imgId}.png" onerror="hideBrokenImage(this)">
                    <span class="relationship-badge">${escapeHtml(relation)}</span>
                    <button class="friend-follow-btn friend-follow-top" type="button" data-action="${canUnfollow ? 'unfollow' : 'follow'}" data-viewer-id="${escapeAttr(String(friend.viewer_id || ''))}">
                        ${canUnfollow ? 'UNFOLLOW' : 'FOLLOW'}
                    </button>
                    <div class="grid-card-overlay">
                        <span class="grid-card-name">${friend.support_name || 'Unknown'}</span>
                        <span class="grid-card-kicker">${friend.type || '?'} | LB${lb}</span>
                    </div>
                </div>`;
            }).filter(Boolean).join('');
            attachFriendHandlers();
            syncFriendSelection();
            renderFriendManageList();
            renderTeamPanel();
        }
        function appendSeenFriendIds(ids) {
            if (!dashData) return;
            const seen = new Set(dashData.friendExcludeIds || []);
            (ids || []).forEach(id => {
                if (id) seen.add(id);
            });
            dashData.friendExcludeIds = Array.from(seen);
        }
        async function loadFriends(refresh = false) {
            if (!dashData || state.isFetchingFriends) return;
            const isCareerActive = dashData.account && dashData.account.career && dashData.account.career.active;
            if (isCareerActive) {
                els.friendRefreshBtn.disabled = true;
                els.friendStatus.classList.remove('error');
                els.friendStatus.innerText = 'Active career, endpoint blocked';
                return;
            }
            state.isFetchingFriends = true;
            els.friendRefreshBtn.disabled = true;
            els.friendStatus.classList.remove('error');
            els.friendStatus.innerText = refresh ? 'Refreshing friends...' : 'Loading friends...';
            const excludeIds = [];
            try {
                const data = await apiJson('/api/career/friends', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ exclude_viewer_ids: excludeIds, force_refresh: !!refresh })
                });
                if (!data.success) throw new Error(data.detail || 'Friend load failed');
                dashData.friends = data.friends || [];
                appendSeenFriendIds(data.exclude_viewer_ids || []);
                renderFriends();
                if (data.warning && els.friendStatus) {
                    els.friendStatus.innerText = `Using cached friends; refresh failed: ${data.warning}`;
                    els.friendStatus.classList.add('error');
                    return;
                }
                if (data.source === 'Active Career (Skip)') {
                    els.friendStatus.innerText = 'Active career, endpoint blocked';
                    return;
                }
                const source = data.source === 'initial' ? 'initial' : 'refresh';
                const visibleCount = ((dashData && dashData.visibleFriends) || []).length;
                els.friendStatus.innerText = `${source} list: ${visibleCount}/${dashData.friends.length} cards`;
            } catch (e) {
                els.friendStatus.innerText = e.message || 'Friend load failed';
                els.friendStatus.classList.add('error');
            } finally {
                state.isFetchingFriends = false;
                const stillActive = dashData.account && dashData.account.career && dashData.account.career.active;
                els.friendRefreshBtn.disabled = !!stillActive;
            }
        }
        function attachFriendHandlers() {
            const visibleFriends = (dashData && dashData.visibleFriends) || [];
            document.querySelectorAll('#friend-grid .friend-follow-btn').forEach(btn => {
                btn.addEventListener('click', ev => {
                    ev.preventDefault();
                    ev.stopPropagation();
                    manageFollow(btn.dataset.action, Number(btn.dataset.viewerId || 0));
                });
            });
            document.querySelectorAll('#friend-grid .grid-card').forEach((el, i) => {
                el.classList.add('selectable');
                el.addEventListener('click', () => {
                    const friend = visibleFriends[i];
                    const already = selection.friend && friendKey(selection.friend) === friendKey(friend);
                    document.querySelectorAll('#friend-grid .grid-card').forEach(c => c.classList.remove('selected'));
                    selection.friend = already ? null : friend;
                    if (!already) el.classList.add('selected');
                    renderTeamPanel();
                });
            });
        }

        async function manageFollow(action, viewerId) {
            if (!viewerId || state.isManagingFollow) return;
            state.isManagingFollow = true;
            if (els.friendManageStatus) {
                els.friendManageStatus.classList.remove('error');
                els.friendManageStatus.innerText = `${action === 'unfollow' ? 'Unfollowing' : 'Following'} ${viewerId}...`;
            }
            try {
                const res = await apiJson(`/api/friends/${action === 'unfollow' ? 'unfollow' : 'follow'}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ viewer_id: viewerId })
                });
                if (!res.success) throw new Error(res.detail || 'Follow action failed');
                if (els.friendManageStatus) els.friendManageStatus.innerText = 'Relationship updated. Refreshing...';
                await loadFriends(true);
                await loadFriendVeterans(true);
            } catch (e) {
                if (els.friendManageStatus) {
                    els.friendManageStatus.innerText = e?.message || String(e);
                    els.friendManageStatus.classList.add('error');
                }
            } finally {
                state.isManagingFollow = false;
            }
        }

        function vetKey(vet) {
            if (!vet) return '';
            return `${vet.viewer_id}:${vet.trained_chara_id}`;
        }
        // Game rank ids -> letter (matches the chip the game itself draws on a
        // veteran card). Anything > 13 = EX-tier (UG/UF/UE/UD/UC/UB/UA/US).
        const VET_RANK_LABELS = {
            1: 'G',   2: 'G+',
            3: 'F',   4: 'F+',
            5: 'E',   6: 'E+',
            7: 'D',   8: 'D+',
            9: 'C',  10: 'C+',
           11: 'B',  12: 'B+',
           13: 'A',  14: 'A+',
           15: 'S',  16: 'S+',
           17: 'SS', 18: 'SS+',
           19: 'UG', 20: 'UG+',
           21: 'UF', 22: 'UF+',
           23: 'UE', 24: 'UE+',
           25: 'UD', 26: 'UD+',
           27: 'UC', 28: 'UC+',
           29: 'UB', 30: 'UB+',
           31: 'UA', 32: 'UA+',
           33: 'US', 34: 'US+',
        };
        const VET_SCENARIO_NAMES = {
            1: 'URA',
            2: 'Aoharu',
            3: "Make a New Track",
            4: 'Trailblazer',
            5: "Grand Live",
            6: 'Grand Masters',
            7: 'L\'Arc',
            8: "UAF Ready Go",
            9: 'Daily',
           10: 'Pretty Derby',
           11: 'Mecha Umamusume',
        };
        function rankLabel(rankId) {
            if (!rankId) return '';
            return VET_RANK_LABELS[rankId] || `R${rankId}`;
        }
        function rankTier(rankId) {
            // Used for CSS color coding: low (G..D+), mid (C..A+), high (S..SS+),
            // ex (UG and above).
            if (!rankId) return 'unk';
            if (rankId <= 8) return 'low';
            if (rankId <= 14) return 'mid';
            if (rankId <= 18) return 'high';
            return 'ex';
        }
        function statTier(value) {
            const v = Number(value) || 0;
            if (v >= 1200) return 'blue3';   // ★3 blue factor
            if (v >= 1100) return 'blue2';   // ★2
            if (v >= 600)  return 'blue1';   // ★1
            return 'white';
        }
        function renderVetStats(v) {
            const cells = [
                ['SPD', v.speed],
                ['STA', v.stamina],
                ['PWR', v.power],
                ['GUT', v.guts],
                ['WIT', v.wiz],
            ];
            return cells.map(([label, raw]) => {
                const tier = statTier(raw);
                return `<span class="vet-stat vet-stat-${tier}">
                    <span class="vet-stat-label">${label}</span>
                    <span class="vet-stat-value">${Number(raw) || 0}</span>
                </span>`;
            }).join('');
        }
        function renderVetFactors(factors, max = 5) {
            const items = (factors || [])
                .filter(f => f && (f.category === 'stat' || f.category === 'aptitude' ||
                                   f.category === 'unique' || f.category === 'skill'))
                .slice(0, max);
            if (!items.length) return '';
            return `<div class="vet-factors">${items.map(f => {
                const stars = '★'.repeat(Math.min(3, Math.max(0, Number(f.stars) || 0)));
                return `<span class="vet-factor vet-factor-${escapeAttr(f.category)}" title="${escapeAttr(f.name)} ${stars}">
                    ${escapeHtml(f.name)}<span class="vet-factor-stars">${stars}</span>
                </span>`;
            }).join('')}</div>`;
        }
        function renderVetParents(parentCardIds) {
            const ids = (parentCardIds || []).filter(Boolean);
            if (!ids.length) return '';
            return `<div class="vet-parents" title="Direct parents">${ids.map(cid => `
                <img class="vet-parent-portrait" src="/api/images/${cid}.png" onerror="hideBrokenImage(this)" alt="${cid}">
            `).join('')}</div>`;
        }
        function renderFriendVeterans() {
            if (!els.friendVetGrid) return;
            scanUniqueFactors();
            const vets = (dashData && dashData.friendVeterans) || [];
            
            const query = (state.filters.friendVets.query || '').toLowerCase().trim();
            const minRank = state.filters.friendVets.rank;
            const criteria = state.filters.friendVets.criteria;
            
            const filteredVets = vets.filter(v => {
                if (query) {
                    const cName = String(v.chara_name || '').toLowerCase();
                    const tName = String(v.trainer_name || '').toLowerCase();
                    if (!cName.includes(query) && !tName.includes(query)) return false;
                }
                if (minRank !== 'all') {
                    const rankVal = Number(v.rank || 0);
                    if (minRank === 'UG' && rankVal < 19) return false;
                    if (minRank === 'SS' && rankVal < 18) return false;
                    if (minRank === 'S' && rankVal < 17) return false;
                    if (minRank === 'A+' && rankVal < 16) return false;
                }
                for (const criterion of criteria) {
                    if (!criterion.name) continue;
                    let totalStars = 0;
                    if (v.factors) {
                        v.factors.forEach(f => {
                            if (f && f.name === criterion.name) {
                                totalStars += Number(f.stars || 0);
                            }
                        });
                    }
                    if (totalStars < criterion.minStars) return false;
                }
                return true;
            });
            
            if (els.friendVetCount) els.friendVetCount.innerText = `(${filteredVets.length}/${vets.length})`;
            els.friendVetGrid.innerHTML = filteredVets.map(v => {
                const imgId = v.card_id || 100101;
                const rank = rankLabel(v.rank);
                const tier = rankTier(v.rank);
                const scenario = VET_SCENARIO_NAMES[v.scenario_id] || '';
                const style = STYLE_NAMES[v.running_style] || '';
                const score = Number(v.rank_score) || 0;
                const deckLabel = v.deck_archetype ? `Deck: ${v.deck_archetype}` : '';
                return `<div class="grid-card friend-card friend-vet-card vet-tier-${tier}" data-vet-key="${vetKey(v)}">
                    <img src="/api/images/${imgId}.png" onerror="hideBrokenImage(this)">
                    ${rank ? `<span class="rank-badge vet-rank-${tier}">${escapeHtml(rank)}</span>` : ''}
                    ${renderVetParents(v.parent_card_ids)}
                    <div class="grid-card-overlay vet-overlay">
                        <div class="vet-stats">${renderVetStats(v)}</div>
                        ${renderVetFactors(v.factors)}
                        ${renderSupportDeckStrip(v.deck_support_cards || v.deck_support_ids, 'support-deck-strip vet-deck-strip')}
                        <span class="grid-card-name">${escapeHtml(v.chara_name || 'Unknown')}</span>
                        <span class="grid-card-kicker">
                            ${escapeHtml(v.trainer_name || '')}
                            ${scenario ? ` &middot; ${escapeHtml(scenario)}` : ''}
                            ${style ? ` &middot; ${escapeHtml(style)}` : ''}
                            ${score ? ` &middot; ${score.toLocaleString()}pt` : ''}
                            ${deckLabel ? ` &middot; ${escapeHtml(deckLabel)}` : ''}
                        </span>
                    </div>
                </div>`;
            }).join('');
            attachFriendVeteranHandlers(filteredVets);
            syncFriendVeteranSelection();
            renderTeamPanel();
            updateAdvisorRecommendations();
        }
        function syncFriendVeteranSelection() {
            const selected = selection.rentalParent;
            const key = selected ? vetKey(selected) : '';
            document.querySelectorAll('#friend-vet-grid .grid-card').forEach(el => {
                el.classList.toggle('selected', el.dataset.vetKey === key);
            });
        }
        function attachFriendVeteranHandlers(filteredVets) {
            const vets = filteredVets || (dashData && dashData.friendVeterans) || [];
            document.querySelectorAll('#friend-vet-grid .grid-card').forEach((el, i) => {
                el.classList.add('selectable');
                el.addEventListener('click', () => {
                    const vet = vets[i];
                    if (!vet) return;
                    const already = selection.rentalParent && vetKey(selection.rentalParent) === vetKey(vet);
                    selection.rentalParent = already ? null : vet;
                    syncFriendVeteranSelection();
                    syncSelectionToServer();
                    savePresetRentalChara();
                    renderTeamPanel();
                    updateAdvisorRecommendations();
                });
            });
        }
        async function savePresetRentalChara() {
            // Keep rental parent choice in the active UI/server selection only.
            // Runtime career tuning now reads the start request instead of
            // mutating preset JSON for every parent experiment.
            const v = selection.rentalParent;
            selection.rentalParent = v || null;
            await syncSelectionToServer();
        }
        async function loadFriendVeterans(refresh = false) {
            if (!dashData || state.isFetchingFriendVeterans) return;
            const isCareerActive = dashData.account && dashData.account.career && dashData.account.career.active;
            if (isCareerActive) {
                if (els.friendVetRefreshBtn) els.friendVetRefreshBtn.disabled = true;
                if (els.friendVetStatus) {
                    els.friendVetStatus.classList.remove('error');
                    els.friendVetStatus.innerText = 'Active career, endpoint blocked';
                }
                return;
            }
            state.isFetchingFriendVeterans = true;
            if (els.friendVetRefreshBtn) els.friendVetRefreshBtn.disabled = true;
            if (els.friendVetStatus) {
                els.friendVetStatus.classList.remove('error');
                els.friendVetStatus.innerText = refresh ? 'Refreshing borrowable parents...' : 'Loading borrowable parents...';
            }
            try {
                // Reuse /api/career/friends which also populates the veterans cache.
                const data = await apiJson('/api/career/friends', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ exclude_viewer_ids: [], force_refresh: !!refresh })
                });
                if (!data.success) throw new Error(data.detail || 'Veteran load failed');
                dashData.friendVeterans = data.veterans || [];
                dashData.friendVeteransSource = data.veterans_source || 'unknown';
                if (els.friendVetStatus) {
                    if (data.veterans_source === 'no_data') {
                        els.friendVetStatus.innerText = 'No borrowable veterans surfaced by the game yet. Make sure you have friends with public veterans, then REFRESH.';
                    } else {
                        els.friendVetStatus.innerText = `Found ${dashData.friendVeterans.length} borrowable parent(s)`;
                    }
                }
                renderFriendVeterans();
                applyPresetRentalSelection();
                updateAdvisorRecommendations();
            } catch (e) {
                if (els.friendVetStatus) {
                    els.friendVetStatus.innerText = e.message || 'Veteran load failed';
                    els.friendVetStatus.classList.add('error');
                }
            } finally {
                state.isFetchingFriendVeterans = false;
                const stillActive = dashData.account && dashData.account.career && dashData.account.career.active;
                if (els.friendVetRefreshBtn) els.friendVetRefreshBtn.disabled = !!stillActive;
            }
        }
        function applyPresetRentalSelection() {
            // When a preset specifies a rental parent (e.g. from uma.moe), try
            // to find the matching loaded veteran and highlight it.
            //
            // Resolution order:
            //   1. exact (viewer_id, trained_chara_id) — set after the user
            //      clicked a veteran in this UI;
            //   2. (viewer_id, card_id hint) — for fresh uma.moe imports we
            //      only know the trainer + their published parent's card_id,
            //      so we pick that trainer's highest-rank veteran on that card;
            //   3. card_id hint alone — fall back to any friend running that
            //      card_id if the trainer is not in the friend list.
            const preset = getCurrentPreset();
            if (!preset) return;
            const vid = Number(preset.rental_chara_viewer_id || 0);
            const cid = Number(preset.rental_chara_id || 0);
            const cardHint = Number(preset.rental_chara_card_id || 0);
            if (!vid && !cid && !cardHint) {
                if (selection.rentalParent) {
                    selection.rentalParent = null;
                    syncFriendVeteranSelection();
                    renderTeamPanel();
                }
                return;
            }
            const vets = (dashData && dashData.friendVeterans) || [];

            let match = null;
            if (vid && cid) {
                match = vets.find(v => Number(v.viewer_id) === vid && Number(v.trained_chara_id) === cid) || null;
            }
            if (!match && vid && cardHint) {
                const ownerVets = vets
                    .filter(v => Number(v.viewer_id) === vid && Number(v.card_id) === cardHint)
                    .sort((a, b) => (Number(b.rank_score) || 0) - (Number(a.rank_score) || 0));
                match = ownerVets[0] || null;
            }
            if (!match && cardHint) {
                const cardVets = vets
                    .filter(v => Number(v.card_id) === cardHint)
                    .sort((a, b) => (Number(b.rank_score) || 0) - (Number(a.rank_score) || 0));
                match = cardVets[0] || null;
            }

            if (match) {
                selection.rentalParent = match;
                // Auto-persist the resolved trained_chara_id back into the preset
                // so subsequent loads pin to this exact veteran.
                if (Number(preset.rental_chara_id || 0) !== Number(match.trained_chara_id)) {
                    savePresetRentalChara();
                }
            } else if (vid && cid) {
                // Preset specifies a rental we don't have in the friend list (e.g.
                // imported from uma.moe but that trainer isn't an in-game friend).
                // Keep a stub so the start payload still sends the ids.
                selection.rentalParent = { viewer_id: vid, trained_chara_id: cid, chara_name: '(unloaded)', trainer_name: '(unloaded)' };
            } else {
                selection.rentalParent = null;
            }
            syncFriendVeteranSelection();
            renderTeamPanel();
        }
        async function startCareer() {
            const reason = getStartMissingReason();
            if (reason || state.isStartingCareer) {
                syncStartButton();
                return;
            }
            state.isStartingCareer = true;
            syncStartButton();
            let finalMessage = '';
            let finalIsError = false;
            const activeCareer = state.account && state.account.career && state.account.career.active;
            const rentalParent = selection.rentalParent || null;
            const boost = resolveEventBoostForStart();
            const body = activeCareer ? {
                preset_name: state.selectedPreset,
                max_steps: 2500,
                burn_clocks: state.burnClocks,
                dev_mode: state.devEnabled
            } : {
                card_id: Number(selection.trainee.id),
                support_card_ids: selection.deck.cards.map(card => Number(card.id)),
                friend_viewer_id: Number(selection.friend.viewer_id),
                friend_card_id: Number(selection.friend.support_card_id),
                parent_id_1: Number(selection.veterans[0].instance_id),
                parent_id_2: selection.veterans[1] ? Number(selection.veterans[1].instance_id) : (rentalParent ? Number(rentalParent.trained_chara_id) : 0),
                rental_viewer_id: rentalParent ? Number(rentalParent.viewer_id) : 0,
                rental_chara_id: rentalParent ? Number(rentalParent.trained_chara_id) : 0,
                deck_id: Number(selection.deck.deck_id || selection.deck.id) || 1,
                scenario_id: 4,
                use_tp: boost.useTp,
                difficulty_id: 0,
                difficulty: 0,
                is_boost: boost.isBoost,
                boost_story_event_id: boost.storyEventId,
                preset_name: state.selectedPreset,
                max_steps: 2500,
                burn_clocks: state.burnClocks,
                dev_mode: state.devEnabled
            };
            try {
                const data = await apiJson('/api/career/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                if (!data.success) throw new Error(data.detail || 'Start failed');
                state.displayedClocksUsed = Number(data.runner && data.runner.clocks_used || 0);
                renderAccountStrip(data.account);
                if (data.account && data.account.career && data.account.career.active) {
                    autoLoadCareerSelection();
                    renderFriends();
                }
                startRunnerPolling();
                const advisor = data.runtime_advisor || {};
                const archetype = advisor.deck_archetype ? ` (${advisor.deck_archetype})` : '';
                finalMessage = `Career runner started${archetype}`;
            } catch (e) {
                finalMessage = e.message || 'Start failed';
                finalIsError = true;
                if (state.devEnabled) {
                    setDevEnabled(false, { persist: true });
                }
            } finally {
                state.isStartingCareer = false;
                syncStartButton();
                if (finalMessage) {
                    els.startStatus.innerText = finalMessage;
                    els.startStatus.classList.toggle('error', finalIsError);
                }
            }
        }
        function applyRunnerSettings(runner) {
            if (runner.running && runner.burn_clocks !== undefined && state.burnClocks !== runner.burn_clocks) {
                setBurnClocks(runner.burn_clocks, { persist: true });
            }
        }
        function applyRunnerClockUsage(runner) {
            const clocksUsed = Number(runner.clocks_used || 0);
            if (state.account && clocksUsed > state.displayedClocksUsed) {
                const delta = clocksUsed - state.displayedClocksUsed;
                state.account = {
                    ...state.account,
                    clocks: Math.max(0, Number(state.account.clocks || 0) - delta)
                };
                state.displayedClocksUsed = clocksUsed;
                renderAccountStrip(state.account);
            } else if (clocksUsed < state.displayedClocksUsed) {
                state.displayedClocksUsed = clocksUsed;
            }
        }
        function applyRunnerSnapshot(runner) {
            state.runner = runner;
            applyRunnerSettings(runner);
            applyRunnerClockUsage(runner);
        }
        async function refreshRunnerStatus() {
            try {
                const data = await apiJson('/api/career/runner');
                if (!data.success || !data.runner) return;
                const runner = data.runner;
                applyRunnerSnapshot(runner);

                const rows = (runner.action_history && runner.action_history.length) ? runner.action_history : deriveActionHistory(runner.log || []);
                if (rows.length) renderActionHistory(rows);
                if (runner.running) {
                    els.startStatus.classList.toggle('error', false);
                    if (!rows.length) els.startStatus.innerText = `Turn ${runner.turn || '?'} / ${runner.last_action || 'running'} / ${runner.steps || 0}`;
                    return;
                }
                if (state.runnerTimer && !state.devEnabled) {
                    bgClearTimer(state.runnerTimer);
                    state.runnerTimer = 0;
                }
                if (runner.last_error) {
                    els.startStatus.classList.toggle('error', true);
                    if (!rows.length) els.startStatus.innerText = runner.last_error;
                    if (state.devEnabled) {
                        state.consecutiveRunnerFails++;
                        if (state.consecutiveRunnerFails >= 3) {
                            if (!rows.length) els.startStatus.innerText = runner.last_error + " (Auto-retry disabled due to loop)";
                            setDevEnabled(false, { persist: true });
                        }
                    }
                } else if (state.devEnabled && runner.finished && !runner.last_error) {
                    state.consecutiveRunnerFails = 0;
                    els.startStatus.classList.toggle('error', false);
                    if (!rows.length) els.startStatus.innerText = `Career finished! Restarting...`;
                    if (state.account && state.account.career) state.account.career.active = false;
                    renderAccountStrip(state.account);
                } else if (runner.steps) {
                    els.startStatus.classList.toggle('error', false);
                    if (!rows.length) els.startStatus.innerText = `Runner stopped after ${runner.steps} steps`;
                    if (state.devEnabled) {
                        state.consecutiveRunnerFails++;
                        if (state.consecutiveRunnerFails >= 3) {
                            if (!rows.length) els.startStatus.innerText = `Runner stopped after ${runner.steps} steps (Auto-retry disabled due to loop)`;
                            setDevEnabled(false, { persist: true });
                        }
                    }
                }
            } catch (e) {}
        }
        function renderActionHistory(rows) {
            if (!els.startStatus) return;
            if (!rows.length) {
                els.startStatus.innerText = '';
                return;
            }
            const formatStatsDetail = row => {
                const stats = row.stats || {};
                if (!Object.keys(stats).length) return row.detail || '';
                return [
                    `HP ${stats.hp ?? 0}/${stats.max_hp ?? 100}`,
                    `MOOD ${stats.motivation ?? 0}`,
                    `SPD ${stats.speed ?? 0} STA ${stats.stamina ?? 0} PWR ${stats.power ?? 0} GUT ${stats.guts ?? 0} WIT ${stats.wit ?? 0} SP ${stats.skill_point ?? 0}`
                ].join(' | ');
            };
            const body = rows.map(row => `
                    <tr>
                        <td>${escapeHtml(row.turn)}</td>
                        <td><span class="action-pill action-pill-${escapeAttr(normalizeHistoryAction(row).action)}">${escapeHtml(normalizeHistoryAction(row).action)}</span></td>
                        <td>${escapeHtml(row.facility)}</td>
                        <td class="action-history-detail">${escapeHtml(formatStatsDetail(row))}</td>
                    </tr>
                `).join('');
            els.startStatus.innerHTML = `
                <div class="action-history-wrap">
                    <table class="action-history-table">
                        <thead>
                            <tr>
                                <th>TURN</th>
                                <th>ACTION</th>
                                <th>FACILITY</th>
                                <th>DETAIL</th>
                            </tr>
                        </thead>
                        <tbody>${body}</tbody>
                    </table>
                </div>
            `;
            const wrap = els.startStatus.querySelector('.action-history-wrap');
            if (wrap) wrap.scrollTop = wrap.scrollHeight;
        }
        function deriveActionHistory(log) {
            return log.filter(item => ['command', 'race', 'race_progress', 'finish', 'api_delay', 'turn_delay', 'complex_delay'].includes(item.action)).map(item => {
                const detail = String(item.detail || '');
                let action = item.action;
                let facility = '';
                if (action === 'command') {
                    if (detail.startsWith('training ')) {
                        action = 'train';
                        facility = detail.replace('training ', '');
                    } else if (detail.startsWith('rest ')) {
                        action = 'rest';
                        facility = detail.replace('rest ', '');
                        if (['301', '302', '303', '304', '305', '390'].includes(facility)) action = 'recreation';
                    } else if (detail.startsWith('challenge ')) {
                        action = 'rest';
                        facility = detail.replace('challenge ', '');
                    } else if (detail.startsWith('recreation ')) {
                        action = 'recreation';
                        facility = detail.replace('recreation ', '');
                    } else if (detail.startsWith('command 8:')) {
                        action = 'medic';
                    }
                } else if (action === 'race_progress') {
                    action = 'race';
                }
                return { turn: item.turn, action, facility, detail };
            });
        }
        function normalizeHistoryAction(row) {
            const facility = String(row.facility ?? '');
            if (row.action === 'rest' && ['301', '302', '303', '304', '305', '390'].includes(facility)) {
                return { ...row, action: 'recreation' };
            }
            return row;
        }
        const timerWorkerBlob = new Blob([`
            let activeTimers = {};
            self.onmessage = function(e) {
                const { action, id, ms } = e.data;
                if (action === 'setInterval') {
                    activeTimers[id] = setInterval(() => postMessage({ id }), ms);
                } else if (action === 'setTimeout') {
                    activeTimers[id] = setTimeout(() => {
                        postMessage({ id });
                        delete activeTimers[id];
                    }, ms);
                } else if (action === 'clear') {
                    clearInterval(activeTimers[id]);
                    clearTimeout(activeTimers[id]);
                    delete activeTimers[id];
                }
            };
        `], {type: 'application/javascript'});
        const timerWorker = new Worker(URL.createObjectURL(timerWorkerBlob));
        let nextTimerId = 1;
        const timerCallbacks = {};
        timerWorker.onmessage = function(e) {
            if (timerCallbacks[e.data.id]) timerCallbacks[e.data.id]();
        };
        function bgSetInterval(cb, ms) {
            const id = nextTimerId++;
            timerCallbacks[id] = cb;
            timerWorker.postMessage({ action: 'setInterval', id, ms });
            return id;
        }
        function bgSetTimeout(cb, ms) {
            const id = nextTimerId++;
            timerCallbacks[id] = () => { delete timerCallbacks[id]; cb(); };
            timerWorker.postMessage({ action: 'setTimeout', id, ms });
            return id;
        }
        function bgClearTimer(id) {
            delete timerCallbacks[id];
            timerWorker.postMessage({ action: 'clear', id });
        }
        function startRunnerPolling() {
            if (state.runnerTimer) bgClearTimer(state.runnerTimer);
            refreshRunnerStatus();
            state.runnerTimer = bgSetInterval(refreshRunnerStatus, 1500);
        }
        els.friendRefreshBtn.addEventListener('click', event => {
            event.stopPropagation();
            loadFriends(true);
            loadFriendVeterans(true);
        });
        if (els.friendVetRefreshBtn) {
            els.friendVetRefreshBtn.addEventListener('click', event => {
                event.stopPropagation();
                loadFriendVeterans(true);
            });
        }
        els.friendPreviewBtn?.addEventListener('click', event => {
            event.stopPropagation();
            previewFriendId();
        });
        els.friendFollowIdBtn?.addEventListener('click', event => {
            event.stopPropagation();
            followFriendId();
        });
        els.friendIdInput?.addEventListener('keydown', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                previewFriendId();
            }
        });
        if (els.deckEditorNewBtn) {
            els.deckEditorNewBtn.addEventListener('click', event => {
                event.stopPropagation();
                openDeckEditor();
            });
        }
        if (els.deckEditorSaveBtn) {
            els.deckEditorSaveBtn.addEventListener('click', event => {
                event.stopPropagation();
                saveDeckEditor();
            });
        }
        if (els.deckEditorName) {
            els.deckEditorName.addEventListener('input', () => {
                state.deckEditor.name = els.deckEditorName.value;
            });
        }
        els.startCareerBtn.addEventListener('click', startCareer);

        function selectDeck(index, element) {
            const alreadySelected = element.classList.contains('selected');
            document.querySelectorAll('.deck-container.selected').forEach(card => card.classList.remove('selected'));
            selection.deck = null;
            if (!alreadySelected) {
                element.classList.add('selected');
                selection.deck = dashData.validDecks[index];
            }
            renderFriends();
            renderTeamPanel();
            syncSelectionToServer();
            updateAdvisorRecommendations();
        }
        function selectTrainee(index, element) {
            const alreadySelected = element.classList.contains('selected');
            document.querySelectorAll('#uma-grid .grid-card.selected').forEach(card => card.classList.remove('selected'));
            selection.trainee = null;
            if (!alreadySelected) {
                element.classList.add('selected');
                selection.trainee = dashData.umas[index];
            }
            renderFriends();
            updateVetSelectability();
            renderTeamPanel();
            syncSelectionToServer();
            updateAdvisorRecommendations();
        }
        function selectParent(index, element) {
            if (element.classList.contains('vet-full')) return;
            if (element.classList.contains('selected')) {
                element.classList.remove('selected');
                selection.veterans = selection.veterans.filter(parent => parent._gridIdx !== index);
            } else if (selection.veterans.length < 2) {
                element.classList.add('selected');
                selection.veterans.push({ ...dashData.parents[index], _gridIdx: index });
            }
            updateVetSelectability();
            renderTeamPanel();
            syncSelectionToServer();
            updateAdvisorRecommendations();
        }
        function attachDeckHandlers() {
            document.querySelectorAll('.deck-container').forEach((element) => {
                const index = Number(element.dataset.originalIndex);
                if (isNaN(index) || index < 0) return;
                element.addEventListener('click', () => selectDeck(index, element));
            });
            document.querySelectorAll('.deck-edit-btn').forEach(btn => {
                btn.addEventListener('click', event => {
                    event.preventDefault();
                    event.stopPropagation();
                    const deck = (dashData.validDecks || []).find(item => String(item.id) === String(btn.dataset.deckId));
                    if (deck) openDeckEditor(deck);
                });
            });
        }

        function attachTraineeHandlers() {
            document.querySelectorAll('#uma-grid .grid-card').forEach((element) => {
                const index = Number(element.dataset.originalIndex);
                if (isNaN(index) || index < 0) return;
                element.classList.add('selectable');
                element.addEventListener('click', () => selectTrainee(index, element));
            });
        }

        function attachParentHandlers() {
            document.querySelectorAll('#parent-grid .grid-card').forEach((element) => {
                const index = Number(element.dataset.originalIndex);
                if (isNaN(index) || index < 0) return;
                element.classList.add('selectable');
                element.addEventListener('click', () => selectParent(index, element));
            });
        }

        function attachSelectionHandlers() {
            attachDeckHandlers();
            attachTraineeHandlers();
            attachParentHandlers();
        }
        function isValidDeck(deck) {
            return deck.cards.every(card => {
                const id = card.id || '';
                const name = card.name || '';
                return !id.includes('{') && !id.includes('-') && !name.includes('Unknown');
            });
        }
        function renderCounts(data) {
            // Handled dynamically per-render to support filtered states
        }
        function renderDecks(decks) {
            const query = (state.filters.decks.query || '').toLowerCase().trim();
            const filteredDecks = decks.filter(deck => {
                if (!query) return true;
                return String(deck.name || '').toLowerCase().includes(query);
            });

            els.deckList.innerHTML = filteredDecks.map(deck => {
                const originalIdx = (dashData.validDecks || []).indexOf(deck);
                const cards = deck.cards.map(card => {
                    const imgId = card.id || '10001';
                    return `<div class="grid-card deck-card">
                        <img src="/api/images/${imgId}.png" onerror="hideBrokenImage(this)">
                        <div class="grid-card-overlay">
                            <span class="grid-card-kicker">${card.type || '?'} | ${card.rarity || '?'}</span>
                            <span class="grid-card-name">${card.name || 'Unknown'}</span>
                        </div>
                    </div>`;
                }).join('');
                const localActions = deck.local ? `<button class="btn btn-sm deck-edit-btn" type="button" data-deck-id="${escapeAttr(deck.id)}">EDIT</button>` : '';
                return `<div class="deck-container" data-original-index="${originalIdx}">
                    <div class="deck-header">
                        <span>${escapeHtml(deck.name || 'Deck').toUpperCase()} ${deck.local ? '<span class="deck-local-badge">LOCAL</span>' : ''}</span>
                        <span style="font-size:0.85rem; opacity:0.8">${deck.local ? 'SWEEPY' : `SLOT ${deck.id}`} ${localActions}</span>
                    </div>
                    <div class="deck-cards">${cards}</div>
                </div>`;
            }).join('');
            attachDeckHandlers();
        }

        function supportById(id) {
            const sid = String(id || '');
            return ((dashData && dashData.supports) || []).find(card => String(card.id) === sid) || null;
        }

        function enrichDeckCard(card) {
            return supportById(card && card.id) || card || {};
        }

        function renderDeckEditor() {
            if (!els.deckEditorPanel) return;
            const editor = state.deckEditor;
            els.deckEditorPanel.style.display = editor.open ? '' : 'none';
            if (els.deckEditorName) els.deckEditorName.value = editor.name || '';
            if (els.deckEditorSaveBtn) els.deckEditorSaveBtn.disabled = !editor.open || editor.cards.length !== 5;
            if (!editor.open) return;
            const selectedIds = new Set(editor.cards.map(card => String(card.id)));
            document.querySelectorAll('#card-grid .grid-card').forEach(el => {
                el.classList.toggle('deck-pick-selected', selectedIds.has(String(el.dataset.cardId || '')));
            });
            const slots = Array.from({ length: 5 }, (_, idx) => {
                const card = editor.cards[idx];
                if (!card) {
                    return `<div class="deck-editor-slot deck-editor-slot-empty" data-slot="${idx}">Click owned cards to fill slot ${idx + 1}</div>`;
                }
                const imgId = card.id || '10001';
                return `<button class="deck-editor-slot" type="button" data-remove-card="${escapeAttr(card.id)}">
                    <img src="/api/images/${imgId}.png" onerror="hideBrokenImage(this)">
                    <span>${escapeHtml(card.name || `Card ${card.id}`)}</span>
                    <small>${escapeHtml(card.rarity || '?')} · ${escapeHtml(card.type || '?')} · LB${card.limit_break_count ?? '?'}</small>
                </button>`;
            }).join('');
            const inspect = editor.inspectCard || editor.cards[editor.cards.length - 1] || null;
            const inspector = inspect ? `
                <div class="deck-card-inspector">
                    <img src="/api/images/${inspect.id || '10001'}.png" onerror="hideBrokenImage(this)">
                    <div>
                        <div class="deck-inspector-title">${escapeHtml(inspect.name || `Card ${inspect.id}`)}</div>
                        <div class="deck-inspector-meta">${escapeHtml(inspect.rarity || '?')} · ${escapeHtml(inspect.type || '?')} · LB${inspect.limit_break_count ?? '?'} · EXP ${formatNumber(inspect.exp || 0)}</div>
                        <div class="deck-inspector-copy">Use owned cards here; the friend support remains selected in the Friend Supports section. Local decks save to <code>data/decks.json</code> and do not modify the game deck slot.</div>
                        <a class="deck-inspector-link" href="https://gametora.com/umamusume/supports/${encodeURIComponent(inspect.id || '')}" target="_blank" rel="noreferrer">Open reference</a>
                    </div>
                </div>
            ` : `<div class="deck-card-inspector deck-card-inspector-empty">Click a card in OWNED CARDS to inspect and add it.</div>`;
            els.deckEditorPanel.innerHTML = `
                <div class="deck-editor-help">Building ${editor.cards.length}/5 owned support cards. Click a selected slot to remove it.</div>
                <div class="deck-editor-slots">${slots}</div>
                ${inspector}
            `;
            els.deckEditorPanel.querySelectorAll('[data-remove-card]').forEach(btn => {
                btn.addEventListener('click', event => {
                    event.preventDefault();
                    const id = String(btn.dataset.removeCard || '');
                    editor.cards = editor.cards.filter(card => String(card.id) !== id);
                    renderDeckEditor();
                    renderSupports(dashData.supports || []);
                });
            });
        }

        function openDeckEditor(deck = null) {
            const cards = (deck && deck.cards ? deck.cards : []).map(enrichDeckCard).filter(card => card.id);
            state.deckEditor = {
                open: true,
                id: deck && deck.local ? String(deck.id || '') : `local_${Date.now()}`,
                name: deck ? deck.name || 'Sweepy Deck' : 'Sweepy Deck',
                cards,
                inspectCard: cards[0] || null
            };
            if (els.deckEditorStatus) {
                els.deckEditorStatus.innerText = 'Click owned cards below to add/remove. Save when 5 are selected.';
                els.deckEditorStatus.classList.remove('error');
            }
            renderDeckEditor();
            renderSupports(dashData.supports || []);
        }

        function toggleDeckEditorCard(card) {
            if (!state.deckEditor.open || !card) return;
            const id = String(card.id || '');
            state.deckEditor.inspectCard = card;
            const exists = state.deckEditor.cards.some(c => String(c.id) === id);
            if (exists) {
                state.deckEditor.cards = state.deckEditor.cards.filter(c => String(c.id) !== id);
            } else if (state.deckEditor.cards.length < 5) {
                state.deckEditor.cards.push(card);
            } else if (els.deckEditorStatus) {
                els.deckEditorStatus.innerText = 'Deck is full; remove a slot before adding another card.';
                els.deckEditorStatus.classList.add('error');
            }
            renderDeckEditor();
            renderSupports(dashData.supports || []);
        }

        async function saveDeckEditor() {
            if (!state.deckEditor.open || state.deckEditor.cards.length !== 5) return;
            if (els.deckEditorSaveBtn) els.deckEditorSaveBtn.disabled = true;
            if (els.deckEditorStatus) {
                els.deckEditorStatus.innerText = 'Saving deck...';
                els.deckEditorStatus.classList.remove('error');
            }
            try {
                const name = (els.deckEditorName && els.deckEditorName.value.trim()) || state.deckEditor.name || 'Sweepy Deck';
                const res = await apiJson('/api/local-decks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        id: state.deckEditor.id,
                        name,
                        support_card_ids: state.deckEditor.cards.map(card => Number(card.id)),
                        deck_id: 1
                    })
                });
                if (!res.success) throw new Error(res.detail || 'Deck save failed');
                const nonLocal = (dashData.decks || []).filter(deck => !deck.local);
                dashData.decks = nonLocal.concat((res.decks || []).map(deck => ({
                    ...deck,
                    cards: (deck.cards || []).map(enrichDeckCard)
                })));
                dashData.validDecks = dashData.decks.filter(isValidDeck);
                renderDecks(dashData.validDecks);
                attachDeckHandlers();
                if (els.deckEditorStatus) els.deckEditorStatus.innerText = 'Deck saved';
            } catch (e) {
                if (els.deckEditorStatus) {
                    els.deckEditorStatus.innerText = e.message || 'Deck save failed';
                    els.deckEditorStatus.classList.add('error');
                }
            } finally {
                renderDeckEditor();
            }
        }
        function renderFactors(factors) {
            const star = String.fromCharCode(9733);
            return factors.map(factor => `
                <div class="factor-badge f-${factor.category}">
                    ${factor.name} <span class="stars">${star.repeat(factor.stars)}</span>
                </div>
            `).join('');
        }
        function renderWins(wins) {
            if (!wins || !wins.total) return '<span class="spark-win-chip">Wins --</span>';
            return `
                <span class="spark-win-chip">G1 ${wins.g1 || 0}</span>
                <span class="spark-win-chip">G2 ${wins.g2 || 0}</span>
                <span class="spark-win-chip">G3 ${wins.g3 || 0}</span>
            `;
        }
        function renderParentSparks(parent, fallbackImgId) {
            const tree = parent.tree || {};
            return ['self', 'p1', 'p2'].map(key => {
                const node = tree[key];
                if (!node || !node.factors || node.factors.length === 0) return '';
                const nodeImg = node.card_id || fallbackImgId;
                const nodeClass = key === 'self' ? 'spark-node spark-node-self' : 'spark-node';
                return `<div class="${nodeClass}" style="--node-bg: url('/api/images/${nodeImg}.png')">
                    <div class="spark-node-header">
                        <img class="spark-node-portrait" src="/api/images/${nodeImg}.png" onerror="hideBrokenImage(this)">
                        <div class="spark-node-meta">
                            <div class="spark-node-title">${node.name || `Card ${node.card_id || '?'}`}</div>
                            <div class="spark-win-row">${renderWins(node.wins)}</div>
                        </div>
                    </div>
                    <div class="spark-factor-list">
                        ${renderFactors(node.factors)}
                    </div>
                </div>`;
            }).join('');
        }
        function renderParentTreeNode(node, role) {
            const cardId = Number(node && node.card_id) || 0;
            if (!cardId) {
                return `<div class="parent-tree-node parent-tree-node-empty" data-role="${role}">
                    <span class="parent-tree-placeholder">?</span>
                </div>`;
            }
            return `<div class="parent-tree-node" data-role="${role}">
                <img src="/api/images/${cardId}.png" onerror="hideBrokenImage(this)">
            </div>`;
        }
        const invCategoryMap = {
            blue: 'stat',
            pink: 'aptitude',
            green: 'unique',
            white: 'skill'
        };

        function scanUniqueFactors() {
            const factorSet = new Set();
            if (dashData && dashData.parents) {
                dashData.parents.forEach(parent => {
                    const tree = parent.tree || {};
                    ['self', 'p1', 'p2'].forEach(key => {
                        const node = tree[key];
                        if (node && node.factors) {
                            node.factors.forEach(f => {
                                if (f && f.name) {
                                    factorSet.add(JSON.stringify({ name: f.name, category: f.category }));
                                }
                            });
                        }
                    });
                });
            }
            if (dashData && dashData.friendVeterans) {
                dashData.friendVeterans.forEach(v => {
                    if (v && v.factors) {
                        v.factors.forEach(f => {
                            if (f && f.name) {
                                factorSet.add(JSON.stringify({ name: f.name, category: f.category }));
                            }
                        });
                    }
                });
            }
            state.uniqueFactors = Array.from(factorSet).map(str => JSON.parse(str)).sort((a, b) => a.name.localeCompare(b.name));
        }

        function getFactorsByCategory(categoryName) {
            const dbCategory = invCategoryMap[categoryName];
            if (!dbCategory) return [];
            return state.uniqueFactors.filter(f => f.category === dbCategory);
        }

        function renderSparkCriterionRow(categoryName, criterion, index, type) {
            const factors = getFactorsByCategory(categoryName);
            const optionsHtml = factors.map(f => {
                const selected = f.name === criterion.name ? 'selected' : '';
                return `<option value="${escapeAttr(f.name)}" ${selected}>${escapeHtml(f.name)}</option>`;
            }).join('');

            return `<div class="spark-criterion-row" data-category="${categoryName}" data-index="${index}" data-type="${type}">
                <select class="spark-criterion-select">
                    <option value="">-- Select Factor --</option>
                    ${optionsHtml}
                </select>
                <select class="spark-criterion-stars">
                    ${[1, 2, 3, 4, 5, 6, 7, 8, 9].map(stars => {
                        const selected = stars === Number(criterion.minStars) ? 'selected' : '';
                        return `<option value="${stars}" ${selected}>${stars}★</option>`;
                    }).join('')}
                </select>
                <button class="spark-criterion-remove" type="button" title="Remove factor">&times;</button>
            </div>`;
        }

        function renderSparkCriteria(type) {
            const prefix = type === 'parents' ? 'parent' : 'friend-vet';
            const categories = ['blue', 'pink', 'green', 'white'];
            
            categories.forEach(cat => {
                const listEl = document.getElementById(`${prefix}-${cat}-criteria`);
                if (listEl) listEl.innerHTML = '';
            });

            const criteria = state.filters[type].criteria;
            criteria.forEach((criterion, idx) => {
                const cat = criterion.category;
                const listEl = document.getElementById(`${prefix}-${cat}-criteria`);
                if (listEl) {
                    listEl.insertAdjacentHTML('beforeend', renderSparkCriterionRow(cat, criterion, idx, type));
                }
            });

            const containerId = type === 'parents' ? 'parent-spark-drawer' : 'friend-vet-spark-drawer';
            const container = document.getElementById(containerId);
            if (!container) return;

            container.querySelectorAll('.spark-criterion-select').forEach(sel => {
                sel.addEventListener('change', (e) => {
                    const row = e.target.closest('.spark-criterion-row');
                    const idx = Number(row.dataset.index);
                    const val = e.target.value;
                    state.filters[type].criteria[idx].name = val;
                    triggerFilterReRender(type);
                });
            });

            container.querySelectorAll('.spark-criterion-stars').forEach(sel => {
                sel.addEventListener('change', (e) => {
                    const row = e.target.closest('.spark-criterion-row');
                    const idx = Number(row.dataset.index);
                    const val = Number(e.target.value);
                    state.filters[type].criteria[idx].minStars = val;
                    triggerFilterReRender(type);
                });
            });

            container.querySelectorAll('.spark-criterion-remove').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const row = e.target.closest('.spark-criterion-row');
                    const idx = Number(row.dataset.index);
                    state.filters[type].criteria.splice(idx, 1);
                    renderSparkCriteria(type);
                    triggerFilterReRender(type);
                });
            });
        }

        function triggerFilterReRender(type) {
            if (type === 'parents') {
                if (dashData && dashData.parents) renderParents(dashData.parents);
            } else if (type === 'friendVets') {
                if (dashData && dashData.friendVeterans) renderFriendVeterans();
            }
        }

        function addSparkCriterion(type, categoryName) {
            state.filters[type].criteria.push({
                category: categoryName,
                name: '',
                minStars: 3
            });
            renderSparkCriteria(type);
            triggerFilterReRender(type);
        }

        function bindLibraryFilters() {
            if (els.deckSearch) {
                els.deckSearch.addEventListener('input', () => {
                    state.filters.decks.query = els.deckSearch.value;
                    if (dashData && dashData.validDecks) renderDecks(dashData.validDecks);
                });
            }
            if (els.traineeSearch) {
                els.traineeSearch.addEventListener('input', () => {
                    state.filters.trainees.query = els.traineeSearch.value;
                    if (dashData && dashData.umas) renderTrainees(dashData.umas);
                });
            }
            if (els.friendSearch) {
                els.friendSearch.addEventListener('input', () => {
                    state.filters.friends.query = els.friendSearch.value;
                    renderFriends();
                });
            }
            if (els.friendType) {
                els.friendType.addEventListener('change', () => {
                    state.filters.friends.type = els.friendType.value;
                    renderFriends();
                });
            }
            if (els.friendRarityRow) {
                els.friendRarityRow.querySelectorAll('.filter-chip').forEach(chip => {
                    chip.addEventListener('click', () => {
                        const filterVal = chip.dataset.filter;
                        if (filterVal === 'all' || filterVal === '4') {
                            state.filters.friends.limitBreak = filterVal;
                            els.friendRarityRow.querySelectorAll('.filter-chip').forEach(c => {
                                const f = c.dataset.filter;
                                if (f === 'all' || f === '4') {
                                    c.classList.toggle('active', f === filterVal);
                                }
                            });
                        } else {
                            state.filters.friends.rarity[filterVal] = !state.filters.friends.rarity[filterVal];
                            chip.classList.toggle('active', state.filters.friends.rarity[filterVal]);
                        }
                        renderFriends();
                    });
                });
            }
            if (els.cardSearch) {
                els.cardSearch.addEventListener('input', () => {
                    state.filters.ownedCards.query = els.cardSearch.value;
                    if (dashData && dashData.supports) renderSupports(dashData.supports);
                });
            }
            if (els.cardType) {
                els.cardType.addEventListener('change', () => {
                    state.filters.ownedCards.type = els.cardType.value;
                    if (dashData && dashData.supports) renderSupports(dashData.supports);
                });
            }
            if (els.cardRarityRow) {
                els.cardRarityRow.querySelectorAll('.filter-chip').forEach(chip => {
                    chip.addEventListener('click', () => {
                        const filterVal = chip.dataset.filter;
                        state.filters.ownedCards.rarity[filterVal] = !state.filters.ownedCards.rarity[filterVal];
                        chip.classList.toggle('active', state.filters.ownedCards.rarity[filterVal]);
                        if (dashData && dashData.supports) renderSupports(dashData.supports);
                    });
                });
            }
            if (els.parentSearch) {
                els.parentSearch.addEventListener('input', () => {
                    state.filters.parents.query = els.parentSearch.value;
                    if (dashData && dashData.parents) renderParents(dashData.parents);
                });
            }
            if (els.parentRank) {
                els.parentRank.addEventListener('change', () => {
                    state.filters.parents.rank = els.parentRank.value;
                    if (dashData && dashData.parents) renderParents(dashData.parents);
                });
            }
            if (els.parentSparkToggle && els.parentSparkDrawer) {
                els.parentSparkToggle.addEventListener('click', () => {
                    const isHidden = els.parentSparkDrawer.style.display === 'none';
                    els.parentSparkDrawer.style.display = isHidden ? 'flex' : 'none';
                    const chevron = els.parentSparkToggle.querySelector('.spark-toggle-chevron');
                    if (chevron) chevron.classList.toggle('expanded', isHidden);
                });
            }
            if (els.parentSparkDrawer) {
                els.parentSparkDrawer.querySelectorAll('.add-spark-criterion-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const cat = btn.dataset.category;
                        addSparkCriterion('parents', cat);
                    });
                });
            }
            if (els.friendVetSearch) {
                els.friendVetSearch.addEventListener('input', () => {
                    state.filters.friendVets.query = els.friendVetSearch.value;
                    renderFriendVeterans();
                });
            }
            if (els.friendVetRank) {
                els.friendVetRank.addEventListener('change', () => {
                    state.filters.friendVets.rank = els.friendVetRank.value;
                    renderFriendVeterans();
                });
            }
            if (els.friendVetSparkToggle && els.friendVetSparkDrawer) {
                els.friendVetSparkToggle.addEventListener('click', () => {
                    const isHidden = els.friendVetSparkDrawer.style.display === 'none';
                    els.friendVetSparkDrawer.style.display = isHidden ? 'flex' : 'none';
                    const chevron = els.friendVetSparkToggle.querySelector('.spark-toggle-chevron');
                    if (chevron) chevron.classList.toggle('expanded', isHidden);
                });
            }
            if (els.friendVetSparkDrawer) {
                els.friendVetSparkDrawer.querySelectorAll('.add-spark-criterion-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const cat = btn.dataset.category;
                        addSparkCriterion('friendVets', cat);
                    });
                });
            }

            renderSparkCriteria('parents');
            renderSparkCriteria('friendVets');
        }

        function renderParents(parents) {
            scanUniqueFactors();
            const query = (state.filters.parents.query || '').toLowerCase().trim();
            const minRank = state.filters.parents.rank;
            const criteria = state.filters.parents.criteria;
            
            const filteredParents = parents.filter(parent => {
                if (query) {
                    const cName = String(parent.name || '').toLowerCase();
                    if (!cName.includes(query)) return false;
                }
                if (minRank !== 'all') {
                    const rankVal = Number(parent.rank || 0);
                    if (minRank === 'UG' && rankVal < 19) return false;
                    if (minRank === 'SS' && rankVal < 18) return false;
                    if (minRank === 'S' && rankVal < 17) return false;
                    if (minRank === 'A+' && rankVal < 16) return false;
                }
                for (const criterion of criteria) {
                    if (!criterion.name) continue;
                    let totalStars = 0;
                    const tree = parent.tree || {};
                    ['self', 'p1', 'p2'].forEach(key => {
                        const node = tree[key];
                        if (node && node.factors) {
                            node.factors.forEach(f => {
                                if (f && f.name === criterion.name) {
                                    totalStars += Number(f.stars || 0);
                                }
                            });
                        }
                    });
                    if (totalStars < criterion.minStars) return false;
                }
                return true;
            });

            els.parentCount.innerText = `(${filteredParents.length}/${parents.length})`;
            els.parentGrid.innerHTML = filteredParents.map(parent => {
                const tree = parent.tree || {};
                const selfNode = tree.self || { card_id: parent.card_id, name: parent.name };
                const imgId = (selfNode.card_id || parent.card_id) || '100101';
                const originalIdx = (dashData.parents || []).indexOf(parent);
                return `<div class="grid-card parent-card" data-original-index="${originalIdx}">
                    <div class="rank-badge">${rankMap[parent.rank] || '??'}</div>
                    <div class="parent-tree">
                        ${renderParentTreeNode(selfNode, 'self')}
                        <svg class="parent-tree-lines" viewBox="0 0 100 24" preserveAspectRatio="none" aria-hidden="true">
                            <line x1="50" y1="0" x2="22" y2="24"></line>
                            <line x1="50" y1="0" x2="78" y2="24"></line>
                        </svg>
                        <div class="parent-tree-row">
                            ${renderParentTreeNode(tree.p1, 'p1')}
                            ${renderParentTreeNode(tree.p2, 'p2')}
                        </div>
                    </div>
                    <div class="sparks-tooltip" style="--spark-bg: url('/api/images/${imgId}.png')">
                        <div class="sparks-tooltip-title"></div>
                        <div class="sparks-tooltip-scroll">
                            <div class="sparks-lineage-grid">
                                ${renderParentSparks(parent, imgId)}
                            </div>
                        </div>
                    </div>
                    <div class="grid-card-overlay">
                        <span class="grid-card-name">${parent.name || 'Unknown'}</span>
                    </div>
                </div>`;
            }).join('');
            attachParentHandlers();
            bindSparkTooltips();
        }
        function renderTrainees(umas) {
            const query = (state.filters.trainees.query || '').toLowerCase().trim();
            const filteredUmas = umas.filter(uma => {
                if (!query) return true;
                return String(uma.name || '').toLowerCase().includes(query);
            });

            els.umaCount.innerText = `(${filteredUmas.length}/${umas.length})`;
            els.umaGrid.innerHTML = filteredUmas.map(uma => {
                const imgId = uma.id || '100101';
                const originalIdx = (dashData.umas || []).indexOf(uma);
                return `<div class="grid-card" data-original-index="${originalIdx}">
                    <img src="/api/images/${imgId}.png" onerror="hideBrokenImage(this)">
                    <div class="grid-card-overlay"><span class="grid-card-name">${uma.name || 'Unknown'}</span></div>
                </div>`;
            }).join('');
            attachTraineeHandlers();
        }
        function renderSupports(supports) {
            const query = (state.filters.ownedCards.query || '').toLowerCase().trim();
            const type = state.filters.ownedCards.type;
            const filteredSupports = supports.filter(card => {
                if (query && !String(card.name || '').toLowerCase().includes(query)) return false;
                if (type !== 'all' && card.type !== type) return false;
                if (!state.filters.ownedCards.rarity[card.rarity]) return false;
                return true;
            });

            const selected = new Set((state.deckEditor.cards || []).map(card => String(card.id)));
            els.cardCount.innerText = `(${filteredSupports.length}/${supports.length})`;
            els.cardGrid.innerHTML = filteredSupports.map(card => {
                const imgId = card.id || '10001';
                const isSelected = selected.has(String(card.id));
                return `<div class="grid-card support-card ${isSelected ? 'deck-pick-selected' : ''}" data-card-id="${escapeAttr(card.id)}">
                    <img src="/api/images/${imgId}.png" onerror="hideBrokenImage(this)">
                    <div class="grid-card-overlay">
                        <span class="grid-card-kicker">${escapeHtml((card.rarity || '?') + ' | ' + (card.type || '?'))} · LB${card.limit_break_count ?? '?'}</span>
                        <span class="grid-card-name">${escapeHtml(card.name || 'Unknown')}</span>
                    </div>
                </div>`;
            }).join('');
            document.querySelectorAll('#card-grid .support-card').forEach((element) => {
                element.addEventListener('click', () => {
                    const cardId = String(element.dataset.cardId);
                    const cardObj = (dashData.supports || []).find(c => String(c.id) === cardId);
                    if (cardObj) toggleDeckEditorCard(cardObj);
                });
            });
        }
        function showDashboardView(data) {
            document.body.classList.add('dashboard-mode');
            els.loginView.style.display = 'none';
            els.dashboardView.style.display = '';
            els.dashboardView.classList.add('active');
            els.logoutBtn.style.display = 'block';
            showNavbar();
            renderAccountStrip(data.account);
            syncDashboardHeight();
        }

        function autoLoadCareerSelection() {
            const activeCareer = state.account && state.account.career && state.account.career.active ? state.account.career : null;
            if (!activeCareer) return;

            resetSelection();
            document.querySelectorAll('.deck-container.selected, #uma-grid .grid-card.selected, #parent-grid .grid-card.selected, #friend-grid .grid-card.selected')
                .forEach(el => el.classList.remove('selected'));

            selectCareerDeck(activeCareer);

            if (activeCareer.card_id && dashData.umas) {
                const umaIdx = dashData.umas.findIndex(u => String(u.id) === String(activeCareer.card_id));
                if (umaIdx >= 0) {
                    selection.trainee = dashData.umas[umaIdx];
                    const umaEl = document.querySelector(`#uma-grid .grid-card[data-original-index="${umaIdx}"]`);
                    if (umaEl) umaEl.classList.add('selected');
                }
            }

            if (dashData.parents) {
                const p1 = activeCareer.parent_id_1;
                const p2 = activeCareer.parent_id_2;

                if (p1 || p2) {
                    dashData.parents.forEach((p, idx) => {
                        const pId = Number(p.instance_id);
                        if ((p1 && pId === Number(p1)) || (p2 && pId === Number(p2))) {
                            if (selection.veterans.length < 2 && !selection.veterans.find(v => Number(v.instance_id) === pId)) {
                                p._gridIdx = idx;
                                selection.veterans.push(p);
                                const parentEl = document.querySelector(`#parent-grid .grid-card[data-original-index="${idx}"]`);
                                if (parentEl) parentEl.classList.add('selected');
                            }
                        }
                    });
                    updateVetSelectability();
                }
            }

            selectCareerFriend(activeCareer);
            renderTeamPanel();
        }

        function applyServerSelection(serverSelection) {
            if (!serverSelection) return;
            if (serverSelection.deck && dashData.validDecks) {
                const deckIdx = dashData.validDecks.findIndex(d => Number(d.id) === Number(serverSelection.deck.id));
                if (deckIdx >= 0) {
                    selection.deck = dashData.validDecks[deckIdx];
                    const deckEl = document.querySelector(`.deck-container[data-original-index="${deckIdx}"]`);
                    if (deckEl) deckEl.classList.add('selected');
                }
            }
            if (serverSelection.trainee && dashData.umas) {
                const umaIdx = dashData.umas.findIndex(u => String(u.id) === String(serverSelection.trainee.id));
                if (umaIdx >= 0) {
                    selection.trainee = dashData.umas[umaIdx];
                    const umaEl = document.querySelector(`#uma-grid .grid-card[data-original-index="${umaIdx}"]`);
                    if (umaEl) umaEl.classList.add('selected');
                }
            }
            if (serverSelection.veterans && dashData.parents) {
                serverSelection.veterans.forEach(v => {
                    const pIdx = dashData.parents.findIndex(p => Number(p.instance_id) === Number(v.instance_id));
                    if (pIdx >= 0 && selection.veterans.length < 2) {
                        const parent = dashData.parents[pIdx];
                        parent._gridIdx = pIdx;
                        selection.veterans.push(parent);
                        const parentEl = document.querySelector(`#parent-grid .grid-card[data-original-index="${pIdx}"]`);
                        if (parentEl) parentEl.classList.add('selected');
                    }
                });
                updateVetSelectability();
            }
            if (serverSelection.friend) {
                state.pendingFriendSelection = {
                    viewer_id: String(serverSelection.friend.viewer_id),
                    support_card_id: String(serverSelection.friend.support_card_id)
                };
            }
        }

        async function renderDashboard(data, options = {}) {
            dashData = data;
            dashData.decks = (data.decks || []).map(deck => deck.local ? {
                ...deck,
                cards: (deck.cards || []).map(enrichDeckCard)
            } : deck);
            dashData.validDecks = dashData.decks.filter(isValidDeck);
            dashData.friends = data.friends || [];
            dashData.friendExcludeIds = data.friendExcludeIds || [];
            if (els.lastSessionBanner) {
                els.lastSessionBanner.style.display = 'none';
                els.lastSessionBanner.innerHTML = '';
            }
            showDashboardView(data);
            renderCounts(data);
            renderDecks(dashData.validDecks);
            renderParents(data.parents);
            renderTrainees(dashData.umas);
            renderSupports(data.supports);
            resetSelection();
            if (data.selection) applyServerSelection(data.selection);
            autoLoadCareerSelection();

            await loadPresets();
            await fetchEventBoostSettings();
            if (!dashData.friends.length) {
                loadFriends(false);
                loadFriendVeterans(false);
            } else {
                renderFriends();
                if ((dashData.friendVeterans || []).length === 0) {
                    loadFriendVeterans(false);
                } else {
                    renderFriendVeterans();
                }
            }
            bindSparkTooltips();
            attachSelectionHandlers();
            bindRaceHandlers();
            bindPresetHandlers();
            renderTeamPanel();
            updateAdvisorRecommendations();

            startRunnerPolling();
            await waitForDomPaint(2);
            setLoadingScreen(false);
            await waitForDomPaint(2);
            if (options.animateIntro !== false) {
                playBrandIntro();
                if (options.waitForIntro) await sleep(780);
            }
        }

        function formatRelativeTime(iso) {
            if (!iso) return '';
            const then = Date.parse(iso);
            if (isNaN(then)) return '';
            const deltaSec = Math.max(0, Math.round((Date.now() - then) / 1000));
            if (deltaSec < 60) return 'just now';
            if (deltaSec < 3600) return `${Math.round(deltaSec / 60)}m ago`;
            if (deltaSec < 86400) return `${Math.round(deltaSec / 3600)}h ago`;
            return `${Math.round(deltaSec / 86400)}d ago`;
        }
        function renderLastSessionBanner(cache) {
            const el = els.lastSessionBanner;
            if (!el) return;
            if (!cache || (!cache.viewer_id && !cache.selected_preset && !cache.career)) {
                el.style.display = 'none';
                el.innerHTML = '';
                return;
            }
            const pills = [];
            if (cache.viewer_id) {
                pills.push(`<span class="last-session-banner-pill">Viewer <strong>${escapeHtml(cache.viewer_id)}</strong></span>`);
            }
            if (cache.career && cache.career.name) {
                const turn = cache.career.turn ? ` · T${escapeHtml(cache.career.turn)}` : '';
                const active = cache.career.active ? ' · active' : '';
                pills.push(`<span class="last-session-banner-pill">${escapeHtml(cache.career.name)}${turn}${active}</span>`);
            }
            if (cache.selected_preset) {
                pills.push(`<span class="last-session-banner-pill">preset <strong>${escapeHtml(cache.selected_preset)}</strong></span>`);
            }
            const when = formatRelativeTime(cache.last_login_at);
            if (when) {
                pills.push(`<span class="last-session-banner-pill">${escapeHtml(when)}</span>`);
            }
            if (!pills.length) {
                el.style.display = 'none';
                el.innerHTML = '';
                return;
            }
            el.innerHTML =
                `<span class="last-session-banner-title">Last session</span>` +
                `<div class="last-session-banner-row">${pills.join('')}</div>`;
            el.style.display = 'block';
        }
        async function fetchSessionCache() {
            try {
                const data = await apiJson('/api/session-cache');
                if (data && data.success) {
                    state.lastSessionCache = data.cache || {};
                    if (state.lastSessionCache.steam_username) {
                        const uInput = document.getElementById('username');
                        if (uInput) uInput.value = state.lastSessionCache.steam_username;
                    }
                    if (state.lastSessionCache.steam_password) {
                        const pInput = document.getElementById('password');
                        if (pInput) pInput.value = state.lastSessionCache.steam_password;
                    }
                    if (state.lastSessionCache.proxy_url) {
                        const prxyInput = document.getElementById('proxy-url');
                        if (prxyInput) prxyInput.value = state.lastSessionCache.proxy_url;
                    }
                }
            } catch (e) {}
            return state.lastSessionCache || {};
        }
        async function loadAndRenderSessionCache() {
            const cache = await fetchSessionCache();
            renderLastSessionBanner(cache);
        }
        async function persistSelectedPresetToCache(name) {
            try {
                await apiJson('/api/session-cache', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ selected_preset: name || '' })
                });
            } catch (e) {}
        }

        async function restoreSession() {
            await fetchSessionCache();
            try {
                const data = await apiJson('/api/session?t=' + Date.now());
                if (data && data.success) await renderDashboard(data, { animateIntro: true, waitForIntro: false });
                else {
                    hideNavbar();
                    setLoadingScreen(false);
                    renderLastSessionBanner(state.lastSessionCache);
                }
            } catch (e) {
                hideNavbar();
                setLoadingScreen(false);
                renderLastSessionBanner(state.lastSessionCache);
            }
        }
        bindDelayControls();
        bindMasterDataControls();
        bindLibraryFilters();
        setLoadingScreen(true);
        restoreSession();
})();
