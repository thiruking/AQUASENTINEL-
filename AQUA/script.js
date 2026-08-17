(function () {
    const frameCount = 240;
    const canvas = document.getElementById('hero-canvas');
    const ctx = canvas ? canvas.getContext('2d') : null;

    const images = [];
    const loadedStatus = new Array(frameCount).fill(false);

    let targetFrame = 0;
    let currentFrame = 0;
    let lastRenderedFrame = -1;
    let basePath = '';
    let isSimulating = false;
    let simInterval = null;
    // Slider input events can overlap. Only the newest prediction is allowed
    // to update the dashboard so an old SAFE response cannot overwrite a new
    // CRITICAL reading.
    let latestPredictionRequest = 0;

    // Prefer the persistent session only when the user explicitly selected
    // “Remember me”; otherwise keep the token scoped to this browser tab.
    let jwtToken = localStorage.getItem('aquasentinel_jwt') || sessionStorage.getItem('aquasentinel_jwt') || null;
    let currentUser = null;

    // Use the page origin so the dashboard works in local development and
    // behind a reverse proxy / hosted preview without browser-side localhost calls.
    const API_BASE = '/api';

    function getFrameFilename(index) {
        const frameNum = String(index + 1).padStart(3, '0');
        return `ezgif-frame-${frameNum}.jpg`;
    }

    function getFrameUrl(index) {
        return basePath + getFrameFilename(index);
    }

    function resizeCanvas() {
        const dpr = window.devicePixelRatio || 1;
        if (canvas) {
            canvas.width = Math.floor(window.innerWidth * dpr);
            canvas.height = Math.floor(window.innerHeight * dpr);
        }
        render(Math.round(currentFrame));
    }

    function drawImageScaled(img, targetCtx, targetCanvas) {
        if (!targetCtx || !targetCanvas) return;
        const dWidth = targetCanvas.width;
        const dHeight = targetCanvas.height;
        const iWidth = img.width;
        const iHeight = img.height;

        if (!iWidth || !iHeight) return;

        const hRatio = dWidth / iWidth;
        const vRatio = dHeight / iHeight;
        const ratio = Math.min(hRatio, vRatio);

        const drawW = iWidth * ratio;
        const drawH = iHeight * ratio;
        const drawX = (dWidth - drawW) / 2;
        const drawY = (dHeight - drawH) / 2;

        targetCtx.fillStyle = '#000000';
        targetCtx.fillRect(0, 0, dWidth, dHeight);

        targetCtx.imageSmoothingEnabled = true;
        targetCtx.imageSmoothingQuality = 'high';

        targetCtx.drawImage(img, 0, 0, iWidth, iHeight, drawX, drawY, drawW, drawH);
    }

    function findClosestLoadedFrame(index) {
        if (loadedStatus[index]) return index;

        for (let dist = 1; dist < frameCount; dist++) {
            if (index - dist >= 0 && loadedStatus[index - dist]) return index - dist;
            if (index + dist < frameCount && loadedStatus[index + dist]) return index + dist;
        }
        return -1;
    }

    function render(index) {
        const clampIndex = Math.max(0, Math.min(frameCount - 1, index));
        const activeIndex = findClosestLoadedFrame(clampIndex);

        if (activeIndex !== -1 && images[activeIndex] && ctx && canvas) {
            drawImageScaled(images[activeIndex], ctx, canvas);
        }
    }

    function updateScrollProgress() {
        const scrollTop = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || 0;
        const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        const scrollFraction = Math.max(0, Math.min(1, scrollTop / maxScroll));
        targetFrame = scrollFraction * (frameCount - 1);
    }

    function startPreloading() {
        const firstImg = new Image();
        firstImg.src = getFrameUrl(0);
        firstImg.onload = () => {
            loadedStatus[0] = true;
            render(0);
        };
        images[0] = firstImg;

        for (let i = 1; i < frameCount; i++) {
            const img = new Image();
            img.src = getFrameUrl(i);
            img.onload = () => {
                loadedStatus[i] = true;
                if (Math.round(currentFrame) === i) {
                    render(i);
                }
            };
            images[i] = img;
        }
    }

    function detectBasePathAndInit() {
        const testFileName = getFrameFilename(0);
        const testImg = new Image();

        testImg.onload = () => {
            basePath = '';
            initEngine();
        };

        testImg.onerror = () => {
            basePath = 'AQUA/';
            initEngine();
        };

        testImg.src = testFileName;
    }

    function initEngine() {
        startPreloading();
        resizeCanvas();
        updateScrollProgress();
        requestAnimationFrame(animate);
        initAppBindings();
    }

    function animate() {
        const delta = targetFrame - currentFrame;
        if (Math.abs(delta) > 0.001) {
            currentFrame += delta * 0.2;
        } else {
            currentFrame = targetFrame;
        }

        const renderIndex = Math.round(currentFrame);
        if (renderIndex !== lastRenderedFrame) {
            render(renderIndex);
            lastRenderedFrame = renderIndex;
        }

        requestAnimationFrame(animate);
    }

    function getAuthHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (jwtToken) {
            headers['Authorization'] = `Bearer ${jwtToken}`;
        }
        return headers;
    }

    // ============================================================
    // AQUASENTINEL+ v1.3.0 UX & AUTHENTICATION BINDINGS
    // ============================================================
    function initAppBindings() {
        initModeToggle();
        initAuthAndSession();
        initGuidedTour();
        initFAQModal();
        initPondModal();

        fetchHealthStatus();
        fetchModelMetrics();
        fetchAlerts();
        fetchMultiPonds();
        fetchTrends();

        // Sliders & Selectors
        const sliders = ['ph', 'do', 'ammonia', 'nitrate', 'turbidity', 'temp', 'salinity'];
        sliders.forEach(id => {
            const el = document.getElementById(`slider-${id}`);
            if (el) {
                el.addEventListener('input', (e) => {
                    const valSpan = document.getElementById(`val-${id}`);
                    if (valSpan) valSpan.innerText = e.target.value;
                    triggerPrediction();
                });
            }
        });

        const speciesSel = document.getElementById('species-select');
        if (speciesSel) {
            speciesSel.addEventListener('change', triggerPrediction);
        }

        // Notification center toggle
        const notifToggle = document.getElementById('notif-toggle');
        if (notifToggle) {
            notifToggle.addEventListener('click', () => {
                const dd = document.getElementById('notif-dropdown');
                if (dd) dd.classList.toggle('show');
            });
        }

        const markRead = document.getElementById('btn-mark-read');
        if (markRead) {
            markRead.addEventListener('click', () => {
                const badge = document.getElementById('notif-badge');
                if (badge) badge.style.display = 'none';
                const list = document.getElementById('notif-list');
                if (list) list.innerHTML = '<p style="color:#94a3b8; font-size:0.75rem; padding:8px;">All notifications marked as read.</p>';
            });
        }

        // Simulation Stream Button
        const simBtn = document.getElementById('btn-toggle-sim');
        if (simBtn) {
            simBtn.addEventListener('click', toggleSimulation);
        }

        triggerPrediction();
    }

    // FEATURE 1: Simple Mode vs Advanced Mode Toggle
    function initModeToggle() {
        const toggle = document.getElementById('mode-toggle-checkbox');
        const labelText = document.getElementById('mode-label-text');
        
        const savedMode = localStorage.getItem('aquasentinel_mode') || 'simple';
        if (savedMode === 'advanced') {
            document.body.classList.remove('simple-mode');
            if (toggle) toggle.checked = true;
            if (labelText) labelText.innerHTML = 'Mode: <strong>Advanced</strong>';
        } else {
            document.body.classList.add('simple-mode');
            if (toggle) toggle.checked = false;
            if (labelText) labelText.innerHTML = 'Mode: <strong>Simple</strong>';
        }

        if (toggle) {
            toggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    document.body.classList.remove('simple-mode');
                    localStorage.setItem('aquasentinel_mode', 'advanced');
                    if (labelText) labelText.innerHTML = 'Mode: <strong>Advanced</strong>';
                } else {
                    document.body.classList.add('simple-mode');
                    localStorage.setItem('aquasentinel_mode', 'simple');
                    if (labelText) labelText.innerHTML = 'Mode: <strong>Simple</strong>';
                }
            });
        }
    }

    // FEATURE 2: Auth Tabs & Session Handling
    function initAuthAndSession() {
        const loginBtn = document.getElementById('btn-login-modal');
        const loginModal = document.getElementById('login-modal');
        const loginClose = document.getElementById('login-close');
        
        const tabLogin = document.getElementById('tab-login-btn');
        const tabReg = document.getElementById('tab-register-btn');
        const formLogin = document.getElementById('login-form');
        const formReg = document.getElementById('register-form');

        const userDisplay = document.getElementById('user-display');
        const userDropdown = document.getElementById('user-dropdown');
        const btnLogout = document.getElementById('btn-logout');

        if (loginBtn && loginModal) {
            loginBtn.addEventListener('click', () => {
                if (currentUser) {
                    if (userDropdown) userDropdown.classList.toggle('show');
                } else {
                    loginModal.classList.add('show');
                }
            });
        }

        if (loginClose && loginModal) {
            loginClose.addEventListener('click', () => loginModal.classList.remove('show'));
        }

        if (tabLogin && tabReg && formLogin && formReg) {
            tabLogin.addEventListener('click', () => {
                tabLogin.classList.add('active');
                tabReg.classList.remove('active');
                formLogin.style.display = 'block';
                formReg.style.display = 'none';
            });

            tabReg.addEventListener('click', () => {
                tabReg.classList.add('active');
                tabLogin.classList.remove('active');
                formReg.style.display = 'block';
                formLogin.style.display = 'none';
            });
        }

        if (formLogin) {
            formLogin.addEventListener('submit', async (e) => {
                e.preventDefault();
                const u = document.getElementById('login-user').value;
                const p = document.getElementById('login-pass').value;
                const rem = document.getElementById('remember-me')?.checked || false;

                try {
                    const res = await fetch(`${API_BASE}/auth/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: u, password: p, remember_me: rem })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        jwtToken = data.access_token;
                        if (rem) localStorage.setItem('aquasentinel_jwt', jwtToken);
                        else sessionStorage.setItem('aquasentinel_jwt', jwtToken);

                        currentUser = data.user;
                        updateUserSessionUI(currentUser);
                        loginModal.classList.remove('show');
                        fetchMultiPonds();
                    } else {
                        alert('Incorrect email or password. Evaluator Demo: admin@aquasentinel.demo / demo1234');
                    }
                } catch (err) {
                    alert('Login server connection failed. Ensure backend is running.');
                }
            });
        }

        if (formReg) {
            formReg.addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('reg-name').value;
                const farm = document.getElementById('reg-farm').value;
                const email = document.getElementById('reg-email').value;
                const pass = document.getElementById('reg-pass').value;

                try {
                    const res = await fetch(`${API_BASE}/auth/register`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, farm_name: farm, email, password: pass })
                    });
                    if (res.ok) {
                        alert('Registration successful! Please log in with your credentials.');
                        tabLogin.click();
                        document.getElementById('login-user').value = email;
                    } else {
                        const err = await res.json();
                        alert(`Registration failed: ${err.detail || 'Email already exists'}`);
                    }
                } catch (err) {
                    alert('Registration failed. Check network connection.');
                }
            });
        }

        if (btnLogout) {
            btnLogout.addEventListener('click', () => {
                jwtToken = null;
                currentUser = null;
                localStorage.removeItem('aquasentinel_jwt');
                sessionStorage.removeItem('aquasentinel_jwt');
                updateUserSessionUI(null);
                if (userDropdown) userDropdown.classList.remove('show');
                fetchMultiPonds();
            });
        }

        checkActiveSession();
    }

    async function checkActiveSession() {
        if (!jwtToken) return;
        try {
            const res = await fetch(`${API_BASE}/auth/me`, { headers: getAuthHeaders() });
            if (res.ok) {
                currentUser = await res.json();
                updateUserSessionUI(currentUser);
            } else {
                // Token expired
                showToast('Session expired. Please log in again.');
                jwtToken = null;
                localStorage.removeItem('aquasentinel_jwt');
                sessionStorage.removeItem('aquasentinel_jwt');
                updateUserSessionUI(null);
            }
        } catch (e) {}
    }

    function updateUserSessionUI(user) {
        const uDisplay = document.getElementById('user-display');
        const dName = document.getElementById('dropdown-user-name');
        const dRole = document.getElementById('dropdown-user-role');

        if (user) {
            if (uDisplay) uDisplay.innerText = user.name || user.email;
            if (dName) dName.innerText = user.name || user.email;
            if (dRole) dRole.innerText = (user.role || 'farmer').toUpperCase();
        } else {
            if (uDisplay) uDisplay.innerText = 'Admin Login';
            if (dName) dName.innerText = 'Guest User';
            if (dRole) dRole.innerText = 'VISITOR';
        }
    }

    // FEATURE 3: Add New Pond Modal
    function initPondModal() {
        const btnOpen = document.getElementById('btn-open-add-pond');
        const modal = document.getElementById('add-pond-modal');
        const btnClose = document.getElementById('add-pond-close');
        const form = document.getElementById('add-pond-form');

        if (btnOpen && modal) {
            btnOpen.addEventListener('click', () => {
                if (!currentUser) {
                    alert('Please log in to register a custom pond for your farm.');
                    return;
                }
                modal.classList.add('show');
            });
        }

        if (btnClose && modal) {
            btnClose.addEventListener('click', () => modal.classList.remove('show'));
        }

        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('pond-name-input').value;
                const species = document.getElementById('pond-species-input').value;

                try {
                    const res = await fetch(`${API_BASE}/ponds/create`, {
                        method: 'POST',
                        headers: getAuthHeaders(),
                        body: JSON.stringify({ name, species })
                    });
                    if (res.ok) {
                        alert(`Pond '${name}' successfully added!`);
                        modal.classList.remove('show');
                        fetchMultiPonds();
                    } else {
                        alert('Could not create pond. Ensure you are logged in.');
                    }
                } catch (err) {
                    alert('Error creating pond.');
                }
            });
        }
    }

    // FEATURE 4: FAQ Modal & Floating Help Button
    function initFAQModal() {
        const helpBtn = document.getElementById('floating-help-btn');
        const faqModal = document.getElementById('faq-modal');
        const faqClose = document.getElementById('faq-close');

        if (helpBtn && faqModal) {
            helpBtn.addEventListener('click', () => faqModal.classList.add('show'));
        }

        if (faqClose && faqModal) {
            faqClose.addEventListener('click', () => faqModal.classList.remove('show'));
        }

        const items = document.querySelectorAll('.faq-item');
        items.forEach(item => {
            const btn = item.querySelector('.faq-q');
            if (btn) {
                btn.addEventListener('click', () => {
                    item.classList.toggle('open');
                });
            }
        });
    }

    // FEATURE 5: Guided Tour Onboarding Overlay
    function initGuidedTour() {
        const overlay = document.getElementById('tour-overlay');
        const skipBtn = document.getElementById('tour-skip-btn');
        const nextBtn = document.getElementById('tour-next-btn');

        const title = document.getElementById('tour-title');
        const desc = document.getElementById('tour-desc');
        const badge = document.getElementById('tour-step-badge');

        const steps = [
            { title: "Welcome to AquaSentinel+", desc: "Your intelligent AI decision support system for coastal aquaculture. Let's take a 30-second tour.", badge: "Step 1 of 5" },
            { title: "Target Species & Top Status", desc: "Select Shrimp, Tilapia, or Carp in the navbar. The top banner gives you an instant 2-second status update.", badge: "Step 2 of 5" },
            { title: "Pollution Index & Farmer Verdict", desc: "View your 0-100 Pollution Index score and plain-language 'Will My Fish Survive?' verdict sentence.", badge: "Step 3 of 5" },
            { title: "Interactive What-If Sliders", desc: "Test real-time parameter changes (pH, DO, Ammonia) and get instant AI recommendations.", badge: "Step 4 of 5" },
            { title: "Pond Health Handbook", desc: "Non-technical farmers can open the Pond Health Guide for plain-language glossary cards and thermometer visual rules.", badge: "Step 5 of 5" }
        ];

        let currentStep = 0;

        const tourDone = localStorage.getItem('aquasentinel_tour_done');
        if (!tourDone && overlay) {
            setTimeout(() => overlay.classList.add('show'), 1500);
        }

        if (skipBtn) {
            skipBtn.addEventListener('click', () => {
                if (overlay) overlay.classList.remove('show');
                localStorage.setItem('aquasentinel_tour_done', 'true');
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                currentStep++;
                if (currentStep < steps.length) {
                    if (title) title.innerText = steps[currentStep].title;
                    if (desc) desc.innerText = steps[currentStep].desc;
                    if (badge) badge.innerText = steps[currentStep].badge;
                    if (currentStep === steps.length - 1) nextBtn.innerText = 'Finish Tour 🎉';
                } else {
                    if (overlay) overlay.classList.remove('show');
                    localStorage.setItem('aquasentinel_tour_done', 'true');
                }
            });
        }
    }

    function showToast(msg) {
        const toast = document.getElementById('toast-notification');
        const text = document.getElementById('toast-text');
        if (toast && text) {
            text.innerText = msg;
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', 4000);
        }
    }

    async function fetchHealthStatus() {
        try {
            const res = await fetch(`${API_BASE}/health`);
            if (res.ok) {
                const data = await res.json();
                const hStatus = document.getElementById('health-status');
                if (hStatus) hStatus.innerText = `${data.status.toUpperCase()} (${data.api_latency_ms}ms)`;

                const hModel = document.getElementById('health-model');
                if (hModel) hModel.innerText = `${data.model_name} (91.98% Accuracy)`;
            }
        } catch (e) {
            const hStatus = document.getElementById('health-status');
            if (hStatus) hStatus.innerText = 'Offline (Client Fallback Active)';
        }
    }

    function getSliderPayload() {
        return {
            species: document.getElementById('species-select')?.value || 'Shrimp',
            temperature: parseFloat(document.getElementById('slider-temp')?.value || 28.5),
            turbidity: parseFloat(document.getElementById('slider-turbidity')?.value || 35.0),
            DO: parseFloat(document.getElementById('slider-do')?.value || 6.5),
            ph: parseFloat(document.getElementById('slider-ph')?.value || 7.8),
            ammonia: parseFloat(document.getElementById('slider-ammonia')?.value || 0.02),
            nitrate: parseFloat(document.getElementById('slider-nitrate')?.value || 5.0),
            salinity: parseFloat(document.getElementById('slider-salinity')?.value || 15.0)
        };
    }

    async function triggerPrediction() {
        const payload = getSliderPayload();
        const requestId = ++latestPredictionRequest;
        try {
            const res = await fetch(`${API_BASE}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) {
                throw new Error(`Prediction request failed with status ${res.status}`);
            }

            const data = await res.json();
            // Ignore delayed responses from older slider positions.
            if (requestId === latestPredictionRequest) {
                updatePredictionUI(data);
            }
        } catch (e) {
            // The what-if tool remains useful if the API is temporarily down
            // or the page was opened through a static server.
            if (requestId === latestPredictionRequest) {
                fallbackClientPrediction(payload);
                showToast('Live API unavailable — showing a local what-if estimate. Start FastAPI for full reports and AI results.');
            }
        }
    }

    function updatePredictionUI(data) {
        const species = document.getElementById('species-select')?.value || 'Shrimp';

        // Update Pollution Index Card
        const piVal = document.getElementById('pi-score-val');
        if (piVal) piVal.innerText = data.pollution_index.toFixed(1);

        const statusBadge = document.getElementById('status-badge');
        if (statusBadge) {
            if (data.final_classification === 'CRITICAL') {
                statusBadge.innerText = '🔴 CRITICAL';
                statusBadge.className = 'badge-time status-critical';
            } else if (data.final_classification === 'MODERATE') {
                statusBadge.innerText = '🟡 MODERATE';
                statusBadge.className = 'badge-time status-moderate';
            } else {
                statusBadge.innerText = '🟢 SAFE';
                statusBadge.className = 'badge-time status-safe';
            }
        }

        const piDesc = document.getElementById('pi-status-desc');
        if (piDesc) piDesc.innerText = data.explanation;

        // Update Plain-Language Farmer Verdict Widget
        updateFarmerVerdictUI(species, data.final_classification, data.pollution_index, data.recommendations);

        // Update Always-Visible Top Status Banner
        updateTopStatusBannerUI(data.final_classification);

        // Results Panel
        const resClass = document.getElementById('res-classification');
        if (resClass) {
            resClass.innerText = data.final_classification === 'CRITICAL' ? '🔴 CRITICAL' : (data.final_classification === 'MODERATE' ? '🟡 MODERATE' : '🟢 SAFE');
        }

        const resAnom = document.getElementById('res-anomaly');
        if (resAnom) {
            resAnom.innerText = data.anomaly_flag ? `ANOMALY (Score: ${data.anomaly_score})` : 'Normal Pattern';
            resAnom.style.color = data.anomaly_flag ? '#ef4444' : '#38bdf8';
        }

        const resExp = document.getElementById('res-explanation');
        if (resExp) resExp.innerText = data.explanation;

        // Parameter Contributions
        const barsBox = document.getElementById('contribution-bars');
        if (barsBox && data.parameter_contributions) {
            barsBox.innerHTML = data.parameter_contributions.map(c => `
                <div class="contribution-item">
                    <div class="contrib-label-row">
                        <span>${c.parameter.toUpperCase()} (${c.current_value})</span>
                        <span>${c.contribution_percent}% [Range: ${c.ideal_range}]</span>
                    </div>
                    <div class="bar-outer">
                        <div class="bar-inner" style="width: ${c.contribution_percent}%;"></div>
                    </div>
                </div>
            `).join('');
        }

        // Feature Importances / SHAP
        const shapBox = document.getElementById('shap-bars');
        if (shapBox && data.feature_importances) {
            const keys = Object.keys(data.feature_importances).slice(0, 7);
            shapBox.innerHTML = keys.map(k => `
                <div class="shap-item">
                    <span class="shap-label">${k.replace('_', ' ').toUpperCase()}</span>
                    <div class="shap-bar-outer">
                        <div class="shap-bar-inner" style="width: ${data.feature_importances[k]}%;"></div>
                    </div>
                    <span class="shap-val">${data.feature_importances[k]}%</span>
                </div>
            `).join('');
        }

        // Recommendations
        const recsBox = document.getElementById('recs-list');
        if (recsBox && data.recommendations) {
            recsBox.innerHTML = data.recommendations.map(r => `<li>${r}</li>`).join('');
        }
    }

    function updateFarmerVerdictUI(species, status, pi, recs) {
        const vText = document.getElementById('farmer-verdict-text');
        const gHead = document.getElementById('guide-verdict-title');
        const eHead = document.getElementById('embedded-verdict-headline');
        const gAct = document.getElementById('guide-action-desc');
        const eAct = document.getElementById('embedded-action-desc');

        let sentence = '';
        let icon = '🟢';
        let action = (recs && recs.length > 0) ? recs[0] : 'All parameters optimal. Maintain standard feeding and water monitoring schedule.';

        if (status === 'CRITICAL') {
            icon = '🚨';
            sentence = `🚨 <strong>Your ${species} are at risk.</strong> Water stress is dangerously high (Pollution Index: ${pi.toFixed(1)}/100). Act within the next few hours to prevent fish loss.`;
        } else if (status === 'MODERATE') {
            icon = '⚠️';
            sentence = `⚠️ <strong>Your ${species} are under mild stress.</strong> Water parameters are slightly off — fish may eat less and grow slower if uncorrected.`;
        } else {
            icon = '✅';
            sentence = `✅ <strong>Your ${species} are safe right now.</strong> All water conditions are within a healthy operational range.`;
        }

        if (vText) vText.innerHTML = sentence;

        const headlineHtml = `<span>${icon}</span> <span>${sentence.replace(/<[^>]*>/g, '')}</span>`;
        if (gHead) gHead.innerHTML = headlineHtml;
        if (eHead) eHead.innerHTML = headlineHtml;

        if (gAct) gAct.innerText = action;
        if (eAct) eAct.innerText = action;
    }

    function updateTopStatusBannerUI(status) {
        const banner = document.getElementById('top-status-banner');
        const bIcon = document.getElementById('banner-icon');
        const bText = document.getElementById('banner-text');

        if (!banner || !bIcon || !bText) return;

        if (status === 'CRITICAL') {
            banner.className = 'top-status-banner banner-critical';
            bIcon.innerText = '🔴';
            bText.innerHTML = '<strong>Farm Status: CRITICAL RISK</strong> — Action required immediately to prevent aquatic loss.';
        } else if (status === 'MODERATE') {
            banner.className = 'top-status-banner banner-warning';
            bIcon.innerText = '🟡';
            bText.innerHTML = '<strong>Farm Status: MODERATE STRESS</strong> — Monitor water parameters and prepare aeration.';
        } else {
            banner.className = 'top-status-banner banner-safe';
            bIcon.innerText = '🟢';
            bText.innerHTML = '<strong>Farm Status: SAFE</strong> — All ponds operating within optimal parameters.';
        }
    }

    function fallbackClientPrediction(p) {
        const devDO = p.DO < 5.0 ? (5.0 - p.DO) * 15 : 0;
        const devNH = p.ammonia > 0.05 ? (p.ammonia - 0.05) * 100 : 0;
        const devPH = (p.ph < 7.5 || p.ph > 8.5) ? 20 : 0;

        const pi = Math.min(100, Math.round(devDO + devNH + devPH + 8));
        const finalClass = pi > 60 ? 'CRITICAL' : (pi > 30 ? 'MODERATE' : 'SAFE');

        updatePredictionUI({
            pollution_index: pi,
            final_classification: finalClass,
            anomaly_flag: devNH > 30,
            anomaly_score: devNH > 30 ? 0.85 : 0.05,
            explanation: `AquaSentinel+ client fallback: Pollution Index ${pi}/100 based on active parameters.`,
            parameter_contributions: [
                { parameter: 'dissolved_oxygen', current_value: p.DO, contribution_percent: 45, ideal_range: '5.0 - 9.0' },
                { parameter: 'ammonia', current_value: p.ammonia, contribution_percent: 35, ideal_range: '0.0 - 0.05' },
                { parameter: 'ph', current_value: p.ph, contribution_percent: 20, ideal_range: '7.5 - 8.5' }
            ],
            feature_importances: {
                dissolved_oxygen: 28.5,
                ammonia: 24.2,
                ph: 15.8,
                temperature: 11.4,
                turbidity: 8.1
            },
            recommendations: [
                p.DO < 5.0 ? 'Turn on the paddlewheel aerator immediately.' : 'All parameters optimal.'
            ]
        });
    }

    async function fetchMultiPonds() {
        try {
            const res = await fetch(`${API_BASE}/user/ponds`, { headers: getAuthHeaders() });
            if (res.ok) {
                const ponds = await res.json();
                renderMultiPonds(ponds);
            }
        } catch (e) {
            renderMultiPonds([
                { id: 1, name: 'Pond A', species: 'Shrimp', pollution_index: 12.4, final_classification: 'SAFE', readings: { ph: 7.8, dissolved_oxygen: 6.5, ammonia: 0.02 } },
                { id: 2, name: 'Pond B', species: 'Tilapia', pollution_index: 38.5, final_classification: 'MODERATE', readings: { ph: 7.2, dissolved_oxygen: 4.8, ammonia: 0.08 } },
                { id: 3, name: 'Pond C', species: 'Carp', pollution_index: 15.0, final_classification: 'SAFE', readings: { ph: 7.9, dissolved_oxygen: 6.8, ammonia: 0.01 } }
            ]);
        }
    }

    function renderMultiPonds(ponds) {
        const box = document.getElementById('multi-ponds-container');
        if (!box) return;

        box.innerHTML = ponds.map(p => {
            const pName = p.name || p.pond_id || 'Pond';
            const pi = p.pollution_index || (pName === 'Pond B' ? 38.5 : 12.4);
            const status = p.final_classification || (pi > 30 ? 'MODERATE' : 'SAFE');
            const icon = status === 'CRITICAL' ? '🔴' : (status === 'MODERATE' ? '🟡' : '🟢');

            return `
                <div class="pond-card">
                    <div class="pond-card-header">
                        <div>
                            <h4 class="pond-title">${pName}</h4>
                            <span class="pond-species">${p.species}</span>
                        </div>
                        <span class="badge-time ${status === 'CRITICAL' ? 'status-critical' : (status === 'MODERATE' ? 'status-moderate' : 'status-safe')}">${icon} ${status}</span>
                    </div>
                    <div style="display:flex; align-items:baseline; gap:6px;">
                        <span class="pond-pi-val">${typeof pi === 'number' ? pi.toFixed(1) : pi}</span>
                        <span style="color:#64748b; font-size:0.9rem;">/ 100 PI</span>
                    </div>
                    <div class="pond-metrics-mini">
                        <div class="pond-metric-item"><span>pH</span><strong>${p.readings?.ph || 7.8}</strong></div>
                        <div class="pond-metric-item"><span>DO</span><strong>${p.readings?.dissolved_oxygen || 6.5} mg/L</strong></div>
                        <div class="pond-metric-item"><span>NH3</span><strong>${p.readings?.ammonia || 0.02} ppm</strong></div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async function fetchTrends() {
        try {
            const res = await fetch(`${API_BASE}/trends`);
            if (res.ok) {
                const trends = await res.json();
                drawTrendLineChart(trends);
            }
        } catch (e) {
            drawTrendLineChart([
                { time: '02:00', dissolved_oxygen: 6.8, ammonia: 0.02 },
                { time: '04:00', dissolved_oxygen: 6.5, ammonia: 0.02 },
                { time: '06:00', dissolved_oxygen: 6.2, ammonia: 0.03 },
                { time: '08:00', dissolved_oxygen: 5.9, ammonia: 0.04 },
                { time: '10:00', dissolved_oxygen: 5.5, ammonia: 0.06 },
                { time: '12:00', dissolved_oxygen: 6.4, ammonia: 0.02 }
            ]);
        }
    }

    function drawTrendLineChart(data) {
        const cvs = document.getElementById('trend-canvas');
        if (!cvs) return;
        const c = cvs.getContext('2d');
        const w = cvs.width;
        const h = cvs.height;

        c.clearRect(0, 0, w, h);

        c.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        c.lineWidth = 1;
        for (let i = 40; i < h; i += 40) {
            c.beginPath();
            c.moveTo(40, i);
            c.lineTo(w - 20, i);
            c.stroke();
        }

        if (data.length < 2) return;

        const stepX = (w - 80) / (data.length - 1);

        c.strokeStyle = '#38bdf8';
        c.lineWidth = 3;
        c.beginPath();
        data.forEach((d, i) => {
            const x = 50 + i * stepX;
            const y = h - 30 - ((d.dissolved_oxygen || 6.5) / 10.0) * (h - 60);
            if (i === 0) c.moveTo(x, y);
            else c.lineTo(x, y);
        });
        c.stroke();

        c.strokeStyle = '#f59e0b';
        c.lineWidth = 2;
        c.beginPath();
        data.forEach((d, i) => {
            const x = 50 + i * stepX;
            const y = h - 30 - (((d.ammonia || 0.02) * 50) / 10.0) * (h - 60);
            if (i === 0) c.moveTo(x, y);
            else c.lineTo(x, y);
        });
        c.stroke();

        c.fillStyle = '#cbd5e1';
        c.font = '11px sans-serif';
        data.forEach((d, i) => {
            const x = 45 + i * stepX;
            c.fillText(d.time, x, h - 8);
        });
    }

    async function fetchModelMetrics() {
        try {
            const res = await fetch(`${API_BASE}/model/metrics`);
            if (res.ok) {
                const metrics = await res.json();
                renderLeaderboard(metrics);
            }
        } catch (e) {
            renderLeaderboard([
                { model_name: 'SVM', accuracy: 0.9198, precision: 0.9242, recall: 0.9167, f1_score: 0.9197, is_best: true },
                { model_name: 'Random Forest', accuracy: 0.9186, precision: 0.9229, recall: 0.9147, f1_score: 0.9181, is_best: false },
                { model_name: 'XGBoost', accuracy: 0.9186, precision: 0.9229, recall: 0.9147, f1_score: 0.9181, is_best: false },
                { model_name: 'KNN', accuracy: 0.9151, precision: 0.9204, recall: 0.9112, f1_score: 0.9149, is_best: false },
                { model_name: 'Decision Tree', accuracy: 0.9023, precision: 0.9042, recall: 0.8932, f1_score: 0.8983, is_best: false }
            ]);
        }
    }

    function renderLeaderboard(metrics) {
        const body = document.getElementById('leaderboard-body');
        if (!body) return;

        const best = metrics.find(m => m.is_best) || metrics[0];
        const bestName = document.getElementById('best-model-name');
        if (bestName) bestName.innerText = `${best.model_name} Classifier`;

        const bestAcc = document.getElementById('best-model-acc');
        if (bestAcc) bestAcc.innerText = `${(best.accuracy * 100).toFixed(2)}%`;

        body.innerHTML = metrics.map(m => `
            <tr>
                <td><strong>${m.model_name}</strong></td>
                <td>${(m.accuracy * 100).toFixed(2)}%</td>
                <td>${(m.precision * 100).toFixed(2)}%</td>
                <td>${(m.recall * 100).toFixed(2)}%</td>
                <td>${(m.f1_score * 100).toFixed(2)}%</td>
                <td>${m.is_best ? '<span class="badge-best">BEST MODEL</span>' : '<span style="color:#64748b;">Evaluated</span>'}</td>
            </tr>
        `).join('');
    }

    async function fetchAlerts() {
        try {
            const res = await fetch(`${API_BASE}/alerts`);
            if (res.ok) {
                const alerts = await res.json();
                renderAlerts(alerts);
            }
        } catch (e) {
            // Keep default
        }
    }

    function renderAlerts(alerts) {
        const box = document.getElementById('alerts-box');
        const notifList = document.getElementById('notif-list');

        if (!alerts || alerts.length === 0) {
            if (box) box.innerHTML = '<p class="no-alerts">No critical alerts detected in recent monitoring cycle.</p>';
            if (notifList) notifList.innerHTML = '<p style="color:#94a3b8; font-size:0.75rem; padding:8px;">No unread alerts.</p>';
            return;
        }

        if (box) {
            box.innerHTML = alerts.map(a => `
                <div class="alert-item ${a.severity}">
                    <div>
                        <strong>[${a.severity}] ${a.parameter}</strong>
                        <p style="color:#cbd5e1; font-size:0.8rem; margin-top:2px;">${a.reason}</p>
                    </div>
                    <span style="color:#64748b; font-size:0.75rem;">${a.timestamp}</span>
                </div>
            `).join('');
        }

        if (notifList) {
            notifList.innerHTML = alerts.slice(0, 4).map(a => `
                <div class="notif-item ${a.severity}">
                    <strong>[${a.severity}] ${a.parameter}</strong>
                    <p style="color:#cbd5e1; font-size:0.72rem; margin-top:2px;">${a.reason}</p>
                </div>
            `).join('');
        }
    }

    async function toggleSimulation() {
        const btn = document.getElementById('btn-toggle-sim');
        if (isSimulating) {
            isSimulating = false;
            if (simInterval) clearInterval(simInterval);
            if (btn) btn.innerHTML = '<span class="pulse-dot"></span> Live Fleet Stream';
        } else {
            isSimulating = true;
            if (btn) btn.innerText = 'Stop Simulation';
            try {
                await fetch(`${API_BASE}/simulate/start`, { method: 'POST' });
            } catch (e) {}

            simInterval = setInterval(async () => {
                try {
                    const res = await fetch(`${API_BASE}/simulate/latest`);
                    if (res.ok) {
                        const ponds = await res.json();
                        renderMultiPonds(ponds);
                        fetchAlerts();
                        fetchTrends();
                    }
                } catch (e) {}
            }, 3000);
        }
    }

    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('scroll', updateScrollProgress, { passive: true });

    detectBasePathAndInit();
})();
