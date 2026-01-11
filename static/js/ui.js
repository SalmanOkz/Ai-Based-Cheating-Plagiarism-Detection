// UI Handler Class
class UIHandler {
    constructor() {
        this.elements = {};
        this.animations = new Map();
        this.init();
    }
    
    init() {
        // Cache DOM elements
        this.cacheElements();
        
        // Initialize animations
        this.setupAnimations();
        
        // Setup global event handlers
        this.setupGlobalHandlers();
    }
    
    cacheElements() {
        // Cache frequently used elements
        this.elements = {
            body: document.body,
            appContainer: document.querySelector('.app-container'),
            videoFeed: document.getElementById('videoFeed'),
            startBtn: document.getElementById('startBtn'),
            stopBtn: document.getElementById('stopBtn'),
            screenshotBtn: document.getElementById('screenshotBtn'),
            refreshBtn: document.getElementById('refreshStatus'),
            helpBtn: document.getElementById('helpBtn')
        };
    }
    
    setupAnimations() {
        // Setup CSS animations
        this.animations.set('fadeIn', 'animate-fade-in');
        this.animations.set('slideRight', 'animate-slide-right');
        this.animations.set('slideLeft', 'animate-slide-left');
    }
    
    setupGlobalHandlers() {
        // Handle clicks on disabled buttons
        document.addEventListener('click', (e) => {
            if (e.target.disabled) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                e.preventDefault();
            }
        });
    }
    
    setLoading(isLoading, element = null) {
        if (element) {
            if (isLoading) {
                element.classList.add('loading');
                element.disabled = true;
            } else {
                element.classList.remove('loading');
                element.disabled = false;
            }
        } else {
            // Global loading state
            if (isLoading) {
                this.elements.body.classList.add('loading');
            } else {
                this.elements.body.classList.remove('loading');
            }
        }
    }
    
    updateProctoringState(isActive) {
        const { startBtn, stopBtn, screenshotBtn } = this.elements;
        
        if (isActive) {
            // Proctoring active state
            startBtn.disabled = true;
            stopBtn.disabled = false;
            screenshotBtn.disabled = false;
            
            startBtn.classList.remove('btn-success');
            startBtn.classList.add('btn-outline');
            stopBtn.classList.remove('btn-outline');
            stopBtn.classList.add('btn-danger');
            
            this.addAnimation(startBtn, 'fadeIn');
            this.addAnimation(stopBtn, 'fadeIn');
        } else {
            // Proctoring inactive state
            startBtn.disabled = false;
            stopBtn.disabled = true;
            screenshotBtn.disabled = true;
            
            startBtn.classList.remove('btn-outline');
            startBtn.classList.add('btn-success');
            stopBtn.classList.remove('btn-danger');
            stopBtn.classList.add('btn-outline');
            
            this.addAnimation(startBtn, 'fadeIn');
            this.addAnimation(stopBtn, 'fadeIn');
        }
    }
    
    addAnimation(element, animationName) {
        if (!element || !this.animations.has(animationName)) return;
        
        const animationClass = this.animations.get(animationName);
        element.classList.add(animationClass);
        
        // Remove animation class after animation completes
        element.addEventListener('animationend', () => {
            element.classList.remove(animationClass);
        }, { once: true });
    }
    
    updateVideoStats(stats) {
        const fpsElement = document.getElementById('fpsCounter');
        const frameElement = document.getElementById('frameCounter');
        
        if (fpsElement && stats.fps !== undefined) {
            fpsElement.textContent = stats.fps.toFixed(1);
            this.addAnimation(fpsElement, 'fadeIn');
        }
        
        if (frameElement && stats.frame_count !== undefined) {
            frameElement.textContent = stats.frame_count.toLocaleString();
            
            // Add pulse animation every 100 frames
            if (stats.frame_count % 100 === 0) {
                this.addAnimation(frameElement, 'fadeIn');
            }
        }
    }
    
    showModal(title, content, buttons = []) {
        // Create modal elements
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';
        
        const modalContainer = document.createElement('div');
        modalContainer.className = 'modal-container';
        
        const modalHeader = document.createElement('div');
        modalHeader.className = 'modal-header';
        
        const modalTitle = document.createElement('h3');
        modalTitle.textContent = title;
        
        const closeButton = document.createElement('button');
        closeButton.className = 'modal-close';
        closeButton.innerHTML = '&times;';
        closeButton.setAttribute('aria-label', 'Close modal');
        
        const modalBody = document.createElement('div');
        modalBody.className = 'modal-body';
        
        if (typeof content === 'string') {
            modalBody.innerHTML = content;
        } else if (content instanceof HTMLElement) {
            modalBody.appendChild(content);
        }
        
        const modalFooter = document.createElement('div');
        modalFooter.className = 'modal-footer';
        
        // Add buttons
        buttons.forEach(buttonConfig => {
            const button = document.createElement('button');
            button.className = `btn ${buttonConfig.class || 'btn-primary'}`;
            button.textContent = buttonConfig.text;
            
            if (buttonConfig.onClick) {
                button.addEventListener('click', () => {
                    buttonConfig.onClick();
                    this.hideModal(modalOverlay);
                });
            }
            
            if (buttonConfig.closeOnClick !== false) {
                button.addEventListener('click', () => {
                    this.hideModal(modalOverlay);
                });
            }
            
            modalFooter.appendChild(button);
        });
        
        // Add close functionality
        closeButton.addEventListener('click', () => {
            this.hideModal(modalOverlay);
        });
        
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                this.hideModal(modalOverlay);
            }
        });
        
        // Escape key to close
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.hideModal(modalOverlay);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        // Assemble modal
        modalHeader.appendChild(modalTitle);
        modalHeader.appendChild(closeButton);
        
        modalContainer.appendChild(modalHeader);
        modalContainer.appendChild(modalBody);
        if (buttons.length > 0) {
            modalContainer.appendChild(modalFooter);
        }
        
        modalOverlay.appendChild(modalContainer);
        
        // Add to DOM
        const modalContainerElement = document.getElementById('modal-container');
        if (modalContainerElement) {
            modalContainerElement.appendChild(modalOverlay);
        } else {
            document.body.appendChild(modalOverlay);
        }
        
        // Show modal
        setTimeout(() => {
            modalOverlay.classList.add('show');
        }, 10);
        
        return modalOverlay;
    }
    
    hideModal(modalElement) {
        if (modalElement) {
            modalElement.classList.remove('show');
            
            // Remove from DOM after animation
            setTimeout(() => {
                modalElement.remove();
            }, 300);
        }
    }
    
    showHelpModal() {
        const helpContent = `
            <div class="help-content">
                <h4>Vision Guardian Help</h4>
                <p>This is an AI-powered proctoring system that monitors exam sessions for integrity violations.</p>
                
                <h5>Getting Started:</h5>
                <ol>
                    <li>Click <strong>Start</strong> to begin proctoring</li>
                    <li>Ensure you have camera permissions enabled</li>
                    <li>Monitor the risk assessment panel for alerts</li>
                </ol>
                
                <h5>Features:</h5>
                <ul>
                    <li><strong>Gaze Tracking:</strong> Monitors where the student is looking</li>
                    <li><strong>Person Detection:</strong> Ensures only one student is present</li>
                    <li><strong>Object Detection:</strong> Detects prohibited items</li>
                    <li><strong>Risk Assessment:</strong> Calculates overall risk score</li>
                </ul>
                
                <p><em>For technical support, please contact your system administrator.</em></p>
            </div>
        `;
        
        this.showModal('Help & Instructions', helpContent, [
            {
                text: 'Close',
                class: 'btn-primary',
                closeOnClick: true
            }
        ]);
    }
    
    updateConnectionStatus(status) {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        
        if (!statusDot || !statusText) return;
        
        statusDot.className = 'status-dot';
        statusText.textContent = status.message || 'Unknown';
        
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
    
    // Utility method to format numbers
    formatNumber(num, decimals = 1) {
        if (num === null || num === undefined) return 'N/A';
        
        if (num >= 1000000) {
            return (num / 1000000).toFixed(decimals) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(decimals) + 'K';
        }
        
        return num.toFixed(decimals);
    }
    
    // Utility method to format time
    formatTime(seconds) {
        if (seconds === null || seconds === undefined) return '--:--';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UIHandler };
}