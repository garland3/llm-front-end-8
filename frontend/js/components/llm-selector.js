class LLMSelectorComponent {
    constructor() {
        this.selector = document.getElementById('llm-provider');
        this.providers = [];
        this.storageKey = 'llm-frontend-selected-provider';
        
        this.setupEventListeners();
        this.loadProviders();
    }

    setupEventListeners() {
        this.selector.addEventListener('change', () => {
            this.saveSelectedProvider();
        });
    }

    async loadProviders() {
        try {
            this.providers = await window.apiClient.getLLMProviders();
            this.renderProviders();
            this.restoreSelectedProvider();
        } catch (error) {
            console.error('Error loading LLM providers:', error);
            this.showError('Failed to load LLM providers');
        }
    }

    renderProviders() {
        this.selector.innerHTML = '<option value="">Select LLM...</option>';
        
        this.providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.id;
            option.textContent = `${provider.name} - ${provider.model}`;
            option.disabled = !provider.available;
            
            if (!provider.available) {
                option.textContent += ' (Unavailable)';
            }
            
            this.selector.appendChild(option);
        });

        if (this.providers.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No providers available';
            option.disabled = true;
            this.selector.appendChild(option);
        }
    }

    showError(message) {
        this.selector.innerHTML = `<option value="" disabled>${message}</option>`;
    }

    getSelectedProvider() {
        return this.selector.value;
    }

    getProviderInfo(providerId) {
        return this.providers.find(p => p.id === providerId);
    }

    saveSelectedProvider() {
        const selectedId = this.selector.value;
        if (selectedId) {
            localStorage.setItem(this.storageKey, selectedId);
        }
    }

    getSavedProvider() {
        return localStorage.getItem(this.storageKey);
    }

    restoreSelectedProvider() {
        const savedProviderId = this.getSavedProvider();
        const availableProviders = this.providers.filter(p => p.available);
        
        if (savedProviderId && availableProviders.find(p => p.id === savedProviderId)) {
            // Restore saved selection if it's still available
            this.selector.value = savedProviderId;
        } else if (availableProviders.length > 0) {
            // Select first available provider as default
            this.selector.value = availableProviders[0].id;
            this.saveSelectedProvider();
        }
    }
}

window.llmSelectorComponent = new LLMSelectorComponent();