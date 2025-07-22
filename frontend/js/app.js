class App {
    constructor() {
        this.init();
    }

    async init() {
        this.showUserInfo();
        this.connectWebSocket();
        this.setupGlobalErrorHandling();
        
        window.addEventListener('beforeunload', () => {
            window.wsManager.disconnect();
        });
    }

    showUserInfo() {
        const userEmailEl = document.getElementById('user-email');
        userEmailEl.textContent = 'Loading...';
        
        setTimeout(() => {
            userEmailEl.textContent = 'test@test.com';
        }, 500);
    }

    connectWebSocket() {
        window.wsManager.connect();
        
        window.wsManager.on('connection', (data) => {
            const statusEl = this.getOrCreateStatusElement();
            
            switch (data.state) {
                case 'connected':
                    statusEl.textContent = 'Connected';
                    statusEl.className = 'connection-status connected';
                    break;
                case 'disconnected':
                case 'error':
                    statusEl.textContent = 'Disconnected';
                    statusEl.className = 'connection-status disconnected';
                    break;
                case 'failed':
                    statusEl.textContent = 'Connection Failed';
                    statusEl.className = 'connection-status failed';
                    break;
            }
        });
    }

    getOrCreateStatusElement() {
        let statusEl = document.getElementById('connection-status');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'connection-status';
            statusEl.className = 'connection-status';
            
            const userInfo = document.querySelector('.user-info');
            userInfo.appendChild(statusEl);
        }
        return statusEl;
    }

    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.showNotification(`Error: ${event.error.message}`, 'error');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showNotification(`Promise rejection: ${event.reason}`, 'error');
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});