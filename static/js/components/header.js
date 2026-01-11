// Header Component
class HeaderComponent {
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
        const header = document.createElement('header');
        header.id = 'header';
        header.className = 'app-header';
        
        header.innerHTML = `
            <div class="logo-container">
                <div class="logo-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="logo-text">
                    <h1>Vision Guardian AI Proctoring</h1>
                    <p>Intelligent Exam Monitoring System</p>
                </div>
            </div>
            <div class="connection-status" id="connectionStatus">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">Initializing...</span>
            </div>
        `;
        
        this.element = header;
    }
    
    render() {
        const headerContainer = document.getElementById('header');
        if (headerContainer) {
            headerContainer.replaceWith(this.element);
        } else {
            document.querySelector('.app-container').prepend(this.element);
        }
    }
    
    setupEventListeners() {
        // Connection status click handler
        const statusElement = this.element.querySelector('.connection-status');
        if (statusElement) {
            statusElement.addEventListener('click', () => {
                this.app.checkSystemStatus();
            });
        }
    }
    
    updateStatus(status) {
        const statusDot = this.element.querySelector('#statusDot');
        const statusText = this.element.querySelector('#statusText');
        
        if (!statusDot || !statusText) return;
        
        // Reset classes
        statusDot.className = 'status-dot';
        statusText.textContent = status.message || 'Unknown';
        
        // Add appropriate class
        switch (status.type) {
            case 'connected':
                statusDot.classList.add('connected');
                break;
            case 'warning':
                statusDot.classList.add('warning');
                break;
            case 'error':
                statusDot.classList.add('danger');
                break;
            default:
                break;
        }
    }
    
    destroy() {
        if (this.element) {
            this.element.remove();
        }
    }
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HeaderComponent };
}