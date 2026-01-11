class VisionGuardianApp {
    constructor() {
        this.api = new APIHandler();
        this.ui = new UIHandler();
        this.components = {};
        this.copyPasteMonitor = new CopyPasteMonitor(); // NEW: Copy-paste monitoring
        this.state = {
            isProctoring: false,
            aiMode: 'checking',
            riskScore: 0,
            lastUpdate: null,
            clipboardViolations: 0, // NEW: Track clipboard violations
            settings: {
                refreshInterval: 2000,
                autoRefresh: true,
                monitorClipboard: true // NEW: Enable clipboard monitoring
            }
        };
        
        this.init();
    }
}