        let isTaskRunning = false;
        let _themeInstallPending = false;
        let eventSource = null;
        let taskEventSource = null;
        let _taskStreamConnected = false;
        let _serverShutdown = false;  // bloque les reconnexions SSE apres /api/quit
        let selectedProfiles = new Set();
        let profilesData = {};
        let autoScroll = true;
        const BASE_TITLE = 'MintyForge';

        const ICON_MAP = {
            'box': '📦', 'wrench': '🔧', 'gamepad': '🎮', 'cpu': '🖥️',
            'gpu': '🎛️', 'code': '💻', 'film': '🎬', 'shield': '🛡️', 'server': '🖧',
            'docker': '🐳', 'office': '📝'
        };

        function showToast(message, type) {
            const el = document.createElement('div');
            el.className = 'toast ' + (type || 'info');
            el.textContent = message;
            document.getElementById('toastContainer').appendChild(el);
            setTimeout(() => el.remove(), 4000);
        }

        let _confirmCallback = null;
        function showConfirm(title, message, onOk, danger) {
            document.getElementById('confirmTitle').textContent = title;
            document.getElementById('confirmMessage').textContent = message;
            const btn = document.getElementById('confirmOk');
            btn.classList.toggle('danger', !!danger);
            _confirmCallback = onOk;
            document.getElementById('confirmOverlay').classList.add('active');
        }
        function confirmOk() {
            document.getElementById('confirmOverlay').classList.remove('active');
            if (_confirmCallback) { _confirmCallback(); _confirmCallback = null; }
        }
        function confirmCancel() {
            document.getElementById('confirmOverlay').classList.remove('active');
            _confirmCallback = null;
        }

        function esc(str) {
            if (!str) return '';
            // Couvre les contextes texte HTML, attributs (double et simple quote)
            // et chaines JS injectees dans des attributs onclick='...${esc(x)}...'.
            return String(str)
                .replace(/&/g,  '&amp;')
                .replace(/"/g,  '&quot;')
                .replace(/'/g,  '&#39;')
                .replace(/`/g,  '&#96;')
                .replace(/</g,  '&lt;')
                .replace(/>/g,  '&gt;');
        }

        document.addEventListener('DOMContentLoaded', function() {
            loadTheme();
            updateStatus();
            loadProfiles();
            loadOptionalPackages();
            loadThemeCatalog();
            loadHistory();
            loadFirewall();
            loadGreeterStatus();
            detectLaptop();
            connectLogs();
            connectTaskStream();
            loadLogsHistory();
            setInterval(updateStatus, 5000);
            // Rafraichissement batterie toutes les 30 s
            setInterval(detectLaptop, 30000);
        });

        // Theme
        function toggleTheme() {
            const html = document.documentElement;
            const isDark = html.getAttribute('data-theme') === 'dark';
            html.setAttribute('data-theme', isDark ? 'light' : 'dark');
            document.getElementById('themeIcon').textContent = isDark ? '🌙' : '☀️';
            localStorage.setItem('mintyforge-theme', isDark ? 'light' : 'dark');
        }

        function loadTheme() {
            const saved = localStorage.getItem('mintyforge-theme') || 'light';
            document.documentElement.setAttribute('data-theme', saved);
            document.getElementById('themeIcon').textContent = saved === 'dark' ? '☀️' : '🌙';
        }

        // Status polling
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    updateCheck('status-internet', data.checks.internet);
                    updateCheck('status-sudo', data.checks.sudo);
                    updateCheck('status-python', data.checks.python_version);
                    const tools = data.checks.tools || {};
                    const missing = Object.entries(tools).filter(([,ok]) => !ok).map(([t]) => t);
                    const warn = document.getElementById('toolsWarning');
                    if (missing.length) {
                        warn.textContent = 'Outils manquants : ' + missing.join(', ') + ' — certaines fonctions seront indisponibles.';
                        warn.style.display = '';
                    } else {
                        warn.style.display = 'none';
                    }
                    document.getElementById('count-apt').textContent = data.packages.apt || 0;
                    document.getElementById('count-optional').textContent = data.packages.optional || 0;
                    document.getElementById('count-flatpak').textContent = data.packages.flatpak || 0;
                    const totalThemes = (data.packages.themes_gtk || 0) + (data.packages.themes_icons || 0) + (data.packages.themes_cursors || 0);
                    document.getElementById('count-themes').textContent = totalThemes;
                    const disk = data.checks.disk_free_gb;
                    document.getElementById('disk-free').textContent = disk !== undefined ? disk + ' Go' : '--';
                    const diskItem = document.getElementById('status-disk');
                    diskItem.classList.toggle('ok', disk > 5);
                    diskItem.classList.toggle('error', disk !== undefined && disk <= 5);
                    // L'etat de tache arrive desormais via SSE (connectTaskStream),
                    // mais on garde un fallback sur /api/status au cas ou le flux est coupe.
                    if (!_taskStreamConnected) updateTaskStatus(data.task);
                })
                .catch(err => console.error('Status error:', err));
        }

        function updateCheck(elemId, isOk) {
            const elem = document.getElementById(elemId);
            elem.classList.toggle('ok', isOk);
            elem.classList.toggle('error', !isOk);
            elem.querySelector('.value').textContent = isOk ? '✅' : '❌';
        }

        function updateTaskStatus(task) {
            const taskBar = document.getElementById('taskBar');
            const statusDiv = document.getElementById('taskStatus');
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            const wasRunning = isTaskRunning;

            if (task.running) {
                isTaskRunning = true;
                taskBar.style.display = 'block';
                statusDiv.innerHTML = '<span class="spinner"></span>' + task.name;
                statusDiv.classList.add('running');
                progressBar.style.display = 'block';
                progressFill.style.width = task.progress + '%';
                progressFill.textContent = task.progress + '%';
                document.title = '⏳ ' + task.name + ' - ' + BASE_TITLE;
                document.getElementById('btnCancelTask').style.display = '';
                setAllButtons(true);
            } else {
                document.getElementById('btnCancelTask').style.display = 'none';
                isTaskRunning = false;
                if (task.progress === 100 && task.name) {
                    taskBar.style.display = 'block';
                    statusDiv.textContent = task.name;
                    statusDiv.classList.remove('running');
                    progressBar.style.display = 'block';
                    progressFill.style.width = '100%';
                    progressFill.textContent = '100%';
                    document.title = '✅ ' + task.name + ' - ' + BASE_TITLE;
                } else {
                    taskBar.style.display = 'none';
                    document.title = BASE_TITLE;
                }
                setAllButtons(false);
                // Quand une tache vient de finir
                if (wasRunning) {
                    loadHistory();
                    loadOptionalPackages();
                    if (_themeInstallPending) {
                        _themeInstallPending = false;
                        setTimeout(() => loadThemeCatalog(), 500);
                    }
                }
            }
        }

        function setAllButtons(disabled) {
            document.querySelectorAll('.big-button, .install-profiles-btn, .history-toolbar button').forEach(btn => {
                btn.disabled = disabled;
            });
            // Desactiver aussi les boutons du catalogue de themes
            document.querySelectorAll('#themeCatalogGrid .btn-small').forEach(btn => {
                btn.disabled = disabled;
                if (disabled) {
                    btn.dataset.prevText = btn.textContent;
                    btn.textContent = 'Tache en cours...';
                } else if (btn.dataset.prevText) {
                    btn.textContent = btn.dataset.prevText;
                }
            });
            if (!disabled) {
                document.getElementById('btnInstallProfiles').disabled = selectedProfiles.size === 0;
            }
        }

        // Profiles
        function loadProfiles() {
            const grid = document.getElementById('profilesGrid');
            grid.innerHTML = '<div style="color: var(--text-muted); padding: 10px;">Chargement...</div>';
            fetch('/api/profiles')
                .then(r => r.json())
                .then(data => {
                    if (!data.success) {
                        grid.innerHTML = '<div style="color: var(--danger); padding: 10px;">Erreur : ' + esc(data.error || 'impossible de charger les profils') + '</div>';
                        return;
                    }
                    profilesData = data.profiles;
                    grid.innerHTML = '';
                    for (const [slug, p] of Object.entries(data.profiles)) {
                        const card = document.createElement('div');
                        card.className = 'profile-card';
                        card.dataset.slug = slug;
                        card.dataset.locked = p.locked ? '1' : '0';

                        card.onclick = (e) => {
                            if (e.target.closest('.btn-detail')) return;
                            if (p.locked && card.dataset.unlocked !== '1') {
                                showConfirm(
                                    'Profil non recommande',
                                    'Ce profil est destine a un GPU different de celui detecte. Forcer l\'installation peut causer des conflits. Continuer quand meme ?',
                                    () => { card.dataset.unlocked = '1'; toggleProfile(slug, card); }
                                );
                                return;
                            }
                            toggleProfile(slug, card);
                        };

                        const counts = [];
                        if (p.counts.apt) counts.push(p.counts.apt + ' APT');
                        if (p.counts.flatpak) counts.push(p.counts.flatpak + ' Flatpak');
                        if (p.counts.external) counts.push('⚠️ ' + p.counts.external + ' Externe');
                        if (p.counts.remove) counts.push(p.counts.remove + ' Suppr.');

                        const badgeHtml = p.suggested
                            ? '<div class="badge-suggested">Recommande</div>'
                            : (p.locked ? '<div class="badge-suggested" style="background: #64748b;">🔒 GPU different</div>' : '');

                        card.innerHTML = `
                            <div class="check-mark"></div>
                            ${badgeHtml}
                            <div class="profile-icon" style="${p.locked ? 'opacity:0.5' : ''}">${ICON_MAP[p.icon] || '📦'}</div>
                            <div class="profile-name" style="${p.locked ? 'opacity:0.6' : ''}">${p.name}</div>
                            <div class="profile-desc" style="${p.locked ? 'opacity:0.6' : ''}">${p.description}</div>
                            <div class="profile-counts">
                                ${counts.map(c => '<span>' + c + '</span>').join('')}
                            </div>
                            <button class="btn-detail" onclick="showProfileDetail('${slug}')" title="Voir le detail">Detail &#8594;</button>
                        `;
                        if (p.locked) card.style.borderColor = '#94a3b8';
                        grid.appendChild(card);

                        if (p.suggested) toggleProfile(slug, card);
                    }
                })
                .catch(err => {
                    document.getElementById('profilesGrid').innerHTML =
                        '<div style="color: var(--danger); padding: 10px;">Erreur reseau — verifiez que le serveur tourne.</div>';
                });
        }

        function toggleProfile(slug, card) {
            if (isTaskRunning) return;
            if (selectedProfiles.has(slug)) {
                selectedProfiles.delete(slug);
                card.classList.remove('selected');
                card.querySelector('.check-mark').textContent = '';
            } else {
                selectedProfiles.add(slug);
                card.classList.add('selected');
                card.querySelector('.check-mark').textContent = '✓';
            }
            updateProfileButton();
        }

        function selectAllProfiles() {
            if (isTaskRunning) return;
            document.querySelectorAll('.profile-card').forEach(card => {
                selectedProfiles.add(card.dataset.slug);
                card.classList.add('selected');
                card.querySelector('.check-mark').textContent = '✓';
            });
            updateProfileButton();
        }

        function deselectAllProfiles() {
            document.querySelectorAll('.profile-card').forEach(card => {
                card.classList.remove('selected');
                card.querySelector('.check-mark').textContent = '';
            });
            selectedProfiles.clear();
            updateProfileButton();
        }

        function updateProfileButton() {
            const btn = document.getElementById('btnInstallProfiles');
            const sub = document.getElementById('profilesBtnSub');
            const count = selectedProfiles.size;
            btn.disabled = count === 0 || isTaskRunning;
            if (count === 0) {
                sub.textContent = 'Aucun profil selectionne';
            } else {
                let total = 0;
                selectedProfiles.forEach(s => { if (profilesData[s]) total += profilesData[s].counts.total; });
                sub.textContent = count + ' profil' + (count > 1 ? 's' : '') + ' — ' + total + ' packages';
            }
        }

        function installProfiles() {
            if (isTaskRunning || selectedProfiles.size === 0) return;
            const slugs = Array.from(selectedProfiles);
            const names = slugs.map(s => profilesData[s] ? profilesData[s].name : s);
            showConfirm(
                'Installer les profils ?',
                names.join(', ') + ' — cela peut prendre plusieurs minutes.',
                () => _doInstallProfiles(slugs, names)
            );
        }
        function _doInstallProfiles(slugs, names) {
            fetch('/api/profiles/install', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({profiles: slugs})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) addLog('Installation demarree: ' + names.join(', '));
                else showToast('Erreur : ' + data.error, 'error');
            })
            .catch(err => showToast('Erreur reseau : ' + err, 'error'));
        }

        function closeModal() {
            document.getElementById('modalOverlay').classList.remove('active');
            document.getElementById('modalFooter').style.display = 'none';
        }
        function closeModalOutside(e) { if (e.target === document.getElementById('modalOverlay')) closeModal(); }

        // =============================================
        // SLICK-GREETER
        // =============================================
        function loadGreeterStatus() {
            fetch('/api/greeter/status')
                .then(r => r.json())
                .then(data => {
                    const el = document.getElementById('greeterStatus');
                    if (!data.success) { el.textContent = 'Impossible de lire slick-greeter (crudini/sudo disponible ?)'; return; }
                    const c = data.current;
                    const lines = [
                        ['Theme GTK',  c['theme-name']],
                        ['Icones',     c['icon-theme-name']],
                        ['Curseur',    c['cursor-theme-name']],
                        ['Police',     c['font-name']],
                        ['Numlock',    c['activate-numlock']],
                        ['Fond',       c['background']],
                    ];
                    el.innerHTML = lines
                        .filter(([, v]) => v)
                        .map(([k, v]) => `<span style="margin-right:18px;"><b>${k}</b> : ${esc(v)}</span>`)
                        .join('') || 'Aucune configuration detectee (fichier vide ou absent)';
                })
                .catch(() => { document.getElementById('greeterStatus').textContent = 'Erreur reseau'; });
        }

        function greeterSync() {
            showConfirm(
                'Synchroniser le greeter ?',
                'Les themes, icones, curseur, police et numlock seront appliques a l\'ecran de connexion.',
                () => {
                    fetch('/api/greeter/sync', { method: 'POST' })
                        .then(r => r.json())
                        .then(data => {
                            if (data.applied && data.applied.length > 0) {
                                showToast('Greeter synchronise (' + data.applied.length + ' parametres)', 'success');
                                addLog('Slick-greeter : ' + data.applied.join(', '));
                            }
                            if (data.warnings && data.warnings.length > 0) {
                                data.warnings.forEach(w => {
                                    showToast(w, 'warning');
                                    addLog('[WARN] Greeter : ' + w);
                                });
                            }
                            if (data.errors && data.errors.length > 0) {
                                showToast('Echecs greeter : ' + data.errors.join(', '), 'error');
                            }
                            loadGreeterStatus();
                        })
                        .catch(err => showToast('Erreur reseau : ' + err, 'error'));
                }
            );
        }

        // Pare-feu
        function loadFirewall() {
            fetch('/api/system/firewall')
                .then(r => r.json())
                .then(data => {
                    const el = document.getElementById('firewallStatus');
                    const out = document.getElementById('firewallOutput');
                    if (!data.success) {
                        el.textContent = 'Non disponible';
                        el.style.color = 'var(--text-muted)';
                        return;
                    }
                    el.textContent = data.enabled ? 'Actif' : 'Inactif';
                    el.style.color = data.enabled ? 'var(--success)' : 'var(--danger)';
                    if (data.output) {
                        out.textContent = data.output;
                        out.style.display = 'block';
                    }
                })
                .catch(() => {
                    document.getElementById('firewallStatus').textContent = 'Non disponible';
                });
        }

        function firewallEnable() {
            showConfirm('Activer le pare-feu ?', 'ufw sera active avec les regles par defaut.', () => {
                fetch('/api/system/firewall/enable', { method: 'POST' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) { loadFirewall(); showToast('Pare-feu active', 'success'); }
                        else showToast('Erreur : ' + data.error, 'error');
                    })
                    .catch(err => showToast('Erreur reseau : ' + err, 'error'));
            });
        }

        function firewallDisable() {
            showConfirm('Desactiver le pare-feu ?', 'Le systeme ne sera plus protege par ufw.', () => {
                fetch('/api/system/firewall/disable', { method: 'POST' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) { loadFirewall(); showToast('Pare-feu desactive', 'warning'); }
                        else showToast('Erreur : ' + data.error, 'error');
                    })
                    .catch(err => showToast('Erreur reseau : ' + err, 'error'));
            }, true);
        }

        function loadLogsHistory() {
            fetch('/api/logs/history')
                .then(r => r.json())
                .then(data => {
                    if (!data.lines || !data.lines.length) return;
                    const container = document.getElementById('logsContainer');
                    container.innerHTML = '';
                    data.lines.forEach(line => {
                        const el = document.createElement('div');
                        el.className = 'log-line';
                        el.textContent = line;
                        container.appendChild(el);
                    });
                    container.scrollTop = container.scrollHeight;
                })
                .catch(() => {});
        }

        function cancelTask() {
            showConfirm(
                'Annuler la tache en cours ?',
                'Le processus sera interrompu immediatement.',
                () => {
                    fetch('/api/task/cancel', { method: 'POST' })
                        .then(r => r.json())
                        .then(data => {
                            if (data.success) addLog('Tache annulee.');
                            else showToast('Rien a annuler.', 'warning');
                        })
                        .catch(err => showToast('Erreur : ' + err, 'error'));
                },
                true
            );
        }

        // Logs SSE
        function connectLogs() {
            if (_serverShutdown) return;
            if (eventSource) eventSource.close();
            const indicator = document.getElementById('sseIndicator');
            eventSource = new EventSource('/api/logs/stream');
            eventSource.onopen = () => { indicator.className = 'sse-indicator connected'; };
            eventSource.onmessage = function(event) {
                if (event.data === '__shutdown__') {
                    _serverShutdown = true;
                    try { eventSource.close(); } catch (e) {}
                    return;
                }
                indicator.className = 'sse-indicator connected';
                const container = document.getElementById('logsContainer');
                const line = document.createElement('div');
                line.className = 'log-line';
                line.textContent = event.data;
                container.appendChild(line);
                if (autoScroll) container.scrollTop = container.scrollHeight;
                while (container.children.length > 500) container.removeChild(container.firstChild);
            };
            eventSource.onerror = () => {
                indicator.className = 'sse-indicator disconnected';
                if (!_serverShutdown) setTimeout(connectLogs, 5000);
            };
        }

        // Task progress SSE (remplace le polling /api/status pour la tache)
        function connectTaskStream() {
            if (_serverShutdown) return;
            if (taskEventSource) { try { taskEventSource.close(); } catch (e) {} }
            taskEventSource = new EventSource('/api/task/stream');
            taskEventSource.onopen = () => { _taskStreamConnected = true; };
            taskEventSource.onmessage = (event) => {
                try {
                    const task = JSON.parse(event.data);
                    if (task && task.__shutdown__) {
                        _serverShutdown = true;
                        try { taskEventSource.close(); } catch (e) {}
                        return;
                    }
                    updateTaskStatus(task);
                } catch (e) { /* keepalive ou JSON invalide */ }
            };
            taskEventSource.onerror = () => {
                _taskStreamConnected = false;
                try { taskEventSource.close(); } catch (e) {}
                if (!_serverShutdown) setTimeout(connectTaskStream, 5000);
            };
        }

        function clearLogs() {
            document.getElementById('logsContainer').innerHTML = '';
            fetch('/api/logs/clear', { method: 'POST' });
        }

        function toggleAutoScroll() {
            autoScroll = !autoScroll;
            document.getElementById('btnAutoScroll').textContent = 'Auto-scroll: ' + (autoScroll ? 'ON' : 'OFF');
        }

        function addLog(message) {
            const container = document.getElementById('logsContainer');
            const line = document.createElement('div');
            line.className = 'log-line';
            line.textContent = new Date().toLocaleTimeString() + ' - ' + message;
            container.appendChild(line);
            if (autoScroll) container.scrollTop = container.scrollHeight;
        }

        // =============================================
        // CATALOGUE DE THEMES
        // =============================================
        let _themeCatalog = {};
        let _currentThemeTab = 'gtk';

        function reloadAllThemes() {
            showToast('Rechargement des themes...', 'info');
            loadThemeCatalog();
        }

        // --- Paquets optionnels ---
        function loadOptionalPackages() {
            const grid = document.getElementById('optionalGrid');
            grid.innerHTML = '<div style="color: var(--text-muted);">Chargement...</div>';
            fetch('/api/optional/list')
                .then(r => r.json())
                .then(data => {
                    if (!data.packages || data.packages.length === 0) {
                        grid.innerHTML = '<div style="color: var(--text-muted);">Aucun paquet optionnel configure.</div>';
                        return;
                    }
                    grid.innerHTML = data.packages.map(pkg => {
                        const status = pkg.installed
                            ? '<span style="color: var(--success); font-weight: bold;">installe</span>'
                            : '<span style="color: var(--text-muted);">non installe</span>';
                        return `<div style="background: var(--light); border-radius: 8px; padding: 10px 14px; border: 1px solid var(--border);">
                            <div style="font-weight: 600; font-size: 0.92em;">${esc(pkg.name)}</div>
                            <div style="font-size: 0.82em; color: var(--text-muted);">${esc(pkg.description)}</div>
                            <div style="font-size: 0.8em; margin-top: 4px;">${status}</div>
                        </div>`;
                    }).join('');
                })
                .catch(() => {
                    grid.innerHTML = '<div style="color: var(--danger);">Erreur de chargement.</div>';
                });
        }

        function installOptional() {
            if (isTaskRunning) { showToast('Une tache est deja en cours', 'warning'); return; }
            showConfirm('Paquets optionnels', 'Installer tous les paquets optionnels non presents ?', () => {
                fetch('/api/execute/optional_install', { method: 'POST' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) showToast('Installation optionnelle lancee', 'success');
                        else showToast(data.error || 'Erreur', 'error');
                    })
                    .catch(() => showToast('Erreur reseau', 'error'));
            });
        }

        function _showQuitPage() {
            _serverShutdown = true;
            document.body.innerHTML =
                '<div class="quit-page">' +
                    '<div class="quit-page-inner">' +
                        '<h2>MintyForge ferme.</h2>' +
                        '<p>Vous pouvez fermer cet onglet.</p>' +
                    '</div>' +
                '</div>';
        }

        function quitApp() {
            showConfirm('Quitter', 'Fermer MintyForge ?', () => {
                fetch('/api/quit', { method: 'POST' })
                    .then(_showQuitPage)
                    .catch(_showQuitPage);
            });
        }

        function loadThemeCatalog() {
            document.getElementById('themeCatalogGrid').innerHTML = '<div style="color: var(--text-muted);">Chargement...</div>';
            fetch('/api/themes/catalog')
                .then(r => r.json())
                .then(data => {
                    if (!data.success) return;
                    _themeCatalog = data.catalog;
                    renderThemeTab(_currentThemeTab);
                })
                .catch(() => {
                    document.getElementById('themeCatalogGrid').innerHTML = '<div style="color: var(--danger);">Erreur chargement catalogue</div>';
                });
        }

        function switchThemeTab(type) {
            _currentThemeTab = type;
            ['gtk', 'icon', 'cursor'].forEach(t => {
                const btn = document.getElementById('themeTab' + t.charAt(0).toUpperCase() + t.slice(1));
                if (btn) btn.classList.toggle('theme-tab-active', t === type);
            });
            renderThemeTab(type);
        }

        function renderThemeTab(type) {
            const grid = document.getElementById('themeCatalogGrid');
            const hideInstalled = document.getElementById('themeHideInstalled')?.checked;
            let themes = (_themeCatalog[type] || []);
            if (hideInstalled) themes = themes.filter(t => !t.installed);
            if (!themes.length) {
                grid.innerHTML = '<div style="color: var(--text-muted);">' + (hideInstalled ? 'Tous les themes de ce catalogue sont deja installes.' : 'Aucun theme dans ce catalogue.') + '</div>';
                return;
            }
            grid.innerHTML = '';
            themes.forEach(t => {
                const card = document.createElement('div');
                card.style.cssText = 'background: var(--card-bg); border-radius: 12px; padding: 16px; box-shadow: var(--card-shadow); display: flex; flex-direction: column; gap: 8px;';
                const statusColor = t.installed ? 'var(--success)' : 'var(--text-muted)';
                const statusLabel = t.installed ? 'Installe' : 'Non installe';
                const canInstall  = t.has_url && !t.installed;
                card.innerHTML = `
                    <div style="font-weight: 600; font-size: 0.95em; color: var(--dark);">${esc(t.name)}</div>
                    <div style="font-size: 0.82em; color: var(--text-muted);">${esc(t.description)}</div>
                    <div style="font-size: 0.8em; color: ${statusColor}; font-weight: 500;">${statusLabel}</div>
                    ${canInstall
                        ? `<button class="btn-small" style="margin-top: auto;" onclick="installTheme('${type}', '${esc(t.name)}', this)">
                               Installer → /usr/share
                           </button>`
                        : `<button class="btn-small" style="margin-top: auto; opacity: 0.4; cursor: not-allowed;" disabled>${t.installed ? 'Deja installe' : 'Inclus systeme'}</button>`
                    }
                `;
                grid.appendChild(card);
            });
        }

        function installTheme(type, name, btn) {
            if (isTaskRunning) { showToast('Une tache est en cours', 'warning'); return; }
            const system = document.getElementById('themeSystemInstall')?.checked || false;
            _themeInstallPending = true;   // positionner avant le fetch pour eviter la race condition SSE
            btn.disabled = true;
            btn.textContent = system ? 'Install. systeme...' : 'Installation...';
            fetch('/api/themes/install', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type, name, system})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showToast('Installation de "' + name + '" lancee', 'success');
                    addLog('Theme : installation de ' + name + ' lancee');
                } else {
                    _themeInstallPending = false;
                    showToast('Erreur : ' + data.error, 'error');
                    btn.disabled = false;
                    btn.textContent = 'Installer';
                }
            })
            .catch(err => { _themeInstallPending = false; showToast('Erreur reseau : ' + err, 'error'); btn.disabled = false; btn.textContent = 'Installer'; });
        }

        // =============================================
        // INSTALLATION PERSONNALISEE DEPUIS MODAL
        // =============================================
        let _modalProfileSlug = null;

        function showProfileDetail(slug) {
            _modalProfileSlug = slug;
            fetch('/api/profiles/' + slug)
                .then(r => r.json())
                .then(data => {
                    if (!data.success) return;
                    const p = data.profile;
                    document.getElementById('modalTitle').textContent = (ICON_MAP[p.icon] || '') + ' ' + p.name;
                    document.getElementById('modalDesc').textContent = p.description;

                    let html = '';
                    const sections = [
                        ['apt',      'APT',        'name', true],
                        ['flatpak',  'Flatpak',    'app',  true],
                        ['external', 'Externe',    'name', true],
                        ['remove',   'Suppression','name', false],
                    ];
                    sections.forEach(([key, label, nameField, checkable]) => {
                        if (!p[key].length) return;
                        const extWarning = (key === 'external' && p[key].some(e => !e.config))
                            ? '<div style="background:#fff3cd;border-left:3px solid #f0ad4e;border-radius:5px;padding:7px 11px;margin-bottom:8px;font-size:0.82em;color:#856404;">⚠️ <strong>Paquets externes</strong> — ces commandes installent depuis des depots tiers (non officiels). Verifiez les sources avant d\'installer.</div>'
                            : '';
                        html += '<div class="pkg-section"><h4>' + label + ' (' + p[key].length + ')</h4>' + extWarning + '<ul class="pkg-list">';
                        p[key].forEach((pkg, i) => {
                            const id = 'mpkg_' + key + '_' + i;
                            const pkgName = pkg[nameField];
                            if (checkable) {
                                html += `<li style="display:flex; align-items:center; gap: 8px;">
                                    <input type="checkbox" id="${id}" data-type="${key}" data-idx="${i}" checked style="cursor:pointer; width:15px; height:15px; flex-shrink:0;">
                                    <label for="${id}" style="cursor:pointer; flex:1;">
                                        <span class="pkg-name">${esc(pkgName)}</span>
                                        <span class="pkg-desc">${esc(pkg.description)}</span>
                                    </label>
                                </li>`;
                            } else {
                                html += '<li><span class="pkg-name">' + esc(pkgName) + '</span><span class="pkg-desc">' + esc(pkg.description) + '</span></li>';
                            }
                        });
                        html += '</ul></div>';
                    });
                    // Stocker le profil pour install-custom
                    document.getElementById('modalContent').innerHTML = html;
                    document.getElementById('modalContent').dataset.profile = JSON.stringify(p);
                    document.getElementById('modalFooter').style.display = 'flex';
                    document.getElementById('modalOverlay').classList.add('active');
                });
        }

        function checkAllModalPkgs(checked) {
            document.querySelectorAll('#modalContent input[type=checkbox]').forEach(cb => { cb.checked = checked; });
        }

        function installCustomFromModal() {
            if (isTaskRunning) { showToast('Une tache est en cours', 'warning'); return; }
            const p = JSON.parse(document.getElementById('modalContent').dataset.profile || '{}');
            const checked = {};
            document.querySelectorAll('#modalContent input[type=checkbox]:checked').forEach(cb => {
                const type = cb.dataset.type;
                const idx  = parseInt(cb.dataset.idx);
                if (!checked[type]) checked[type] = [];
                checked[type].push(idx);
            });
            // On envoie seulement les noms ; le serveur resout les commandes
            // depuis le profil canonique (defense en profondeur contre l'injection).
            const apt      = (checked.apt      || []).map(i => p.apt[i].name);
            const flatpak  = (checked.flatpak  || []).map(i => p.flatpak[i].app);
            const external = (checked.external || []).map(i => p.external[i].name);
            const remove   = (p.remove || []).map(r => r.name);  // suppression: toujours tout

            if (!apt.length && !flatpak.length && !external.length) {
                showToast('Aucun paquet coche', 'warning');
                return;
            }
            const total = apt.length + flatpak.length + external.length;
            const slug  = _modalProfileSlug;

            // Fermer le modal de detail AVANT d'afficher la confirmation
            closeModal();
            // Deselectionner le profil de la grille pour eviter double-install
            if (slug) {
                selectedProfiles.delete(slug);
                const card = document.querySelector('.profile-card[data-slug="' + slug + '"]');
                if (card) { card.classList.remove('selected'); card.querySelector('.check-mark').textContent = ''; }
                updateProfileButton();
            }

            showConfirm(
                'Installer la selection ?',
                total + ' paquet(s) selectionne(s) du profil.',
                () => {
                    fetch('/api/profiles/install-custom', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({slug, apt, flatpak, external, remove})
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) addLog('Installation personnalisee lancee (' + total + ' paquets)');
                        else showToast('Erreur : ' + data.error, 'error');
                    })
                    .catch(err => showToast('Erreur reseau : ' + err, 'error'));
                }
            );
        }

        // Historique & Rollback
        function loadHistory() {
            fetch('/api/state')
                .then(r => r.json())
                .then(data => {
                    if (!data.success) return;
                    const container = document.getElementById('historyContent');
                    const summaryEl = document.getElementById('historySummary');

                    if (!data.history.length) {
                        container.innerHTML = '<div class="history-empty">Aucune action enregistree</div>';
                        summaryEl.style.display = 'none';
                        return;
                    }

                    // Afficher le resume
                    const s = data.summary || {};
                    const parts = [];
                    if (s.total)      parts.push(s.total + ' action(s)');
                    if (s.success)    parts.push(s.success + ' reussies');
                    if (s.failed)     parts.push(s.failed + ' echouees');
                    if (s.rollbackable) parts.push(s.rollbackable + ' annulables');
                    summaryEl.textContent = parts.join(' · ');
                    summaryEl.style.display = 'block';

                    let html = '<ul class="history-list">';
                    data.history.slice().reverse().forEach(entry => {
                        const date = new Date(entry.timestamp).toLocaleString('fr-FR', {
                            hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit'
                        });
                        let badge;
                        if (entry.metadata && entry.metadata.rolled_back) {
                            badge = '<span class="hi-badge rollback">annule</span>';
                        } else if (entry.success) {
                            badge = '<span class="hi-badge ok">ok</span>';
                        } else {
                            badge = '<span class="hi-badge fail">echec</span>';
                        }
                        html += `<li class="history-item">
                            <span class="hi-action">${esc(entry.action)}</span>
                            <span class="hi-target">${esc(entry.target)}</span>
                            ${badge}
                            <span class="hi-time">${date}</span>
                        </li>`;
                    });
                    html += '</ul>';
                    container.innerHTML = html;
                })
                .catch(err => console.error('History error:', err));
        }

        function rollbackLast() {
            if (isTaskRunning) return showToast('Une tache est en cours', 'warning');
            showConfirm('Annuler la derniere action ?', 'Cette operation est irreversible.', () => {
                fetch('/api/state/rollback/last', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.success) addLog('Rollback lance');
                    else showToast('Erreur : ' + data.error, 'error');
                })
                .catch(err => showToast('Erreur reseau : ' + err, 'error'));
            });
        }

        function rollbackAll() {
            if (isTaskRunning) return showToast('Une tache est en cours', 'warning');
            showConfirm('Tout annuler ?', 'Toutes les actions enregistrees seront annulees.', () => {
                fetch('/api/state/rollback/all', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.success) addLog('Rollback total lance');
                    else showToast('Erreur : ' + data.error, 'error');
                })
                .catch(err => showToast('Erreur reseau : ' + err, 'error'));
            }, true);
        }

        function clearHistory() {
            if (isTaskRunning) return showToast('Une tache est en cours', 'warning');
            showConfirm('Effacer l\'historique ?', 'Aucun rollback ne sera effectue. L\'historique sera perdu.', () => {
                fetch('/api/state/clear', { method: 'DELETE' })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        loadHistory();
                        showToast('Historique efface', 'info');
                    }
                    else showToast('Erreur : ' + data.error, 'error');
                })
                .catch(err => showToast('Erreur reseau : ' + err, 'error'));
            }, true);
        }

        // Dry-run / Export / Import
        function dryRunProfiles() {
            if (selectedProfiles.size === 0) return showToast('Aucun profil selectionne.', 'warning');
            fetch('/api/profiles/dry-run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({profiles: Array.from(selectedProfiles)})
            })
            .then(r => r.json())
            .then(data => {
                if (!data.success) return showToast('Erreur: ' + data.error, 'error');
                const STATUS_LABELS = { to_install: 'A installer', installed: 'Deja installe', duplicate: 'Doublon', absent: 'Absent' };
                let html = '';
                for (const [slug, entry] of Object.entries(data.dry_run)) {
                    const pName = profilesData[slug] ? profilesData[slug].name : slug;
                    html += '<div class="pkg-section"><h4>' + pName + '</h4><ul class="pkg-list">';
                    ['apt', 'flatpak', 'external', 'remove'].forEach(cat => {
                        entry[cat].forEach(pkg => {
                            const name = pkg.name || pkg.app;
                            html += '<li><span class="pkg-name">' + name + '</span>'
                                + '<span class="pkg-status ' + pkg.status + '">' + STATUS_LABELS[pkg.status] + '</span></li>';
                        });
                    });
                    html += '</ul></div>';
                }
                document.getElementById('modalTitle').textContent = 'Apercu (dry-run)';
                document.getElementById('modalDesc').textContent = selectedProfiles.size + ' profil(s)';
                document.getElementById('modalContent').innerHTML = html;
                document.getElementById('modalOverlay').classList.add('active');
            })
            .catch(err => showToast('Erreur reseau: ' + err, 'error'));
        }

        function exportProfiles() {
            if (selectedProfiles.size === 0) return showToast('Aucun profil selectionne.', 'warning');
            const blob = new Blob([JSON.stringify({profiles: Array.from(selectedProfiles)}, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'mintyforge_profiles.json';
            a.click();
            URL.revokeObjectURL(url);
            addLog('Selection exportee: ' + Array.from(selectedProfiles).join(', '));
        }

        function importProfiles() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = function(e) {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = function(ev) {
                    try {
                        const data = JSON.parse(ev.target.result);
                        if (!data.profiles || !Array.isArray(data.profiles)) {
                            return showToast('Fichier invalide : pas de liste "profiles".', 'error');
                        }
                        fetch('/api/profiles/import', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({profiles: data.profiles})
                        })
                        .then(r => r.json())
                        .then(resp => {
                            if (!resp.success) return showToast('Erreur: ' + resp.error, 'error');
                            deselectAllProfiles();
                            resp.profiles.forEach(slug => {
                                const card = document.querySelector('.profile-card[data-slug="' + slug + '"]');
                                if (card) toggleProfile(slug, card);
                            });
                            if (resp.invalid.length) addLog('Profils ignores : ' + resp.invalid.join(', '));
                            addLog('Selection importee : ' + resp.profiles.join(', '));
                        });
                    } catch (err) {
                        showToast('Fichier JSON invalide.', 'error');
                    }
                };
                reader.readAsText(file);
            };
            input.click();
        }

        // ─── Laptop ─────────────────────────────────────────────────────

        const _BATTERY_STATUS_FR = {
            'charging':       'en charge',
            'discharging':    'en decharge',
            'full':           'pleine',
            'not charging':   'branche, pas en charge',
            'unknown':        'inconnu',
        };

        function detectLaptop() {
            fetch('/api/laptop/detect')
                .then(r => r.json())
                .then(data => {
                    const banner = document.getElementById('laptopBatteryBanner');
                    if (!banner) return;
                    if (!data.is_laptop) { banner.style.display = 'none'; return; }

                    const bat = data.battery || {};
                    const pct = (bat.capacity !== undefined) ? bat.capacity : null;
                    const rawStatus = (typeof bat.status === 'string') ? bat.status : '';
                    const statusFr = _BATTERY_STATUS_FR[rawStatus.toLowerCase()] || rawStatus;
                    const onAc = /^(charging|full|not charging)$/i.test(rawStatus);
                    const lowBattery = pct !== null && pct < 30 && !onAc;

                    banner.classList.remove('battery-ok', 'battery-warn', 'battery-low');
                    if (lowBattery)       banner.classList.add('battery-low');
                    else if (!onAc)       banner.classList.add('battery-warn');
                    else                  banner.classList.add('battery-ok');

                    let html = '<strong>PC portable detecte.</strong> ';
                    if (pct !== null) {
                        html += 'Batterie : <strong>' + pct + '%</strong>';
                        if (statusFr) html += ' (' + esc(statusFr) + ')';
                        html += '. ';
                    }
                    if (lowBattery) {
                        html += 'Batterie faible : branchez imperativement l\'ordinateur sur secteur avant toute installation ou modification systeme.';
                    } else if (!onAc) {
                        html += 'Il est preferable de brancher l\'ordinateur sur secteur avant d\'installer des paquets ou d\'appliquer des modifications systeme.';
                    } else {
                        html += 'L\'ordinateur est branche sur secteur, vous pouvez continuer en toute securite.';
                    }
                    banner.innerHTML = html;
                    banner.style.display = '';
                })
                .catch(() => {});
        }

