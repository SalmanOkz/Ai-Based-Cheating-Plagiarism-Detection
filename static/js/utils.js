// Utility Functions
class Utils {
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    static formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    static formatDate(date, format = 'default') {
        const d = new Date(date);
        
        if (format === 'relative') {
            const now = new Date();
            const diff = now - d;
            const seconds = Math.floor(diff / 1000);
            
            if (seconds < 60) return 'Just now';
            
            const minutes = Math.floor(seconds / 60);
            if (minutes < 60) return `${minutes}m ago`;
            
            const hours = Math.floor(minutes / 60);
            if (hours < 24) return `${hours}h ago`;
            
            const days = Math.floor(hours / 24);
            if (days < 7) return `${days}d ago`;
            
            return d.toLocaleDateString();
        }
        
        if (format === 'time') {
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        if (format === 'datetime') {
            return d.toLocaleString();
        }
        
        // Default format
        return d.toLocaleDateString();
    }
    
    static generateId(length = 8) {
        return Math.random().toString(36).substring(2, 2 + length);
    }
    
    static deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }
    
    static getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    
    static setCookie(name, value, days = 7) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value}; expires=${date.toUTCString()}; path=/`;
    }
    
    static removeCookie(name) {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    }
    
    static isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    static isTouchDevice() {
        return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    }
    
    static getBrowserInfo() {
        const ua = navigator.userAgent;
        let browser = 'Unknown';
        let version = 'Unknown';
        
        // Detect browser
        if (ua.includes('Firefox')) {
            browser = 'Firefox';
            version = ua.match(/Firefox\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.includes('Chrome') && !ua.includes('Edg')) {
            browser = 'Chrome';
            version = ua.match(/Chrome\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
            browser = 'Safari';
            version = ua.match(/Version\/([0-9.]+)/)?.[1] || 'Unknown';
        } else if (ua.includes('Edg')) {
            browser = 'Edge';
            version = ua.match(/Edg\/([0-9.]+)/)?.[1] || 'Unknown';
        }
        
        return { browser, version };
    }
    
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    static validateUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
    
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            } catch (err) {
                document.body.removeChild(textArea);
                return false;
            }
        }
    }
    
    static randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    
    static randomColor() {
        return `#${Math.floor(Math.random() * 16777215).toString(16)}`;
    }
    
    static measurePerformance(fn, label = 'Function') {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        console.log(`${label} took ${(end - start).toFixed(2)}ms`);
        return result;
    }
}

// DOM Utility Functions
class DOMUtils {
    static createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        // Set attributes
        for (const [key, value] of Object.entries(attributes)) {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(element.style, value);
            } else {
                element.setAttribute(key, value);
            }
        }
        
        // Add children
        if (Array.isArray(children)) {
            children.forEach(child => {
                if (child instanceof HTMLElement) {
                    element.appendChild(child);
                } else if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                }
            });
        }
        
        return element;
    }
    
    static removeAllChildren(element) {
        while (element.firstChild) {
            element.removeChild(element.firstChild);
        }
    }
    
    static addClass(element, className) {
        if (element) {
            element.classList.add(className);
        }
    }
    
    static removeClass(element, className) {
        if (element) {
            element.classList.remove(className);
        }
    }
    
    static toggleClass(element, className) {
        if (element) {
            element.classList.toggle(className);
        }
    }
    
    static hasClass(element, className) {
        return element ? element.classList.contains(className) : false;
    }
    
    static getScrollPosition() {
        return {
            x: window.pageXOffset || document.documentElement.scrollLeft,
            y: window.pageYOffset || document.documentElement.scrollTop
        };
    }
    
    static scrollTo(element, behavior = 'smooth') {
        element.scrollIntoView({ behavior, block: 'start' });
    }
    
    static isElementInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    static getElementCenter(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };
    }
    
    static observeElement(element, callback, options = {}) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                callback(entry.isIntersecting, entry);
            });
        }, options);
        
        observer.observe(element);
        return observer;
    }
}

// Event Utility Functions
class EventUtils {
    static on(element, event, handler, options = {}) {
        element.addEventListener(event, handler, options);
        return () => element.removeEventListener(event, handler, options);
    }
    
    static off(element, event, handler, options = {}) {
        element.removeEventListener(event, handler, options);
    }
    
    static once(element, event, handler) {
        const onceHandler = (...args) => {
            handler(...args);
            element.removeEventListener(event, onceHandler);
        };
        element.addEventListener(event, onceHandler);
    }
    
    static triggerEvent(element, eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        element.dispatchEvent(event);
    }
    
    static preventDefault(event) {
        event.preventDefault();
    }
    
    static stopPropagation(event) {
        event.stopPropagation();
    }
}

// Storage Utility Functions
class StorageUtils {
    static set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('LocalStorage set error:', error);
            return false;
        }
    }
    
    static get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('LocalStorage get error:', error);
            return defaultValue;
        }
    }
    
    static remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('LocalStorage remove error:', error);
            return false;
        }
    }
    
    static clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('LocalStorage clear error:', error);
            return false;
        }
    }
    
    static has(key) {
        return localStorage.getItem(key) !== null;
    }
}

// Export utilities
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        Utils,
        DOMUtils,
        EventUtils,
        StorageUtils
    };
}