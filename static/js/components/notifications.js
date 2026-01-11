// Notifications Component (Fixed filename from notifications.js to notification.js)
class NotificationsComponent {
    constructor(app) {
        this.app = app;
        this.element = null;
        this.notificationQueue = [];
        this.isShowing = false;
        this.init();
    }
    
    init() {
        this.createElement();
        this.render();
    }
    
    createElement() {
        const toast = document.createElement('div');
        toast.id = 'toast-notification';
        toast.className = 'toast-notification';
        toast.setAttribute('aria-live', 'polite');
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="toast-content">
                <i class="toast-icon"></i>
                <span class="toast-message"></span>
            </div>
            <button class="toast-close" aria-label="Close notification">&times;</button>
        `;
        
        this.element = toast;
    }
    
    render() {
        const existingToast = document.getElementById('toast-notification');
        if (existingToast) {
            existingToast.replaceWith(this.element);
        } else {
            document.body.appendChild(this.element);
        }
        
        // Add close button event listener
        const closeBtn = this.element.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hide();
            });
        }
    }
    
    show(message, type = 'info', duration = 5000) {
        // Add to queue
        this.notificationQueue.push({ message, type, duration });
        
        // Show if not already showing
        if (!this.isShowing) {
            this.showNext();
        }
    }
    
    showNext() {
        if (this.notificationQueue.length === 0) {
            this.isShowing = false;
            return;
        }
        
        this.isShowing = true;
        const notification = this.notificationQueue.shift();
        
        // Update toast content
        const icon = this.element.querySelector('.toast-icon');
        const message = this.element.querySelector('.toast-message');
        
        if (icon && message) {
            // Set icon based on type
            icon.className = 'toast-icon fas';
            switch (notification.type) {
                case 'success':
                    icon.classList.add('fa-check-circle');
                    break;
                case 'error':
                    icon.classList.add('fa-exclamation-circle');
                    break;
                case 'warning':
                    icon.classList.add('fa-exclamation-triangle');
                    break;
                default:
                    icon.classList.add('fa-info-circle');
            }
            
            message.textContent = notification.message;
            
            // Set type class
            this.element.className = 'toast-notification';
            this.element.classList.add(notification.type);
            this.element.classList.add('show');
            
            // Auto-hide after duration
            setTimeout(() => {
                this.hide();
            }, notification.duration);
        }
    }
    
    hide() {
        this.element.classList.remove('show');
        
        // Wait for animation to complete before showing next
        setTimeout(() => {
            this.showNext();
        }, 300);
    }
    
    showScreenshotPreview(imageData) {
        const modalContent = `
            <div class="screenshot-preview">
                <h4>Screenshot Preview</h4>
                <div class="preview-image">
                    <img src="${imageData}" alt="Screenshot preview" style="max-width: 100%; border-radius: 8px;">
                </div>
                <div class="preview-actions mt-3">
                    <button class="btn btn-success" id="saveScreenshot">
                        <i class="fas fa-save"></i> Save
                    </button>
                    <button class="btn btn-outline" id="copyScreenshot">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;
        
        const modal = this.app.ui.showModal('Screenshot', modalContent, [
            {
                text: 'Close',
                class: 'btn-primary',
                closeOnClick: true
            }
        ]);
        
        // Add event listeners for preview buttons
        setTimeout(() => {
            const saveBtn = modal.querySelector('#saveScreenshot');
            const copyBtn = modal.querySelector('#copyScreenshot');
            
            if (saveBtn) {
                saveBtn.addEventListener('click', () => {
                    this.saveScreenshot(imageData);
                });
            }
            
            if (copyBtn) {
                copyBtn.addEventListener('click', () => {
                    this.copyScreenshot(imageData);
                });
            }
        }, 100);
    }
    
    saveScreenshot(imageData) {
        // Create a temporary link to download the image
        const link = document.createElement('a');
        link.href = imageData;
        link.download = `screenshot_${new Date().getTime()}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.app.showNotification('Screenshot saved', 'success');
    }
    
    async copyScreenshot(imageData) {
        try {
            // Convert base64 to blob
            const response = await fetch(imageData);
            const blob = await response.blob();
            
            // Copy to clipboard
            await navigator.clipboard.write([
                new ClipboardItem({
                    [blob.type]: blob
                })
            ]);
            
            this.app.showNotification('Screenshot copied to clipboard', 'success');
        } catch (error) {
            console.error('Failed to copy screenshot:', error);
            this.app.showNotification('Failed to copy screenshot', 'error');
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
    module.exports = { NotificationsComponent };
}