/**
 * Copy-Paste Monitor for Exam Integrity
 * Tracks clipboard events during exam
 */
class CopyPasteMonitor {
    constructor() {
        this.enabled = false;
        this.violations = [];
        this.maxViolations = 100; // Prevent memory leak
        
        this.eventHandlers = {
            copy: null,
            cut: null,
            paste: null,
            contextmenu: null
        };
    }
    
    /**
     * Start monitoring clipboard events
     */
    start() {
        if (this.enabled) {
            console.warn('Copy-paste monitor already running');
            return;
        }
        
        console.log('📋 Starting copy-paste monitor...');
        
        // Track copy events
        this.eventHandlers.copy = (e) => this.handleCopy(e);
        document.addEventListener('copy', this.eventHandlers.copy);
        
        // Track cut events
        this.eventHandlers.cut = (e) => this.handleCut(e);
        document.addEventListener('cut', this.eventHandlers.cut);
        
        // Track paste events
        this.eventHandlers.paste = (e) => this.handlePaste(e);
        document.addEventListener('paste', this.eventHandlers.paste);
        
        // Disable right-click (optional - can be annoying)
        // this.eventHandlers.contextmenu = (e) => this.handleContextMenu(e);
        // document.addEventListener('contextmenu', this.eventHandlers.contextmenu);
        
        this.enabled = true;
        console.log('✅ Copy-paste monitor started');
    }
    
    /**
     * Stop monitoring
     */
    stop() {
        if (!this.enabled) {
            return;
        }
        
        console.log('📋 Stopping copy-paste monitor...');
        
        // Remove event listeners
        if (this.eventHandlers.copy) {
            document.removeEventListener('copy', this.eventHandlers.copy);
        }
        if (this.eventHandlers.cut) {
            document.removeEventListener('cut', this.eventHandlers.cut);
        }
        if (this.eventHandlers.paste) {
            document.removeEventListener('paste', this.eventHandlers.paste);
        }
        if (this.eventHandlers.contextmenu) {
            document.removeEventListener('contextmenu', this.eventHandlers.contextmenu);
        }
        
        this.enabled = false;
        console.log('✅ Copy-paste monitor stopped');
    }
    
    /**
     * Handle copy event
     */
    handleCopy(event) {
        const selectedText = window.getSelection().toString();
        
        const violation = {
            type: 'COPY',
            timestamp: new Date().toISOString(),
            textLength: selectedText.length,
            textPreview: selectedText.substring(0, 100), // First 100 chars
            source: this.getSourceElement(event.target)
        };
        
        this.recordViolation(violation);
        
        console.warn('⚠️ Copy detected:', violation);
        
        // Optionally prevent copy (strict mode)
        // event.preventDefault();
        // alert('Copying is not allowed during the exam!');
    }
    
    /**
     * Handle cut event
     */
    handleCut(event) {
        const selectedText = window.getSelection().toString();
        
        const violation = {
            type: 'CUT',
            timestamp: new Date().toISOString(),
            textLength: selectedText.length,
            textPreview: selectedText.substring(0, 100),
            source: this.getSourceElement(event.target)
        };
        
        this.recordViolation(violation);
        
        console.warn('⚠️ Cut detected:', violation);
        
        // Optionally prevent cut
        // event.preventDefault();
    }
    
    /**
     * Handle paste event
     */
    async handlePaste(event) {
        let pastedText = '';
        
        // Get pasted text
        if (event.clipboardData) {
            pastedText = event.clipboardData.getData('text/plain');
        }
        
        const violation = {
            type: 'PASTE',
            timestamp: new Date().toISOString(),
            textLength: pastedText.length,
            textPreview: pastedText.substring(0, 100),
            target: this.getSourceElement(event.target)
        };
        
        this.recordViolation(violation);
        
        console.warn('⚠️ Paste detected:', violation);
        
        // Optionally prevent paste (strict mode)
        // event.preventDefault();
        // alert('Pasting is not allowed during the exam!');
        
        // Optionally analyze pasted text with AI
        if (pastedText.length > 50) {
            this.analyzePastedText(pastedText);
        }
    }
    
    /**
     * Handle right-click context menu
     */
    handleContextMenu(event) {
        const violation = {
            type: 'CONTEXT_MENU',
            timestamp: new Date().toISOString(),
            element: this.getSourceElement(event.target)
        };
        
        this.recordViolation(violation);
        
        console.warn('⚠️ Right-click detected:', violation);
        
        // Prevent context menu
        event.preventDefault();
        return false;
    }
    
    /**
     * Get source element info
     */
    getSourceElement(element) {
        return {
            tagName: element.tagName,
            id: element.id || 'none',
            className: element.className || 'none',
            type: element.type || 'none'
        };
    }
    
    /**
     * Record violation
     */
    recordViolation(violation) {
        this.violations.push(violation);
        
        // Prevent memory leak
        if (this.violations.length > this.maxViolations) {
            this.violations.shift(); // Remove oldest
        }
        
        // Dispatch custom event for app to handle
        const event = new CustomEvent('clipboardViolation', {
            detail: violation
        });
        window.dispatchEvent(event);
    }
    
    /**
     * Analyze pasted text with AI (optional)
     */
    async analyzePastedText(text) {
        try {
            // Send to backend for AI analysis
            const response = await fetch('/api/analyze_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });
            
            const result = await response.json();
            
            if (result.success && result.data.is_ai_generated) {
                console.error('🚨 AI-generated text pasted!', result.data);
                
                // Alert user
                alert('⚠️ Warning: The pasted text appears to be AI-generated!');
            }
        } catch (error) {
            console.error('Failed to analyze pasted text:', error);
        }
    }
    
    /**
     * Get violation statistics
     */
    getStats() {
        const stats = {
            total: this.violations.length,
            byType: {},
            recent: this.violations.slice(-10) // Last 10
        };
        
        // Count by type
        this.violations.forEach(v => {
            stats.byType[v.type] = (stats.byType[v.type] || 0) + 1;
        });
        
        return stats;
    }
    
    /**
     * Get all violations
     */
    getViolations() {
        return [...this.violations]; // Return copy
    }
    
    /**
     * Clear violations
     */
    clearViolations() {
        this.violations = [];
        console.log('📋 Violations cleared');
    }
    
    /**
     * Generate report
     */
    generateReport() {
        const stats = this.getStats();
        
        return {
            monitored: this.enabled,
            totalViolations: stats.total,
            violationsByType: stats.byType,
            recentViolations: stats.recent,
            timestamp: new Date().toISOString()
        };
    }
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CopyPasteMonitor };
}