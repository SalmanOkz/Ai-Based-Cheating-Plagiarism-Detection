// Analytics Component
class AnalyticsComponent {
    constructor(app) {
        this.app = app;
        this.element = null;
        this.metrics = {
            riskScore: 0,
            gazeLevel: 0,
            personCount: 0,
            prohibitedItems: [],
            alertLevel: 'NORMAL'
        };
        this.init();
    }
    
    init() {
        this.createElement();
        this.render();
        this.setupEventListeners();
    }
    
    createElement() {
        const section = document.createElement('div');
        section.id = 'analytics-section';
        section.className = 'analytics-section';
        
        section.innerHTML = `
            <!-- Risk Assessment Card -->
            <div class="risk-card">
                <h3><i class="fas fa-chart-line"></i> Risk Assessment</h3>
                
                <div class="risk-meter-container">
                    <div class="risk-labels">
                        <span>Low</span>
                        <span>Medium</span>
                        <span>High</span>
                    </div>
                    <div class="risk-meter">
                        <div class="risk-indicator" id="riskIndicator" style="left: 0%;"></div>
                    </div>
                </div>
                
                <div class="risk-score-display">
                    <div class="risk-score-value" id="riskScore">0</div>
                    <div class="risk-score-total">/10</div>
                </div>
                
                <div class="risk-status safe" id="riskStatus">No Risk</div>
            </div>
            
            <!-- Detection Cards Grid -->
            <div class="detection-grid">
                <!-- Gaze Tracking Card -->
                <div class="detection-card">
                    <div class="detection-header">
                        <i class="fas fa-eye detection-icon"></i>
                        <h4>Gaze Tracking</h4>
                    </div>
                    <div class="detection-content">
                        <div class="detection-status">
                            <i class="fas fa-check-circle status-icon safe"></i>
                            <span id="gazeText">Looking Center</span>
                        </div>
                        <div class="detection-details">
                            Level: <span id="gazeLevel">0</span>
                        </div>
                    </div>
                </div>
                
                <!-- Student Detection Card -->
                <div class="detection-card">
                    <div class="detection-header">
                        <i class="fas fa-user-friends detection-icon"></i>
                        <h4>Student Detection</h4>
                    </div>
                    <div class="detection-content">
                        <div class="detection-status">
                            <i class="fas fa-user status-icon safe"></i>
                            <span>Count: <span id="studentCount">0</span></span>
                        </div>
                        <div class="detection-details" id="studentStatus">
                            Status: Normal
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- System Information Card -->
            <div class="system-info-card">
                <div class="system-info-header">
                    <h3><i class="fas fa-info-circle"></i> System Info</h3>
                    <button class="refresh-btn" id="refreshStatus" aria-label="Refresh status">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
                <div class="info-items">
                    <div class="info-item">
                        <span class="info-label">AI Mode:</span>
                        <span class="info-value" id="aiStatus">Checking...</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Camera:</span>
                        <span class="info-value" id="cameraStatus">Inactive</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Frames:</span>
                        <span class="info-value" id="totalFrames">0</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Violations:</span>
                        <span class="info-value" id="violationCount">0</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Uptime:</span>
                        <span class="info-value" id="uptime">--:--</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Violations:</span>
                        <span class="info-value" id="violationCount">0</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Clipboard Events:</span>
                        <span class="info-value" id="clipboardCount">0</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Uptime:</span>
                        <span class="info-value" id="uptime">--:--</span>
                    </div>
                </div>
            </div>
        `;
        
        this.element = section;
    }
    
    render() {
        const container = document.getElementById('analytics-section');
        if (container) {
            container.replaceWith(this.element);
        } else {
            document.querySelector('.right-panel').appendChild(this.element);
        }
    }
    
    setupEventListeners() {
        // Refresh button
        const refreshBtn = this.element.querySelector('#refreshStatus');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.handleRefresh();
            });
        }
        
        // Risk status click for details
        const riskStatus = this.element.querySelector('#riskStatus');
        if (riskStatus) {
            riskStatus.addEventListener('click', () => {
                this.showRiskDetails();
            });
        }
    }
    
    async handleRefresh() {
        const refreshBtn = this.element.querySelector('#refreshStatus');
        if (refreshBtn) {
            // Add spin animation
            refreshBtn.classList.add('spin');
            
            try {
                await this.app.checkSystemStatus();
                await this.app.updateAnalytics();
                
                this.app.showNotification('Status refreshed', 'success');
            } catch (error) {
                console.error('Refresh failed:', error);
                this.app.showNotification('Refresh failed', 'error');
            } finally {
                setTimeout(() => {
                    refreshBtn.classList.remove('spin');
                }, 500);
            }
        }
    }
    
    update(results) {
        if (!results) return;
        
        // Update metrics
        this.metrics.riskScore = results.risk_score || 0;
        this.metrics.gazeLevel = results.gaze_level || 0;
        this.metrics.personCount = results.person_count || 0;
        this.metrics.prohibitedItems = results.prohibited_items || [];
        this.metrics.alertLevel = results.alert_level || 'NORMAL';
        
        // Update UI elements
        this.updateRiskMeter();
        this.updateGazeTracking();
        this.updateStudentDetection();
        this.updateSystemInfo(results);
    }
    
    updateRiskMeter() {
        const riskScore = this.metrics.riskScore;
        const alertLevel = this.metrics.alertLevel;
        
        // Update risk indicator position (0-100%)
        const indicator = this.element.querySelector('#riskIndicator');
        if (indicator) {
            const position = (riskScore / 10) * 100;
            indicator.style.left = `${position}%`;
        }
        
        // Update risk score display
        const scoreElement = this.element.querySelector('#riskScore');
        if (scoreElement) {
            scoreElement.textContent = riskScore;
            
            // Add color based on score
            scoreElement.className = 'risk-score-value';
            if (riskScore >= 6) {
                scoreElement.classList.add('danger');
            } else if (riskScore >= 3) {
                scoreElement.classList.add('warning');
            } else {
                scoreElement.classList.add('safe');
            }
        }
        
        // Update risk status
        const statusElement = this.element.querySelector('#riskStatus');
        if (statusElement) {
            statusElement.textContent = alertLevel;
            
            // Update status class
            statusElement.className = 'risk-status';
            switch (alertLevel) {
                case 'CRITICAL':
                    statusElement.classList.add('danger');
                    statusElement.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${alertLevel}`;
                    break;
                case 'WARNING':
                    statusElement.classList.add('warning');
                    statusElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${alertLevel}`;
                    break;
                default:
                    statusElement.classList.add('safe');
                    statusElement.innerHTML = `<i class="fas fa-check-circle"></i> ${alertLevel}`;
            }
        }
    }
    
    updateGazeTracking() {
        const gazeLevel = this.metrics.gazeLevel;
        const gazeStatus = this.element.querySelector('#gazeText');
        const gazeLevelElement = this.element.querySelector('#gazeLevel');
        const statusIcon = this.element.querySelector('#gazeText').previousElementSibling;
        
        if (gazeStatus && gazeLevelElement && statusIcon) {
            // Determine gaze status text
            let statusText = 'Looking Center';
            let statusClass = 'safe';
            
            if (gazeLevel >= 2) {
                statusText = 'Looking Away';
                statusClass = 'danger';
            } else if (gazeLevel >= 1) {
                statusText = 'Suspicious Gaze';
                statusClass = 'warning';
            }
            
            gazeStatus.textContent = statusText;
            gazeLevelElement.textContent = gazeLevel;
            
            // Update status icon
            statusIcon.className = 'fas status-icon';
            statusIcon.classList.add(statusClass);
            
            if (statusClass === 'danger') {
                statusIcon.classList.remove('fa-check-circle');
                statusIcon.classList.add('fa-exclamation-triangle');
            } else if (statusClass === 'warning') {
                statusIcon.classList.remove('fa-check-circle');
                statusIcon.classList.add('fa-exclamation-circle');
            } else {
                statusIcon.classList.remove('fa-exclamation-circle', 'fa-exclamation-triangle');
                statusIcon.classList.add('fa-check-circle');
            }
        }
    }
    
    updateStudentDetection() {
        const personCount = this.metrics.personCount;
        const countElement = this.element.querySelector('#studentCount');
        const statusElement = this.element.querySelector('#studentStatus');
        const statusIcon = this.element.querySelector('#studentCount').previousElementSibling;
        
        if (countElement && statusElement && statusIcon) {
            countElement.textContent = personCount;
            
            let statusText = 'Normal';
            let statusClass = 'safe';
            
            if (personCount === 0) {
                statusText = 'No Student';
                statusClass = 'danger';
            } else if (personCount > 1) {
                statusText = 'Multiple Persons';
                statusClass = 'danger';
            }
            
            statusElement.textContent = `Status: ${statusText}`;
            
            // Update status icon
            statusIcon.className = 'fas status-icon';
            statusIcon.classList.add(statusClass);
            
            if (statusClass === 'danger') {
                statusIcon.classList.remove('fa-user');
                statusIcon.classList.add('fa-user-times');
            } else {
                statusIcon.classList.remove('fa-user-times');
                statusIcon.classList.add('fa-user');
            }
        }
    }
    
    updateSystemInfo(results) {
        // AI Status
        const aiStatusElement = this.element.querySelector('#aiStatus');
        if (aiStatusElement) {
            const aiMode = results.ai_mode || 'Unknown';
            aiStatusElement.textContent = aiMode;
            aiStatusElement.className = 'info-value';
            
            if (aiMode.includes('SIMULATION')) {
                aiStatusElement.classList.add('warning');
            } else if (aiMode.includes('REAL')) {
                aiStatusElement.classList.add('safe');
            }
        }
        
        // Camera Status
        const cameraStatusElement = this.element.querySelector('#cameraStatus');
        if (cameraStatusElement) {
            const isActive = results.camera_active || false;
            cameraStatusElement.textContent = isActive ? 'Active' : 'Inactive';
            cameraStatusElement.className = 'info-value';
            cameraStatusElement.classList.add(isActive ? 'safe' : 'warning');
        }
        
        // Total Frames
        const framesElement = this.element.querySelector('#totalFrames');
        if (framesElement && results.frames_processed !== undefined) {
            framesElement.textContent = results.frames_processed.toLocaleString();
        }
        
        // Violation Count
        const violationElement = this.element.querySelector('#violationCount');
        if (violationElement && results.violation_count !== undefined) {
            violationElement.textContent = results.violation_count;
            violationElement.className = 'info-value';
            
            if (results.violation_count > 0) {
                violationElement.classList.add('danger');
            }
        }
        
        // Uptime
        const uptimeElement = this.element.querySelector('#uptime');
        if (uptimeElement && results.uptime !== undefined) {
            uptimeElement.textContent = this.app.ui.formatTime(results.uptime);
        }
    }
    
    showRiskDetails() {
        const details = `
            <div class="risk-details">
                <h4>Risk Analysis Details</h4>
                <div class="risk-factors">
                    <div class="risk-factor">
                        <span class="factor-label">Gaze Deviation:</span>
                        <span class="factor-value">Level ${this.metrics.gazeLevel}</span>
                    </div>
                    <div class="risk-factor">
                        <span class="factor-label">Student Count:</span>
                        <span class="factor-value">${this.metrics.personCount}</span>
                    </div>
                    <div class="risk-factor">
                        <span class="factor-label">Prohibited Items:</span>
                        <span class="factor-value">${this.metrics.prohibitedItems.length}</span>
                    </div>
                </div>
                
                <div class="prohibited-items">
                    <h5>Detected Items:</h5>
                    ${this.metrics.prohibitedItems.length > 0 
                        ? this.metrics.prohibitedItems.map(item => 
                            `<div class="prohibited-item">
                                <i class="fas fa-ban text-danger"></i>
                                ${item.item} (${(item.confidence * 100).toFixed(1)}%)
                            </div>`
                        ).join('')
                        : '<p class="text-success">No prohibited items detected</p>'
                    }
                </div>
            </div>
        `;
        
        this.app.ui.showModal('Risk Assessment Details', details, [
            {
                text: 'Close',
                class: 'btn-primary',
                closeOnClick: true
            }
        ]);
    }
    
    destroy() {
        if (this.element) {
            this.element.remove();
        }
    }
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AnalyticsComponent };
}