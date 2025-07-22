class ApiClient {
    constructor() {
        this.baseUrl = '';
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    async post(endpoint, data = null, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'POST',
            body: data
        });
    }

    async put(endpoint, data = null, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PUT',
            body: data
        });
    }

    async delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }

    async getLLMProviders() {
        return this.get('/api/llm/providers');
    }

    async getMCPTools() {
        return this.get('/api/mcp/tools');
    }

    async getMCPResources(toolId) {
        return this.get(`/api/mcp/tools/${toolId}/resources`);
    }

    async validateMCPAccess(toolIds) {
        return this.post('/api/mcp/validate', { tool_ids: toolIds });
    }

    async sendChatMessage(message, llmProvider, selectedTools = []) {
        return this.post('/api/chat/message', {
            message,
            llm_provider: llmProvider,
            selected_tools: selectedTools
        });
    }
}

window.apiClient = new ApiClient();