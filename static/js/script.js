/**
 * Vision Guardian Frontend Logic
 */

class VisionGuardianUI {
    constructor() {
        this.isProctoring = false;
        this.startTime = null;
        this.updateInterval = null;
        this.statsInterval = null;
        
        // Initialize
        this.initElements();
        this.initEventListeners();
        this.initStatsUpdate();
    }
    
    initElements() {
        // Buttons
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.screenshotBtn = document.getElementById('screenshotBtn');
        this.refreshLogBtn = document.getElementById('refreshLog');
        
        // Counters
        this.fpsCounter = document.getElementById('fpsCounter');
        this.frameCounter = document.getElementById('frameCounter');
        this.violationCounter = document.getElementById('violationCounter');
        this.riskScore = document.getElementById('riskScore');
        this.riskIndicator = document.getElementById('riskIndicator');
        this.riskStatus = document.getElementById('riskStatus');
        
        // Status displays
        this.gazeStatus = document.getElementById('gazeStatus');
        this.gazeLevel = document.getElementById('gazeLevel');
        this.personCount = document.getElementById('personCount');
        this.presenceStatus = document.getElementById('presenceStatus');
        this.itemsList = document.getElementById('itemsList');
        
        // System info
        this.systemStatus = document.getElementById('systemStatus');
        this.uptime = document.getElementById('uptime');
        this.lastUpdate = document.getElementById('lastUpdate');
        
        // Alerts
        this.alertBanner = document.getElementById('alertBanner');
        this.alertText = document.getElementById('alertText');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.statusText = this.statusIndicator.querySelector('.status-text');
        
        // Lists
        this.violationsList = document.getElementById('violationsList');
        
        // Toast
        this.toast = document.getElementById('toast');
        this.toastMessage = document.querySelector('.toast-message');
    }
    
    initEventListeners() {
        // Start Proctoring
        this.startBtn.addEventListener('click', () => this.startProctoring());
        
        // Stop Proctoring
        this.stopBtn.addEventListener('click', () => this.stopProctoring());
        
        // Take Screenshot
        this.screenshotBtn.addEventListener('click', () => this.takeScreenshot());
        
        // Refresh Violation Log
        this.refreshLogBtn.addEventListener('click', () => this.loadViolations());
    }
    
    async startProctoring() {
        try {
            const response = await fetch('/start_proctoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.isProctoring = true;
                this.startTime = new Date();
                
                // Update UI
                this.startBtn.disabled = true;
                this.stopBtn.disabled = false;
                this.systemStatus.textContent = 'Active';
                this.statusText.textContent = 'Proctoring';
                this.statusDot.style.background = '#2a9d8f';
                
                this.showToast('Proctoring session started');
                
                // Start updating stats more frequently
                this.startStatsUpdate();
                
                // Start uptime counter
                this.startUptimeCounter();
            } else {
                this.showToast('Failed to start proctoring: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error starting proctoring:', error);
            this.showToast('Error starting proctoring', 'error');
        }
    }
    
    async stopProctoring() {
        try {
            const response = await fetch('/stop_proctoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.isProctoring = false;
                
                // Update UI
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.systemStatus.textContent = 'Ready';
                this.statusText.textContent = 'Ready';
                this.statusDot.style.background = '#6c757d';
                
                this.showToast('Proctoring session stopped');
                
                // Stop stats update
                this.stopStatsUpdate();
            }
        } catch (error) {
            console.error('Error stopping proctoring:', error);
            this.showToast('Error stopping proctoring', 'error');
        }
    }
    
    async takeScreenshot() {
        try {
            const response = await fetch('/take_screenshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showToast('Screenshot saved: ' + data.filename);
            } else {
                this.showToast('Failed to take screenshot: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error taking screenshot:', error);
            this.showToast('Error taking screenshot', 'error');
        }
    }
    
    initStatsUpdate() {
        // Update stats every 2 seconds initially
        this.updateInterval = setInterval(() => {
            if (!this.isProctoring) {
                this.loadStats();
            }
        }, 2000);
    }
    
    startStatsUpdate() {
        // Clear initial interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Update more frequently when proctoring
        this.statsInterval = setInterval(() => {
            this.loadStats();
            this.loadViolations();
        }, 1000); // Update every second
    }
    
    stopStatsUpdate() {
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
            this.statsInterval = null;
        }
        
        // Restore slower updates
        this.updateInterval = setInterval(() => {
            this.loadStats();
        }, 2000);
    }
    
    async loadStats() {
        try {
            const response = await fetch('/get_stats');
            const data = await response.json();
            
            // Update counters
            this.fpsCounter.textContent = data.fps;
            this.frameCounter.textContent = data.frame_count.toLocaleString();
            this.violationCounter.textContent = data.violation_count.toLocaleString();
            
            // Update risk assessment
            this.riskScore.textContent = data.risk_score;
            this.updateRiskIndicator(data.risk_score);
            this.updateRiskStatus(data.risk_score, data.is_cheating);
            
            // Update gaze tracking
            this.updateGazeStatus(data.gaze_status, data.alert_level);
            
            // Update presence detection
            this.personCount.textContent = data.person_count;
            this.updatePresenceStatus(data.person_count);
            
            // Update prohibited items
            this.updateProhibitedItems(data.prohibited_items);
            
            // Update alerts
            this.updateAlertBanner(data.alert_level, data.is_cheating);
            
            // Update system status
            this.lastUpdate.textContent = new Date().toLocaleTimeString();
            
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    updateRiskIndicator(score) {
        // Move risk indicator (0-10 to 0-100%)
        const position = (score / 10) * 100;
        this.riskIndicator.style.left = `${position}%`;
        
        // Update color based on score
        if (score <= 3) {
            this.riskIndicator.style.background = '#2a9d8f'; // Green
        } else if (score <= 6) {
            this.riskIndicator.style.background = '#ff9f1c'; // Orange
        } else {
            this.riskIndicator.style.background = '#e63946'; // Red
        }
    }
    
    updateRiskStatus(score, isCheating) {
        if (isCheating) {
            this.riskStatus.textContent = 'HIGH RISK - Cheating Detected';
            this.riskStatus.style.background = '#e63946';
            this.riskStatus.style.color = 'white';
        } else if (score >= 6) {
            this.riskStatus.textContent = 'Medium Risk';
            this.riskStatus.style.background = '#ff9f1c';
            this.riskStatus.style.color = 'black';
        } else if (score >= 3) {
            this.riskStatus.textContent = 'Low Risk';
            this.riskStatus.style.background = '#2a9d8f';
            this.riskStatus.style.color = 'white';
        } else {
            this.riskStatus.textContent = 'No Risk';
            this.riskStatus.style.background = '#6c757d';
            this.riskStatus.style.color = 'white';
        }
    }
    
    updateGazeStatus(status, alertLevel) {
        const gazeElement = this.gazeStatus.querySelector('span');
        const icon = this.gazeStatus.querySelector('i');
        
        gazeElement.textContent = status;
        
        // Update level based on status
        let level = 0;
        if (status.includes('Looking Down')) {
            level = 2;
        } else if (status.includes('Looking') && !status.includes('Center')) {
            level = 1;
        }
        
        this.gazeLevel.textContent = level;
        
        // Update icon color
        if (level === 2) {
            icon.style.color = '#e63946'; // Red
            this.gazeLevel.style.background = '#e63946';
            this.gazeLevel.style.color = 'white';
        } else if (level === 1) {
            icon.style.color = '#ff9f1c'; // Orange
            this.gazeLevel.style.background = '#ff9f1c';
            this.gazeLevel.style.color = 'black';
        } else {
            icon.style.color = '#2a9d8f'; // Green
            this.gazeLevel.style.background = '#2a9d8f';
            this.gazeLevel.style.color = 'white';
        }
    }
    
    updatePresenceStatus(personCount) {
        if (personCount === 0) {
            this.presenceStatus.textContent = 'No Person';
            this.presenceStatus.className = 'status-ok';
            this.presenceStatus.style.color = '#e63946';
        } else if (personCount === 1) {
            this.presenceStatus.textContent = 'Normal';
            this.presenceStatus.className = 'status-ok';
            this.presenceStatus.style.color = '#2a9d8f';
        } else {
            this.presenceStatus.textContent = 'Multiple Persons';
            this.presenceStatus.className = 'status-ok';
            this.presenceStatus.style.color = '#e63946';
        }
    }
    
    updateProhibitedItems(items) {
        this.itemsList.innerHTML = '';
        
        if (items && items.length > 0) {
            items.forEach(item => {
                const itemElement = document.createElement('div');
                itemElement.className = 'item-tag';
                itemElement.textContent = item;
                this.itemsList.appendChild(itemElement);
            });
        } else {
            const noItems = document.createElement('div');
            noItems.className = 'no-items';
            noItems.textContent = 'No prohibited items detected';
            this.itemsList.appendChild(noItems);
        }
    }
    
    updateAlertBanner(alertLevel, isCheating) {
        if (isCheating) {
            this.alertBanner.style.display = 'flex';
            this.alertText.textContent = `ALERT: ${alertLevel} Risk - Cheating Detected!`;
            this.alertBanner.style.background = 'rgba(230, 57, 70, 0.9)';
            
            // Blink effect for critical alerts
            if (alertLevel === 'CRITICAL') {
                this.alertBanner.style.animation = 'pulse 1s infinite';
            }
        } else {
            this.alertBanner.style.display = 'none';
            this.alertBanner.style.animation = 'none';
        }
    }
    
    async loadViolations() {
        try {
            const response = await fetch('/get_violations');
            const data = await response.json();
            
            this.updateViolationsList(data.violations);
        } catch (error) {
            console.error('Error loading violations:', error);
        }
    }
    
    updateViolationsList(violations) {
        this.violationsList.innerHTML = '';
        
        if (violations && violations.length > 0) {
            violations.forEach(violation => {
                const violationItem = document.createElement('div');
                violationItem.className = 'violation-item';
                
                violationItem.innerHTML = `
                    <div>
                        <div class="violation-type">${violation.type}</div>
                        <div class="violation-time">${violation.timestamp}</div>
                    </div>
                    <div class="violation-risk">${violation.risk_score}/10</div>
                `;
                
                this.violationsList.appendChild(violationItem);
            });
        } else {
            const noViolations = document.createElement('div');
            noViolations.className = 'no-violations';
            noViolations.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <p>No violations detected</p>
            `;
            this.violationsList.appendChild(noViolations);
        }
    }
    
    startUptimeCounter() {
        if (this.uptimeInterval) {
            clearInterval(this.uptimeInterval);
        }
        
        this.uptimeInterval = setInterval(() => {
            if (this.startTime) {
                const now = new Date();
                const diff = Math.floor((now - this.startTime) / 1000);
                
                const hours = Math.floor(diff / 3600);
                const minutes = Math.floor((diff % 3600) / 60);
                const seconds = diff % 60;
                
                this.uptime.textContent = 
                    `${hours.toString().padStart(2, '0')}:` +
                    `${minutes.toString().padStart(2, '0')}:` +
                    `${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    showToast(message, type = 'success') {
        this.toastMessage.textContent = message;
        
        // Update color based on type
        if (type === 'error') {
            this.toast.style.background = '#e63946';
        } else if (type === 'warning') {
            this.toast.style.background = '#ff9f1c';
        } else {
            this.toast.style.background = '#2a9d8f';
        }
        
        // Show toast
        this.toast.classList.add('show');
        
        // Hide after 3 seconds
        setTimeout(() => {
            this.toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    const app = new VisionGuardianUI();
    
    // Initial load
    app.loadStats();
    app.loadViolations();
});