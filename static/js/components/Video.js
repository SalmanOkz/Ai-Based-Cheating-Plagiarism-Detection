// Video Component
class VideoComponent {
    constructor(app) {
        this.app = app;
        this.element = null;
        this.videoFeed = null;
        this.stats = {
            fps: 0,
            frameCount: 0,
            processingTime: 0
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
        section.id = 'video-section';
        section.className = 'video-section';
        
        section.innerHTML = `
            <div class="video-header">
                <h2><i class="fas fa-video"></i> Live AI Analysis</h2>
                <div class="video-controls">
                    <button id="startBtn" class="btn btn-success">
                        <i class="fas fa-play"></i> Start Proctoring
                    </button>
                    <button id="stopBtn" class="btn btn-outline" disabled>
                        <i class="fas fa-stop"></i> Stop
                    </button>
                    <button id="screenshotBtn" class="btn btn-info">
                        <i class="fas fa-camera"></i> Screenshot
                    </button>
                </div>
            </div>
            
            <div class="video-frame">
                <img id="videoFeed" src="/video_feed" alt="Live AI Analysis Feed">
            </div>
            
            <div class="video-stats">
                <div class="stat-item">
                    <i class="fas fa-tachometer-alt stat-icon"></i>
                    <span>FPS: <span id="fpsCounter">0</span></span>
                </div>
                <div class="stat-item">
                    <i class="fas fa-film stat-icon"></i>
                    <span>Frame: <span id="frameCounter">0</span></span>
                </div>
                <div class="stat-item">
                    <i class="fas fa-brain stat-icon"></i>
                    <span>AI: <span id="aiMode">Checking...</span></span>
                </div>
                <div class="stat-item">
                    <i class="fas fa-clock stat-icon"></i>
                    <span>Processing: <span id="processingTime">0</span>ms</span>
                </div>
            </div>
        `;
        
        this.element = section;
        this.videoFeed = section.querySelector('#videoFeed');
    }
    
    render() {
        const container = document.getElementById('video-section');
        if (container) {
            container.replaceWith(this.element);
        } else {
            document.querySelector('.left-panel').appendChild(this.element);
        }
    }
    
    setupEventListeners() {
        const startBtn = this.element.querySelector('#startBtn');
        const stopBtn = this.element.querySelector('#stopBtn');
        const screenshotBtn = this.element.querySelector('#screenshotBtn');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                this.app.startProctoring();
            });
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                this.app.stopProctoring();
            });
        }
        
        if (screenshotBtn) {
            screenshotBtn.addEventListener('click', () => {
                this.app.takeScreenshot();
            });
        }
        
        // Handle video feed errors
        if (this.videoFeed) {
            this.videoFeed.addEventListener('error', (e) => {
                console.error('Video feed error:', e);
                this.showVideoError();
            });
            
            this.videoFeed.addEventListener('load', () => {
                console.log('Video feed loaded successfully');
            });
        }
    }
    
    showVideoError() {
        const videoFrame = this.element.querySelector('.video-frame');
        if (videoFrame) {
            const errorMessage = document.createElement('div');
            errorMessage.className = 'video-error';
            errorMessage.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(220, 53, 69, 0.9);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                z-index: 10;
            `;
            errorMessage.innerHTML = `
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                <h3>Video Feed Error</h3>
                <p>Unable to load video stream</p>
                <button class="btn btn-warning mt-3" id="retryVideo">
                    <i class="fas fa-sync-alt"></i> Retry
                </button>
            `;
            
            videoFrame.appendChild(errorMessage);
            
            // Add retry functionality
            const retryBtn = errorMessage.querySelector('#retryVideo');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    errorMessage.remove();
                    this.retryVideoFeed();
                });
            }
        }
    }
    
    retryVideoFeed() {
        if (this.videoFeed) {
            const currentSrc = this.videoFeed.src;
            this.videoFeed.src = '';
            
            setTimeout(() => {
                this.videoFeed.src = currentSrc;
            }, 100);
        }
    }
    
    updateStats(results) {
        if (!results) return;
        
        // Update FPS counter
        const fpsElement = this.element.querySelector('#fpsCounter');
        if (fpsElement && results.fps !== undefined) {
            this.stats.fps = results.fps;
            fpsElement.textContent = results.fps.toFixed(1);
            
            // Add animation if FPS changed significantly
            if (Math.abs(results.fps - this.stats.fps) > 5) {
                this.app.ui.addAnimation(fpsElement, 'fadeIn');
            }
        }
        
        // Update frame counter
        const frameElement = this.element.querySelector('#frameCounter');
        if (frameElement && results.frame_count !== undefined) {
            this.stats.frameCount = results.frame_count;
            frameElement.textContent = results.frame_count.toLocaleString();
            
            // Add animation every 100 frames
            if (results.frame_count % 100 === 0) {
                this.app.ui.addAnimation(frameElement, 'fadeIn');
            }
        }
        
        // Update processing time
        const processingElement = this.element.querySelector('#processingTime');
        if (processingElement && results.processing_time !== undefined) {
            this.stats.processingTime = results.processing_time;
            processingElement.textContent = results.processing_time.toFixed(1);
        }
        
        // Update AI mode
        const aiModeElement = this.element.querySelector('#aiMode');
        if (aiModeElement && results.ai_mode) {
            aiModeElement.textContent = results.ai_mode;
            
            // Add appropriate color class
            aiModeElement.className = '';
            if (results.ai_mode.includes('SIMULATION')) {
                aiModeElement.classList.add('text-warning');
            } else if (results.ai_mode.includes('REAL')) {
                aiModeElement.classList.add('text-success');
            }
        }
    }
    
    updateProctoringState(isActive) {
        const startBtn = this.element.querySelector('#startBtn');
        const stopBtn = this.element.querySelector('#stopBtn');
        const screenshotBtn = this.element.querySelector('#screenshotBtn');
        
        if (isActive) {
            // Active state
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.classList.remove('btn-success');
                startBtn.classList.add('btn-outline');
            }
            
            if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.classList.remove('btn-outline');
                stopBtn.classList.add('btn-danger');
            }
            
            if (screenshotBtn) {
                screenshotBtn.disabled = false;
            }
        } else {
            // Inactive state
            if (startBtn) {
                startBtn.disabled = false;
                startBtn.classList.remove('btn-outline');
                startBtn.classList.add('btn-success');
            }
            
            if (stopBtn) {
                stopBtn.disabled = true;
                stopBtn.classList.remove('btn-danger');
                stopBtn.classList.add('btn-outline');
            }
            
            if (screenshotBtn) {
                screenshotBtn.disabled = true;
            }
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
    module.exports = { VideoComponent };
}