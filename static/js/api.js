// API Handler Class
class APIHandler {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        
        // Request timeout (5 seconds)
        this.timeout = 5000;
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        const config = {
            ...options,
            headers: { ...this.defaultHeaders, ...options.headers },
            signal: controller.signal
        };
        
        try {
            const response = await fetch(url, config);
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            
            throw error;
        }
    }
    
    // System endpoints
    async getSystemStatus() {
        return this.request('/api/system_status');
    }
    
    // Proctoring endpoints
    async startProctoring(cameraId = 0) {
        return this.request('/api/start_proctoring', {
            method: 'POST',
            body: JSON.stringify({ camera_id: cameraId })
        });
    }
    
    async stopProctoring() {
        return this.request('/api/stop_proctoring', {
            method: 'POST'
        });
    }
    
    async getProctoringResults() {
        return this.request('/api/proctoring_results');
    }
    
    async takeScreenshot() {
        return this.request('/api/take_screenshot', {
            method: 'POST'
        });
    }
    
    async debugDetection() {
        return this.request('/api/debug_detection');
    }
    
    // Integrity Auditor endpoints
    async analyzeText(text) {
        return this.request('/api/analyze_text', {
            method: 'POST',
            body: JSON.stringify({ text })
        });
    }
    
    async checkCodePlagiarism(code1, code2, language = 'python') {
        return this.request('/api/check_code_plagiarism', {
            method: 'POST',
            body: JSON.stringify({ code1, code2, language })
        });
    }
    
    async compareCodeFiles(file1, file2) {
        const formData = new FormData();
        formData.append('file1', file1);
        formData.append('file2', file2);
        
        return this.request('/api/compare_code_files', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content type for FormData
        });
    }
    
    // Test endpoints
    async testAI() {
        return this.request('/api/test_ai');
    }
    
    // Utility method for streaming
    async getVideoStream() {
        return `${this.baseURL}/video_feed`;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIHandler };
}