class ToolsComponent {
    constructor() {
        this.exclusiveContainer = document.getElementById('exclusive-tools');
        this.multipleContainer = document.getElementById('multiple-tools');
        this.tools = [];
        this.selectedExclusiveTool = null;
        this.selectedMultipleTools = new Set();

        this.loadTools();
    }

    async loadTools() {
        try {
            this.tools = await window.apiClient.getMCPTools();
            await this.validateToolAccess();
            this.renderTools();
        } catch (error) {
            console.error('Error loading MCP tools:', error);
            this.showError('Failed to load MCP tools');
        }
    }

    async validateToolAccess() {
        try {
            const toolIds = this.tools.map(tool => tool.id);
            const validation = await window.apiClient.validateMCPAccess(toolIds);
            
            this.tools.forEach(tool => {
                const access = validation.find(v => v.tool_id === tool.id);
                tool.hasAccess = access ? access.has_access : false;
                tool.accessReason = access ? access.reason : 'Unknown';
            });
        } catch (error) {
            console.error('Error validating tool access:', error);
        }
    }

    renderTools() {
        this.renderExclusiveTools();
        this.renderMultipleTools();
    }

    renderExclusiveTools() {
        const exclusiveTools = this.tools.filter(tool => tool.exclusive);
        
        if (exclusiveTools.length === 0) {
            this.exclusiveContainer.innerHTML = '<p class="no-tools">No exclusive tools available</p>';
            return;
        }

        this.exclusiveContainer.innerHTML = '';
        
        exclusiveTools.forEach(tool => {
            const toolEl = this.createToolElement(tool, 'radio');
            this.exclusiveContainer.appendChild(toolEl);
        });
    }

    renderMultipleTools() {
        const multipleTools = this.tools.filter(tool => !tool.exclusive);
        
        if (multipleTools.length === 0) {
            this.multipleContainer.innerHTML = '<p class="no-tools">No multiple tools available</p>';
            return;
        }

        this.multipleContainer.innerHTML = '';
        
        multipleTools.forEach(tool => {
            const toolEl = this.createToolElement(tool, 'checkbox');
            this.multipleContainer.appendChild(toolEl);
        });
    }

    createToolElement(tool, inputType) {
        const toolEl = document.createElement('div');
        toolEl.className = `tool-item ${tool.exclusive ? 'exclusive-tool' : 'multiple-tool'}`;
        
        if (!tool.hasAccess) {
            toolEl.classList.add('disabled');
        }

        const header = document.createElement('div');
        header.className = 'tool-header';

        const input = document.createElement('input');
        input.type = inputType;
        input.className = 'tool-input';
        input.value = tool.id;
        input.disabled = !tool.hasAccess;

        if (inputType === 'radio') {
            input.name = 'exclusive-tool';
            input.addEventListener('change', () => {
                if (input.checked) {
                    this.selectedExclusiveTool = tool.id;
                    this.updateToolSelection();
                }
            });
        } else {
            input.addEventListener('change', () => {
                if (input.checked) {
                    this.selectedMultipleTools.add(tool.id);
                } else {
                    this.selectedMultipleTools.delete(tool.id);
                }
                this.updateToolSelection();
            });
        }

        const name = document.createElement('span');
        name.className = 'tool-name';
        name.textContent = tool.name;

        const status = document.createElement('span');
        status.className = `tool-status ${tool.hasAccess ? 'available' : 'unavailable'}`;

        header.appendChild(input);
        header.appendChild(name);
        header.appendChild(status);

        if (!tool.hasAccess) {
            const authRequired = document.createElement('span');
            authRequired.className = 'tool-auth-required';
            authRequired.textContent = tool.accessReason || 'Access denied';
            header.appendChild(authRequired);
        }

        toolEl.appendChild(header);

        if (tool.description) {
            const description = document.createElement('div');
            description.className = 'tool-description';
            description.textContent = tool.description;
            toolEl.appendChild(description);
        }

        return toolEl;
    }

    updateToolSelection() {
        document.querySelectorAll('.tool-item').forEach(item => {
            item.classList.remove('selected');
        });

        if (this.selectedExclusiveTool) {
            const exclusiveInput = document.querySelector(`input[value="${this.selectedExclusiveTool}"]`);
            if (exclusiveInput) {
                exclusiveInput.closest('.tool-item').classList.add('selected');
            }
        }

        this.selectedMultipleTools.forEach(toolId => {
            const multipleInput = document.querySelector(`input[type="checkbox"][value="${toolId}"]`);
            if (multipleInput && multipleInput.checked) {
                multipleInput.closest('.tool-item').classList.add('selected');
            }
        });
    }

    getSelectedTools() {
        const selected = [];
        
        if (this.selectedExclusiveTool) {
            selected.push(this.selectedExclusiveTool);
        }
        
        selected.push(...Array.from(this.selectedMultipleTools));
        
        return selected;
    }

    showError(message) {
        this.exclusiveContainer.innerHTML = `<p class="error">${message}</p>`;
        this.multipleContainer.innerHTML = '';
    }

    async refreshTools() {
        await this.loadTools();
    }
}

window.toolsComponent = new ToolsComponent();