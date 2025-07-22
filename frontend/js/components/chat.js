class ChatComponent {
    constructor() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.isWaitingForResponse = false;

        this.setupEventListeners();
        this.setupWebSocketHandlers();
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.chatInput.addEventListener('input', () => {
            this.adjustTextareaHeight();
        });
    }

    setupWebSocketHandlers() {
        window.wsManager.on('chat_response', (data) => {
            this.handleChatResponse(data);
        });

        window.wsManager.on('chat_stream', (data) => {
            this.handleChatStream(data);
        });

        window.wsManager.on('chat_error', (data) => {
            this.handleChatError(data);
        });

        window.wsManager.on('connection', (data) => {
            if (data.state === 'connected') {
                this.removeSystemMessage('connection-lost');
            } else if (data.state === 'disconnected' || data.state === 'error') {
                this.addSystemMessage('Connection lost. Attempting to reconnect...', 'connection-lost');
            }
        });
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isWaitingForResponse) return;

        const llmProvider = document.getElementById('llm-provider').value;
        if (!llmProvider) {
            this.addSystemMessage('Please select an LLM provider first.');
            return;
        }

        const selectedTools = window.toolsComponent.getSelectedTools();

        this.addMessage(message, 'user');
        this.chatInput.value = '';
        this.adjustTextareaHeight();
        this.setWaitingState(true);

        try {
            if (window.wsManager.getConnectionState() === 'connected') {
                window.wsManager.send('chat_message', {
                    message,
                    llm_provider: llmProvider,
                    selected_tools: selectedTools
                });
            } else {
                await window.apiClient.sendChatMessage(message, llmProvider, selectedTools);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage(`Error: ${error.message}`, 'error');
            this.setWaitingState(false);
        }
    }

    handleChatResponse(data) {
        this.removeTypingIndicator();
        this.addMessage(data.content, 'assistant');
        this.setWaitingState(false);
    }

    handleChatStream(data) {
        if (data.start) {
            this.addTypingIndicator();
        } else if (data.end) {
            this.removeTypingIndicator();
            this.setWaitingState(false);
        } else if (data.content) {
            this.updateStreamingMessage(data.content);
        }
    }

    handleChatError(data) {
        this.removeTypingIndicator();
        this.addMessage(`Error: ${data.error}`, 'error');
        this.setWaitingState(false);
    }

    addMessage(content, type = 'assistant', id = null) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        if (id) messageEl.id = id;

        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        contentEl.textContent = content;

        const metaEl = document.createElement('div');
        metaEl.className = 'message-meta';
        metaEl.textContent = new Date().toLocaleTimeString();

        messageEl.appendChild(contentEl);
        messageEl.appendChild(metaEl);
        
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();

        return messageEl;
    }

    addSystemMessage(content, id = null) {
        return this.addMessage(content, 'system', id);
    }

    removeSystemMessage(id) {
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    }

    addTypingIndicator() {
        if (document.getElementById('typing-indicator')) return;

        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'typing-indicator';
        indicator.textContent = 'Thinking...';
        
        this.messagesContainer.appendChild(indicator);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    updateStreamingMessage(content) {
        let streamingMessage = document.getElementById('streaming-message');
        if (!streamingMessage) {
            streamingMessage = this.addMessage('', 'assistant', 'streaming-message');
        }

        const contentEl = streamingMessage.querySelector('.message-content');
        contentEl.textContent += content;
        this.scrollToBottom();
    }

    setWaitingState(waiting) {
        this.isWaitingForResponse = waiting;
        this.sendButton.disabled = waiting;
        this.chatInput.disabled = waiting;

        if (waiting) {
            this.addTypingIndicator();
        }
    }

    adjustTextareaHeight() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}

window.chatComponent = new ChatComponent();