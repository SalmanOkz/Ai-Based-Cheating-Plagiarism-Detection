/**
 * Toast Notification System
 * Displays temporary notifications to users
 */

class ToastNotification {
    constructor() {
        this.container = this.createContainer();
        this.queue = [];
        this.isShowing = false;
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.style.cssText = `
            padding: 16px 20px;
            border-radius: 8px;
            background-color: ${colors[type] || colors.info};
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            min-width: 280px;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: auto;
            font-size: 14px;
        `;

        toast.innerHTML = `
            <span style="font-size: 18px; font-weight: bold;">${icons[type] || icons.info}</span>
            <span style="flex: 1;">${message}</span>
        `;

        this.container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, duration);
    }

    success(message, duration = 3000) {
        this.show(message, 'success', duration);
    }

    error(message, duration = 4000) {
        this.show(message, 'error', duration);
    }

    warning(message, duration = 3500) {
        this.show(message, 'warning', duration);
    }

    info(message, duration = 3000) {
        this.show(message, 'info', duration);
    }
}

// Add animations if not already present
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Create global toast instance
window.toast = new ToastNotification();

// Export for module systems if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastNotification;
}