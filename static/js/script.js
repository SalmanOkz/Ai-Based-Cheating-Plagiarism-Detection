/**
 * Vision Guardian Frontend - With Debug Features
 */

class VisionGuardianFrontend {
    constructor() {
        this.isProctoring = false;
        this.violations = [];
        this.lastResults = {};
        this.updateInterval = null;
        
        this.initElements();
        this.initEventListeners();
        this.checkConnection();
        
        // Start periodic updates
        setInterval(() => {
            if (this.isProctoring) {
                this.getResults();
            }
            this.getSystemStatus();
        }, 1000); // Update every second
    }
    
    initElements() {
        // Status elements
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        
        // Control buttons
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.screenshotBtn = document.getElementById('screenshotBtn');
        this.refreshStatus = document.getElementById('refreshStatus');
        
        // Add debug button if not exists
        if (!document.getElementById('debugBtn')) {
            const debugBtn = document.createElement('button');
            debugBtn.id = 'debugBtn';
            debugBtn.className = 'btn btn-warning';
            debugBtn.innerHTML = '<i class="fas fa-bug"></i> Debug';
            document.querySelector('.video-controls').appendChild(debugBtn);
        }
        
        this.debugBtn = document.getElementById('debugBtn');
        
        // Counters and displays
        this.fpsCounter = document.getElementById('fpsCounter');
        this.frameCounter = document.getElementById('frameCounter');
        this.aiMode = document.getElementById('aiMode');
        
        // Risk assessment
        this.riskIndicator = document.getElementById('riskIndicator');
        this.riskScore = document.getElementById('riskScore');
        this.riskStatus = document.getElementById('riskStatus');
        
        // Detection displays
        this.gazeText = document.getElementById('gazeText');
        this.gazeLevel = document.getElementById('gazeLevel');
        this.studentCount = document.getElementById('studentCount');
        this.studentStatus = document.getElementById('studentStatus');
        
        // System info
        this.aiStatus = document.getElementById('aiStatus');
        this.cameraStatus = document.getElementById('cameraStatus');
        this.totalFrames = document.getElementById('totalFrames');
        
        // Toast
        this.toast = document.getElementById('toast');
        this.toastMessage = document.getElementById('toastMessage');
    }
    
    initEventListeners() {
        // Start proctoring
        this.startBtn.addEventListener('click', () => this.startProctoring());
        
        // Stop proctoring
        this.stopBtn.addEventListener('click', () => this.stopProctoring());
        
        // Take screenshot
        this.screenshotBtn.addEventListener('click', () => this.takeScreenshot());
        
        // Refresh status
        this.refreshStatus.addEventListener('click', () => this.getSystemStatus());
        
        // Debug button
        this.debugBtn.addEventListener('click', () => this.debugDetection());
        
        // Help
        document.getElementById('helpBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.showHelp();
        });
    }
    
    async checkConnection() {
        try {
            const response = await fetch('/api/test_ai');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateConnectionStatus(true);
                this.aiMode.textContent = data.ai_mode;
                this.aiStatus.textContent = data.ai_mode;
                this.showToast(`✅ Connected to ${data.ai_mode} backend`);
                
                // Show AI component status
                if (data.modules) {
                    console.log('AI Components:', data.modules);
                }
            } else {
                this.aiMode.textContent = 'Simulation';
                this.aiStatus.textContent = 'Simulation Mode';
                this.showToast('⚠️ Running in simulation mode');
            }
        } catch (error) {
            console.error('Connection check failed:', error);
            this.aiMode.textContent = 'Offline';
            this.aiStatus.textContent = 'Offline';
            this.updateConnectionStatus(false);
        }
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.statusDot.className = 'status-dot connected';
            this.statusText.textContent = 'Connected';
        } else {
            this.statusDot.className = 'status-dot';
            this.statusText.textContent = 'Disconnected';
        }
    }
    
    async startProctoring() {
        try {
            const response = await fetch('/api/start_proctoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.isProctoring = true;
                
                this.startBtn.disabled = true;
                this.stopBtn.disabled = false;
                this.cameraStatus.textContent = 'Active';
                
                this.showToast(`Proctoring started (${data.ai_mode})`);
            } else {
                this.showToast(`Failed to start: ${data.message}`);
            }
        } catch (error) {
            console.error('Error starting proctoring:', error);
            this.showToast('Error starting proctoring');
        }
    }
    
    async stopProctoring() {
        try {
            const response = await fetch('/api/stop_proctoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.isProctoring = false;
                
                this.startBtn.disabled = false;
                this.stopBtn.disabled = true;
                this.cameraStatus.textContent = 'Inactive';
                
                this.showToast('Proctoring stopped');
            }
        } catch (error) {
            console.error('Error stopping proctoring:', error);
        }
    }
    
    async takeScreenshot() {
        if (!this.isProctoring) {
            this.showToast('Start proctoring first to take screenshots');
            return;
        }
        
        try {
            const response = await fetch('/api/take_screenshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Create download link
                const link = document.createElement('a');
                link.href = data.image;
                link.download = data.filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                this.showToast(`Screenshot saved: ${data.filename}`);
            } else {
                this.showToast(`Failed: ${data.message}`);
            }
        } catch (error) {
            console.error('Error taking screenshot:', error);
            this.showToast('Error taking screenshot');
        }
    }
    
    async debugDetection() {
        try {
            const response = await fetch('/api/debug_detection');
            const data = await response.json();
            
            if (data.status === 'success') {
                const debugInfo = `
🔍 DEBUG INFORMATION:
=====================
Detections: ${data.detection_count}
Persons: ${data.persons}
Prohibited Items: ${data.prohibited}

Detection Details:
${JSON.stringify(data.detections, null, 2)}

Check the console for more details.
                `;
                
                console.log('Debug Detection Results:', data);
                alert(debugInfo);
                this.showToast('Debug info collected - check console');
            } else {
                this.showToast(`Debug failed: ${data.message}`);
            }
        } catch (error) {
            console.error('Error debugging:', error);
            this.showToast('Error debugging detection');
        }
    }
    
    async getResults() {
        try {
            const response = await fetch('/api/get_results');
            const data = await response.json();
            
            this.lastResults = data;
            this.updateUI(data);
            
            // Log to console for debugging
            if (data.detections && data.detections.length > 0) {
                console.log(`Frame ${data.frame_count}: ${data.detections.length} detections`);
            }
            
            return data;
        } catch (error) {
            console.error('Error getting results:', error);
            return null;
        }
    }
    
    async getSystemStatus() {
        try {
            const response = await fetch('/api/get_system_status');
            const data = await response.json();
            
            this.updateSystemInfo(data);
            return data;
        } catch (error) {
            console.error('Error getting system status:', error);
            return null;
        }
    }
    
    updateUI(results) {
        // Update counters
        if (results.fps) this.fpsCounter.textContent = results.fps;
        if (results.frame_count) this.frameCounter.textContent = results.frame_count;
        
        // Update risk assessment
        this.updateRiskAssessment(results.risk_score, results.alert_level, results.is_cheating);
        
        // Update gaze tracking
        this.updateGazeTracking(results.gaze_status, results.gaze_level);
        
        // Update student detection
        this.updateStudentDetection(results.person_count);
        
        // Update total frames
        if (results.frames_processed) {
            this.totalFrames.textContent = results.frames_processed;
        }
        
        // Update AI mode
        if (results.ai_mode) {
            this.aiMode.textContent = results.ai_mode;
            this.aiStatus.textContent = results.ai_mode;
        }
    }
    
    updateRiskAssessment(score, alertLevel, isCheating) {
        this.riskScore.textContent = score;
        
        // Move risk indicator (0-10 to 0-100%)
        const position = (score / 10) * 100;
        this.riskIndicator.style.left = `${position}%`;
        
        // Update risk status
        this.riskStatus.textContent = alertLevel;
        
        if (isCheating || alertLevel === 'CRITICAL') {
            this.riskStatus.style.background = '#dc3545';
        } else if (alertLevel === 'WARNING') {
            this.riskStatus.style.background = '#ffc107';
            this.riskStatus.style.color = 'black';
        } else {
            this.riskStatus.style.background = '#28a745';
            this.riskStatus.style.color = 'white';
        }
    }
    
    updateGazeTracking(status, level) {
        this.gazeText.textContent = status;
        this.gazeLevel.textContent = level;
        
        // Update icon color
        const icon = this.gazeText.parentElement.querySelector('i');
        if (level >= 2) {
            icon.style.color = '#dc3545';
        } else if (level >= 1) {
            icon.style.color = '#ffc107';
        } else {
            icon.style.color = '#28a745';
        }
    }
    
    updateStudentDetection(count) {
        this.studentCount.textContent = count;
        
        if (count === 0) {
            this.studentStatus.textContent = 'Status: No Student';
            this.studentStatus.style.color = '#dc3545';
        } else if (count === 1) {
            this.studentStatus.textContent = 'Status: Normal';
            this.studentStatus.style.color = '#28a745';
        } else {
            this.studentStatus.textContent = `Status: ${count} Students`;
            this.studentStatus.style.color = '#dc3545';
        }
    }
    
    updateSystemInfo(status) {
        this.aiStatus.textContent = status.ai_mode;
        this.aiStatus.style.color = status.ai_available ? '#28a745' : '#ffc107';
        
        this.cameraStatus.textContent = status.camera_active ? 'Active' : 'Inactive';
        this.cameraStatus.style.color = status.camera_active ? '#28a745' : '#dc3545';
        
        if (status.ai_available) {
            this.aiMode.textContent = 'Real AI';
        } else {
            this.aiMode.textContent = 'Simulation';
        }
    }
    
    showToast(message) {
        this.toastMessage.textContent = message;
        this.toast.classList.add('show');
        
        setTimeout(() => {
            this.toast.classList.remove('show');
        }, 3000);
    }
    
    showHelp() {
        const helpText = `
Vision Guardian AI Proctoring System

How to Use:
1. Click "Start Proctoring" to begin AI analysis
2. The system will analyze:
   - Where the student is looking (Gaze Tracking)
   - How many students are present
   - If any prohibited items are visible (phones, books)
3. Risk assessment updates in real-time
4. Screenshots can be taken for evidence
5. Use "Debug" button to check detection status

AI Modes:
- Real AI: Uses YOLO and MediaPipe models
- Simulation: Uses simulated data for testing

Status Colors:
- Green: Normal activity
- Yellow: Warning (suspicious activity)
- Red: Critical (cheating detected)

Debugging:
- Check browser console for detection logs
- Use Debug button to see detection details
        `;
        
        alert(helpText);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    const app = new VisionGuardianFrontend();
    
    // Global reference for debugging
    window.app = app;
    
    // Show welcome message
    setTimeout(() => {
        app.showToast('Vision Guardian AI Proctoring System Ready');
    }, 1000);
});