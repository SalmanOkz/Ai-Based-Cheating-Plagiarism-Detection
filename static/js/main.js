class VisionGuardianApp {
    constructor() {
        this.api = new APIHandler();
        this.ui = new UIHandler();
        this.components = {};
        this.copyPasteMonitor = new CopyPasteMonitor();
        this.state = {
            isProctoring: false,
            aiMode: 'checking',
            riskScore: 0,
            lastUpdate: null,
            clipboardViolations: 0,
            settings: {
                refreshInterval: 2000,
                autoRefresh: true,
                monitorClipboard: true
            }
        };
        
        this.autoRefreshInterval = null;
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing Vision Guardian...');
        
        // Initialize components
        this.components.header = new HeaderComponent(this);
        this.components.video = new VideoComponent(this);
        this.components.analytics = new AnalyticsComponent(this);
        this.components.footer = new FooterComponent(this);
        
        // Check system status
        await this.checkSystemStatus();
        
        // Start auto-refresh if enabled
        if (this.state.settings.autoRefresh) {
            this.startAutoRefresh();
        }
        
        console.log('✅ Vision Guardian initialized');
    }
    
    async checkSystemStatus() {
    try {
        const response = await this.api.getSystemStatus();
        
        // Fix: Check response structure properly
        if (response && response.success === true) {
            this.components.header.updateStatus({
                type: 'connected',
                message: 'System Online'
            });
            this.state.aiMode = response.data?.ai_mode || 'REAL AI';
        } else {
            throw new Error(response?.message || 'System check failed');
        }
    } catch (error) {
        console.error('System status error:', error);
        this.components.header.updateStatus({
            type: 'error',
            message: 'System Offline'
        });
        window.toast.error('System connection failed: ' + error.message);
    }
}
    
    async startProctoring() {
        if (this.state.isProctoring) {
            window.toast.warning('Proctoring already active');
            return;
        }
        
        try {
            console.log('▶️ Starting proctoring...');
            const response = await this.api.startProctoring(0);
            
            if (response.success) {
                this.state.isProctoring = true;
                this.components.video.updateProctoringState(true);
                this.ui.updateProctoringState(true);
                
                if (this.state.settings.monitorClipboard) {
                    this.copyPasteMonitor.start();
                }
                
                this.startAutoRefresh();
                window.toast.success('Proctoring started successfully');
            } else {
                throw new Error(response.message || 'Failed to start proctoring');
            }
        } catch (error) {
            console.error('Start proctoring error:', error);
            window.toast.error('Failed to start proctoring: ' + error.message);
        }
    }
    
    async stopProctoring() {
        if (!this.state.isProctoring) {
            window.toast.warning('Proctoring not active');
            return;
        }
        
        try {
            console.log('⏹️ Stopping proctoring...');
            const response = await this.api.stopProctoring();
            
            if (response.success) {
                this.state.isProctoring = false;
                this.components.video.updateProctoringState(false);
                this.ui.updateProctoringState(false);
                this.copyPasteMonitor.stop();
                this.stopAutoRefresh();
                window.toast.info('Proctoring stopped');
            } else {
                throw new Error(response.message || 'Failed to stop proctoring');
            }
        } catch (error) {
            console.error('Stop proctoring error:', error);
            window.toast.error('Failed to stop proctoring: ' + error.message);
        }
    }
    
    async takeScreenshot() {
        try {
            const response = await this.api.takeScreenshot();
            
            if (response.success) {
                window.toast.success('Screenshot captured: ' + response.data.filename);
            } else {
                throw new Error(response.message || 'Failed to capture screenshot');
            }
        } catch (error) {
            console.error('Screenshot error:', error);
            window.toast.error('Failed to capture screenshot');
        }
    }
    
    async refreshResults() {
        if (!this.state.isProctoring) return;
        
        try {
            const response = await this.api.getProctoringResults();
            
            if (response.success) {
                const results = response.data;
                this.state.riskScore = results.risk_score || 0;
                this.state.lastUpdate = new Date();
                
                this.components.video.updateStats(results);
                this.components.analytics.updateData(results);
            }
        } catch (error) {
            console.error('Refresh results error:', error);
        }
    }
    
    startAutoRefresh() {
        if (this.autoRefreshInterval) return;
        
        const interval = this.state.settings.refreshInterval || 2000;
        this.autoRefreshInterval = setInterval(() => {
            this.refreshResults();
        }, interval);
        
        console.log(`🔄 Auto-refresh started (${interval}ms)`);
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('🔄 Auto-refresh stopped');
        }
    }
    
    showNotification(message, type = 'info') {
        if (this.state.settings.toastEnabled !== false) {
            window.toast[type](message);
        }
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new VisionGuardianApp();
    });
} else {
    window.app = new VisionGuardianApp();
}