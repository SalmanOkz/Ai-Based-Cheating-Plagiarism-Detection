// Footer Component
class FooterComponent {
    constructor(app) {
        this.app = app;
        this.element = null;
        this.init();
    }
    
    init() {
        this.createElement();
        this.render();
        this.setupEventListeners();
    }
    
    createElement() {
        const footer = document.createElement('footer');
        footer.id = 'footer';
        footer.className = 'app-footer';
        
        footer.innerHTML = `
            <div class="footer-content">
                <p>© ${new Date().getFullYear()} Vision Guardian - AI Proctoring System</p>
                <div class="footer-links">
                    <a href="#" class="footer-link" id="helpBtn">
                        <i class="fas fa-question-circle"></i> Help
                    </a>
                    <a href="#" class="footer-link" id="aboutBtn">
                        <i class="fas fa-info-circle"></i> About
                    </a>
                    <a href="#" class="footer-link" id="settingsBtn">
                        <i class="fas fa-cog"></i> Settings
                    </a>
                </div>
            </div>
        `;
        
        this.element = footer;
    }
    
    render() {
        const footerContainer = document.getElementById('footer');
        if (footerContainer) {
            footerContainer.replaceWith(this.element);
        } else {
            document.querySelector('.app-container').appendChild(this.element);
        }
    }
    
    setupEventListeners() {
        // Help button
        const helpBtn = this.element.querySelector('#helpBtn');
        if (helpBtn) {
            helpBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.app.ui.showHelpModal();
            });
        }
        
        // About button
        const aboutBtn = this.element.querySelector('#aboutBtn');
        if (aboutBtn) {
            aboutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showAboutModal();
            });
        }
        
        // Settings button
        const settingsBtn = this.element.querySelector('#settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showSettingsModal();
            });
        }
    }
    
    showAboutModal() {
        const aboutContent = `
            <div class="about-content">
                <div class="about-header">
                    <i class="fas fa-robot fa-2x mb-3" style="color: var(--primary-color);"></i>
                    <h4>Vision Guardian AI Proctoring</h4>
                </div>
                
                <p>Version: 1.0.0</p>
                <p>An intelligent AI-powered system for monitoring exam integrity and preventing cheating.</p>
                
                <div class="features-list mt-3">
                    <h5>Features:</h5>
                    <ul>
                        <li>Real-time gaze tracking</li>
                        <li>Multi-person detection</li>
                        <li>Prohibited item detection</li>
                        <li>Risk assessment scoring</li>
                        <li>Text integrity analysis</li>
                        <li>Code plagiarism detection</li>
                    </ul>
                </div>
                
                <div class="tech-stack mt-3">
                    <h5>Technology Stack:</h5>
                    <div class="tech-badges">
                        <span class="tech-badge">OpenCV</span>
                        <span class="tech-badge">YOLOv8</span>
                        <span class="tech-badge">Flask</span>
                        <span class="tech-badge">TensorFlow</span>
                        <span class="tech-badge">Transformers</span>
                    </div>
                </div>
                
                <div class="disclaimer mt-4">
                    <p><small><em>Note: This is a demonstration system. Actual implementation may vary based on requirements.</em></small></p>
                </div>
            </div>
        `;
        
        this.app.ui.showModal('About Vision Guardian', aboutContent, [
            {
                text: 'Close',
                class: 'btn-primary',
                closeOnClick: true
            }
        ]);
    }
    
    showSettingsModal() {
        const settingsContent = `
            <div class="settings-content">
                <h4>System Settings</h4>
                
                <div class="settings-section">
                    <h5>Auto-refresh Settings</h5>
                    <div class="setting-item">
                        <label class="setting-label">
                            <input type="checkbox" id="autoRefreshToggle" checked>
                            Enable auto-refresh
                        </label>
                    </div>
                    <div class="setting-item">
                        <label class="setting-label">Refresh Interval (ms):</label>
                        <input type="number" id="refreshInterval" value="2000" min="500" max="10000" step="500">
                    </div>
                </div>
                
                <div class="settings-section">
                    <h5>Notifications</h5>
                    <div class="setting-item">
                        <label class="setting-label">
                            <input type="checkbox" id="soundToggle" checked>
                            Enable sound notifications
                        </label>
                    </div>
                    <div class="setting-item">
                        <label class="setting-label">
                            <input type="checkbox" id="toastToggle" checked>
                            Show toast notifications
                        </label>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h5>Display</h5>
                    <div class="setting-item">
                        <label class="setting-label">Theme:</label>
                        <select id="themeSelect">
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                            <option value="auto">Auto (System)</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
        
        const modal = this.app.ui.showModal('System Settings', settingsContent, [
            {
                text: 'Cancel',
                class: 'btn-outline',
                closeOnClick: true
            },
            {
                text: 'Save',
                class: 'btn-primary',
                onClick: () => this.saveSettings()
            }
        ]);
        
        // Load current settings
        this.loadSettingsIntoModal(modal);
    }
    
    loadSettingsIntoModal(modal) {
        // This would load from localStorage or app state
        const settings = this.app.state.settings || {};
        
        // Set form values
        const autoRefreshToggle = modal.querySelector('#autoRefreshToggle');
        const refreshInterval = modal.querySelector('#refreshInterval');
        const soundToggle = modal.querySelector('#soundToggle');
        const toastToggle = modal.querySelector('#toastToggle');
        const themeSelect = modal.querySelector('#themeSelect');
        
        if (autoRefreshToggle) autoRefreshToggle.checked = settings.autoRefresh !== false;
        if (refreshInterval) refreshInterval.value = settings.refreshInterval || 2000;
        if (soundToggle) soundToggle.checked = settings.soundEnabled !== false;
        if (toastToggle) toastToggle.checked = settings.toastEnabled !== false;
        if (themeSelect) themeSelect.value = settings.theme || 'auto';
    }
    
    saveSettings() {
        const modal = document.querySelector('.modal-overlay.show');
        if (!modal) return;
        
        const settings = {
            autoRefresh: modal.querySelector('#autoRefreshToggle').checked,
            refreshInterval: parseInt(modal.querySelector('#refreshInterval').value),
            soundEnabled: modal.querySelector('#soundToggle').checked,
            toastEnabled: modal.querySelector('#toastToggle').checked,
            theme: modal.querySelector('#themeSelect').value
        };
        
        // Save to app state
        this.app.state.settings = settings;
        
        // Apply settings
        if (settings.autoRefresh) {
            this.app.startAutoRefresh();
        } else {
            this.app.stopAutoRefresh();
        }
        
        // Apply theme
        this.applyTheme(settings.theme);
        
        // Show confirmation
        this.app.showNotification('Settings saved', 'success');
    }
    
    applyTheme(theme) {
        const body = document.body;
        
        // Remove existing theme classes
        body.classList.remove('theme-light', 'theme-dark');
        
        if (theme === 'light') {
            body.classList.add('theme-light');
        } else if (theme === 'dark') {
            body.classList.add('theme-dark');
        } else {
            // Auto - let CSS media query handle it
        }
        
        // Save to localStorage
        localStorage.setItem('vision-guardian-theme', theme);
    }
    
    destroy() {
        if (this.element) {
            this.element.remove();
        }
    }
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FooterComponent };
}