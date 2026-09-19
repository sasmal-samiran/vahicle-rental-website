import { API } from './api.js';
import { CONFIG } from './config.js';
import { Toast } from './toast.js';
import { Auth } from './auth.js';
import { Customer } from './customer.js';
import { executeWebpageAction } from './automation.js';

export const Assistant = {
    isOpen: false,
    isExpanded: false,
    isLoading: false,
    abortController: null,
    storageKey: 'cr_assistant_chat_history_v1',
    messages: [],

    init() {
        this.cacheDom();
        if (!this.dom.widget) return;
        this.bindEvents();
        this.loadHistory();
        this.updateAuthUi();
        this.renderInitialState();
        this.open();
    },

    cacheDom() {
        this.dom = {
            widget: document.getElementById('smart-assistant-widget'),
            chatWindow: document.getElementById('assistant-chat-window'),
            messagesContainer: document.getElementById('assistant-messages-container'),
            form: document.getElementById('assistant-input-form'),
            input: document.getElementById('assistant-input'),
            sendBtn: document.getElementById('assistant-send-btn'),
            stopBtn: document.getElementById('assistant-stop-btn'),
            charCounter: document.getElementById('assistant-char-counter'),
            clearBtn: document.getElementById('assistant-clear-btn'),
            footerExpandBtn: document.getElementById('assistant-footer-expand-btn'),
            closeBtn: document.getElementById('assistant-close-btn')
        };
    },

    bindEvents() {
        // Close button
        this.dom.closeBtn?.addEventListener('click', () => this.close());

        this.dom.footerExpandBtn?.addEventListener('click', () => this.toggleChatSize());

        // Clear history button
        this.dom.clearBtn?.addEventListener('click', () => this.clearHistory());

        // Stop Generating Button
        this.dom.stopBtn?.addEventListener('click', () => this.stopGenerating());

        // Auto-resizing textarea and input validation
        this.dom.input?.addEventListener('input', () => {
            this.handleInputChange();
        });

        // Keydown handling (Enter to send, Shift+Enter for newline)
        this.dom.input?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!this.dom.sendBtn.disabled && !this.isLoading) {
                    this.dom.form.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            }
        });

        // Form submission
        this.dom.form?.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = this.dom.input.value.trim();
            if (text && !this.isLoading) {
                this.sendMessage(text);
            }
        });

        // Close on escape key if open
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // React dynamically to login / logout events across the application
        document.addEventListener('auth:change', (event) => {
            this.handleAuthChange(event.detail?.user);
        });
    },

    isUserAuthenticated() {
        return API.isAuthenticated();
    },

    getCurrentUser() {
        return API.getUser();
    },

    getEndpoint() {
        return this.isUserAuthenticated() ? '/assistant/private/' : '/assistant/public/';
    },

    updateAuthUi() {
        const isAuth = this.isUserAuthenticated();

        // Update Textarea Placeholder
        if (this.dom.input) {
            this.dom.input.placeholder = 'Ask here ...';
        }
    },

    handleAuthChange(user) {
        this.updateAuthUi();

        if (this.messages.length === 0) {
            this.renderInitialState();
        } else {
            const isAuth = !!user;
            const sysText = isAuth
                ? `✨ Switched to VIP Private Concierge (Connected as ${user.first_name || user.email || 'User'}).`
                : 'Switched to Public Concierge mode.';

            const sysMsg = {
                id: 'sys_' + Date.now(),
                sender: 'system',
                text: sysText,
                timestamp: new Date().toISOString()
            };

            this.messages.push(sysMsg);
            this.renderMessageElement(sysMsg, true);
            this.saveHistory();
        }
    },

    handleInputChange() {
        const textarea = this.dom.input;
        if (!textarea) return;

        textarea.style.height = 'auto';
        textarea.style.height = `${Math.min(textarea.scrollHeight, 100)}px`;

        const val = textarea.value.trim();
        const hasContent = val.length > 0;
        this.dom.sendBtn.disabled = !hasContent || this.isLoading;

        if (this.dom.charCounter) {
            this.dom.charCounter.textContent = `${val.length}/1000`;
            this.dom.charCounter.style.color = val.length >= 900 ? 'var(--danger)' : 'var(--primary)';
        }
    },

    toggle() {
        if (!this.dom.chatWindow) this.cacheDom();
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    },

    open(expanded = null) {
        if (!this.dom.chatWindow) this.cacheDom();
        this.isOpen = true;
        if (expanded !== null && expanded !== undefined) {
            this.isExpanded = Boolean(expanded);
        } else {
            this.isExpanded = sessionStorage.getItem('cr_assistant_is_expanded') === 'true';
        }
        sessionStorage.setItem('cr_assistant_is_expanded', String(this.isExpanded));
        this.dom.chatWindow?.classList.toggle('compact', !this.isExpanded);
        this.dom.chatWindow?.classList.toggle('expanded', this.isExpanded);
        this.updateChatSizeButton();
        sessionStorage.setItem('cr_assistant_is_open', 'true');
        this.dom.chatWindow?.classList.remove('hidden');
        document.body.style.overflow = this.isExpanded && window.innerWidth <= 1024
            ? 'hidden'
            : '';

        this.scrollToBottom();

        if (window.innerWidth > 1024) {
            setTimeout(() => this.dom.input?.focus(), 150);
        }
    },

    expand() {
        this.open(true);
    },

    close() {
        if (!this.dom.chatWindow) this.cacheDom();
        this.isOpen = true;
        this.isExpanded = false;
        sessionStorage.setItem('cr_assistant_is_expanded', 'false');
        this.dom.chatWindow?.classList.add('compact');
        this.dom.chatWindow?.classList.remove('expanded', 'hidden');
        this.updateChatSizeButton();
        sessionStorage.setItem('cr_assistant_is_open', 'true');
        document.body.style.overflow = '';
        this.scrollToBottom();
    },

    toggleChatSize() {
        this.isExpanded = !this.isExpanded;
        sessionStorage.setItem('cr_assistant_is_expanded', String(this.isExpanded));
        this.dom.chatWindow?.classList.toggle('compact', !this.isExpanded);
        this.dom.chatWindow?.classList.toggle('expanded', this.isExpanded);
        this.updateChatSizeButton();
        document.body.style.overflow = this.isExpanded && window.innerWidth <= 1024
            ? 'hidden'
            : '';
        this.scrollToBottom();
        this.dom.input?.focus();
    },

    updateChatSizeButton() {
        const button = this.dom.footerExpandBtn;
        const icon = button?.querySelector('i');
        if (!button || !icon) return;

        const expanded = this.isExpanded;
        button.title = expanded ? 'Collapse chat' : 'Open full chat';
        button.setAttribute('aria-label', button.title);
        icon.className = expanded
            ? 'fa-solid fa-down-left-and-up-right-to-center'
            : 'fa-solid fa-up-right-and-down-left-from-center';
    },

    loadHistory() {
        try {
            const raw = localStorage.getItem(this.storageKey);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed)) {
                    this.messages = parsed;
                }
            }
        } catch (e) {
            console.error('Failed to load assistant chat history:', e);
            this.messages = [];
        }
    },

    saveHistory() {
        try {
            const toSave = this.messages.slice(-40);
            localStorage.setItem(this.storageKey, JSON.stringify(toSave));
        } catch (e) {
            console.error('Failed to save assistant chat history:', e);
        }
    },

    clearHistory() {
        if (this.messages.length === 0) return;
        if (confirm('Are you sure you want to reset this conversation?')) {
            if (this.isLoading) {
                this.stopGenerating();
            }
            this.messages = [];
            localStorage.removeItem(this.storageKey);
            this.renderInitialState();
            Toast.info('Conversation history cleared.');
        }
    },

    renderInitialState() {
        if (!this.dom.messagesContainer) return;
        this.dom.messagesContainer.innerHTML = '';

        if (this.messages.length === 0) {
            const isAuth = this.isUserAuthenticated();
            const user = this.getCurrentUser();

            const welcomeHeading = isAuth
                ? `Welcome Back, ${user?.first_name || 'VIP Member'}!`
                : 'Welcome to DriveLuxe AI';

            const welcomeDesc = isAuth
                ? 'I am connected to your private rental account. I can check your reservations, suggest personalized cars based on your trips, and assist with VIP bookings.'
                : 'I can help you explore our luxury fleet, compare models, explain transparent pricing, and guide you through quick online verification.';

            const authHint = !isAuth ? `
                <div class="assistant-auth-banner" style="margin-top:8px;">
                    <div><i class="fa-solid fa-sparkles" style="color:var(--warning);"></i> <strong>Tip:</strong> Sign in for personalized car recommendations and reservation tracking.</div>
                    <button type="button" class="btn btn-primary btn-sm" onclick="Auth.openAuthModal('password')">
                        <i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In to Account
                    </button>
                </div>
            ` : '';

            const welcomeCard = document.createElement('div');
            welcomeCard.className = 'assistant-welcome-card';
            welcomeCard.innerHTML = `
                <div class="welcome-badge-row">
                    <div class="welcome-icon-pill">
                        <i class="fa-solid ${isAuth ? 'fa-crown' : 'fa-wand-magic-sparkles'}"></i>
                    </div>
                    <div>
                        <h4 class="welcome-heading">${welcomeHeading}</h4>
                        <small style="color:var(--text-muted);">${isAuth ? 'Connected to Private Concierge' : '24/7 Public Rental Concierge'}</small>
                    </div>
                </div>
                <p class="welcome-desc">${welcomeDesc}</p>
                ${authHint}
            `;
            this.dom.messagesContainer.appendChild(welcomeCard);
        } else {
            this.messages.forEach(msg => {
                this.renderMessageElement(msg, false);
            });
        }

        this.scrollToBottom();
    },

    askSuggestion(prompt) {
        if (!prompt) return;
        this.open(true);
        if (this.isLoading) return;
        this.sendMessage(prompt);
    },

    stopGenerating() {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
        this.setLoading(false);
        Toast.info('Generation stopped.');
    },

    async sendMessage(text) {
        if (!text || this.isLoading) return;

        // 1. Add User Message
        const userMsg = {
            id: 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
            sender: 'user',
            text: text,
            timestamp: new Date().toISOString()
        };

        this.messages.push(userMsg);
        this.renderMessageElement(userMsg, true);
        this.saveHistory();

        // 2. Reset Input Box
        this.dom.input.value = '';
        this.dom.input.style.height = 'auto';
        this.dom.sendBtn.disabled = true;
        if (this.dom.charCounter) this.dom.charCounter.textContent = '';

        // 3. Create Placeholder Assistant Message for Streaming
        const botMsg = {
            id: 'msg_' + (Date.now() + 1) + '_' + Math.random().toString(36).substr(2, 4),
            sender: 'assistant',
            text: '',
            model: '',
            statusText: ['DriveLuxe AI is thinking...'],
            thoughtDuration: null,
            thoughtOpen: true,
            toolSteps: [],
            timestamp: new Date().toISOString()
        };

        this.messages.push(botMsg);
        const botRow = this.renderMessageElement(botMsg, true);
        this.setLoading(true);

        this.abortController = new AbortController();

        try {
            // 4. Stream SSE Events from backend
            await this.consumeSseStream(text, botMsg, botRow, this.abortController.signal);
            this.saveHistory();
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error('Stream cancelled by user:', error);
            } else {
                console.error('Assistant SSE Stream error:', error);

                let errorMessage = "The assistant encountered an issue processing your request. Please try again.";
                let isAuthError = false;

                if (error.status === 401 || (error.message && error.message.toLowerCase().includes('unauthorized'))) {
                    isAuthError = true;
                    errorMessage = "To access personalized recommendations and manage reservations, please sign in to your account.";
                } else if (error.status === 429 || (error.message && (error.message.includes('429') || error.message.toLowerCase().includes('rate limit')))) {
                    errorMessage = "⏳ AI service is currently experiencing high demand (Rate limit reached). Please wait a few moments and try again.";
                }

                if (!botMsg.text) {
                    botMsg.text = errorMessage;
                    botMsg.isError = true;
                    botMsg.authRequired = isAuthError;
                    this.updateMessageElement(botRow, botMsg, false);
                }
            }
            this.saveHistory();
        } finally {
            this.abortController = null;
            this.setLoading(false);
            this.updateMessageElement(botRow, botMsg, false);
            this.scrollToBottom();
        }
    },

    async consumeSseStream(userMessage, botMsg, botRow, signal) {
        const endpoint = this.getEndpoint();
        const url = endpoint.startsWith('http') ? endpoint : `${CONFIG.API_BASE}${endpoint}`;

        // Prepare History Payload (last 30 turns)
        const historyPayload = this.messages
            .slice(0, -2) // exclude latest user and empty bot message
            .filter(item => item.sender === 'user' || item.sender === 'assistant')
            .map(item => ({
                id: item.id,
                sender: item.sender,
                text: item.text || '',
                model: item.model || null,
                timestamp: item.timestamp,
                // toolSteps: item.sender === 'assistant'
                //     ? (item.toolSteps || [])
                //         .filter(step => step && step.status === 'completed')
                //         .map(step => ({
                //             tool: step.tool,
                //             input: step.input || {},
                //             output: step.output || '',
                //             status: step.status
                //         }))
                //     : []
            }))
            .slice(-10);

        // Resolve last used model
        const lastBotMsg = [...this.messages].reverse().find(m => m.sender === 'assistant' && m.model);
        const lastModel = (lastBotMsg && lastBotMsg.model) || this.lastUsedModel || null;

        const payload = {
            message: userMessage,
            history: historyPayload,
            model: lastModel
        };

        const headers = {
            'Content-Type': 'application/json',
            ...API.getHeaders(false) // includes Bearer token if present
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload),
            signal: signal
        });

        if (!response.ok) {
            const err = new Error(`HTTP ${response.status}`);
            err.status = response.status;
            throw err;
        }

        if (!response.body) {
            throw new Error('Streaming response body unavailable');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed.startsWith('data:')) continue;

                const jsonStr = trimmed.replace(/^data:\s*/, '').trim();
                if (!jsonStr) continue;

                try {
                    const eventData = JSON.parse(jsonStr);
                    this.handleWorkstationEvent(eventData, botMsg, botRow);
                } catch (jsonErr) {
                    console.warn('Failed to parse SSE JSON chunk:', jsonStr, jsonErr);
                }
            }
        }
    },

    handleWorkstationEvent(event, botMsg, botRow) {
        if (event.model) {
            botMsg.model = event.model;
            this.lastUsedModel = event.model;
        }

        if (!Array.isArray(botMsg.statusText)) {
            botMsg.statusText = botMsg.statusText ? [botMsg.statusText] : ['DriveLuxe AI is thinking...'];
        }

        const appendStatusText = (text) => {
            if (!text) return;
            botMsg.statusText.push(text);
        };

        switch (event.type) {
            case 'agent_thinking':
                if (event.model) {
                    botMsg.model = event.model;
                    this.lastUsedModel = event.model;
                }
                appendStatusText(event.message || 'DriveLuxe AI is thinking...');
                this.updateMessageElement(botRow, botMsg, true);
                break;

            case 'tool_start': {
                const toolName = event.tool || 'Tool';
                appendStatusText(event.message || `Executing ${toolName}...`);

                botMsg.toolSteps = botMsg.toolSteps || [];
                const step = {
                    id: 'step_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                    tool: toolName,
                    input: event.input || {},
                    status: 'running',
                    duration: null,
                    output: '',
                    description: event.description,
                    outputOpen: false
                };
                botMsg.toolSteps.push(step);
                this.updateMessageElement(botRow, botMsg, true);
                break;
            }

            case 'tool_end': {
                botMsg.toolSteps = botMsg.toolSteps || [];
                const activeStep = botMsg.toolSteps.find(s => s.tool === event.tool && s.status === 'running') || botMsg.toolSteps[botMsg.toolSteps.length - 1];
                if (activeStep) {
                    activeStep.status = 'completed';
                    activeStep.output = event.output || '';
                    activeStep.duration = event.duration ? Number(event.duration).toFixed(2) : null;
                }

                // Perform real-time Webpage Automation behind chat
                executeWebpageAction(event.tool, event.input || {}, event.output);

                // appendStatusText(event.message || 'Streaming response...');
                this.updateMessageElement(botRow, botMsg, true);
                break;
            }

            case 'token':
                if (event.model && !botMsg.model) {
                    botMsg.model = event.model;
                    this.lastUsedModel = event.model;
                }
                if (event.content) {
                    if (event.thought_duration && !botMsg.thoughtDuration) {
                        botMsg.thoughtDuration = Number(event.thought_duration).toFixed(1);
                    }
                    botMsg.text += event.content;
                    // Auto collapse thought when substantive answer starts
                    if (botMsg.thoughtOpen && botMsg.text.length > 40) {
                        botMsg.thoughtOpen = false;
                    }
                    this.updateMessageElement(botRow, botMsg, true);
                }
                break;

            case 'done':
                if (event.model) {
                    botMsg.model = event.model;
                    this.lastUsedModel = event.model;
                }
                if (event.thought_duration) {
                    botMsg.thoughtDuration = Number(event.thought_duration).toFixed(1);
                }
                if (event.total_duration) {
                    botMsg.totalDuration = event.total_duration;
                }
                this.updateMessageElement(botRow, botMsg, false);
                break;

            case 'switch_model':
                if (event.next_model) {
                    this.lastUsedModel = event.next_model;
                }
                appendStatusText(event.message || `Switching model to ${event.next_model || event.model}...`);
                this.updateMessageElement(botRow, botMsg, true);
                break;

            case 'missing_details':
                if (event.model) {
                    botMsg.model = event.model;
                    this.lastUsedModel = event.model;
                }
                appendStatusText(event.message || 'Please complete rental details in popup:');
                this.updateMessageElement(botRow, botMsg, true);
                this.openBookingDetailsModal(event);
                break;

            case 'show_fleet_cars':
                executeWebpageAction('show_fleet_cars', event.input || {}, event.output || event);
                break;

            case 'error':
                if (event.model) {
                    botMsg.model = event.model;
                    this.lastUsedModel = event.model;
                }
                if (event.auth_required) {
                    botMsg.authRequired = true;
                }
                if (!botMsg.text) {
                    botMsg.text = event.message || 'Assistant error occurred.';
                    botMsg.isError = true;
                }
                this.updateMessageElement(botRow, botMsg, false);
                break;
        }
    },

    renderMessageElement(msg, animated = true) {
        if (!this.dom.messagesContainer) return null;

        const welcomeCard = this.dom.messagesContainer.querySelector('.assistant-welcome-card');
        if (welcomeCard && this.messages.length > 0) {
            welcomeCard.remove();
        }

        const isUser = msg.sender === 'user';
        const isSystem = msg.sender === 'system';
        const row = document.createElement('div');
        row.className = `assistant-msg-row ${isUser ? 'user' : isSystem ? 'system' : 'assistant'}`;
        row.id = msg.id;

        const timeStr = this.formatTime(msg.timestamp);

        if (isSystem) {
            row.innerHTML = `
                <div class="assistant-system-pill">
                    <i class="fa-solid fa-circle-info" style="color:var(--primary);"></i>
                    <span>${this.escapeHtml(msg.text)}</span>
                </div>
            `;
        } else if (isUser) {
            row.innerHTML = `
                <div class="assistant-msg-bubble user">
                    ${this.escapeHtml(msg.text)}
                </div>
                <div class="assistant-msg-meta">
                    <span>${timeStr}</span>
                </div>
            `;
        } else {
            row.innerHTML = `
                <div class="assistant-msg-content-wrapper">
                    <div class="assistant-mini-avatar">
                        <i class="fa-solid fa-robot"></i>
                    </div>
                    <div class="assistant-msg-bubble assistant">
                        <!-- Thinking & Tool Calling Accordion -->
                        <div class="ag-thought-container"></div>

                        <!-- Final Text / Markdown Output or Live Typing Indicator -->
                        <div class="assistant-msg-text-content"></div>

                        <!-- Auth Callout if required -->
                        <div class="assistant-auth-container"></div>
                    </div>
                </div>
                <div class="assistant-msg-meta">
                    <span class="assistant-msg-time">${timeStr}</span>
                    ${msg.model ? `
                        <span class="assistant-msg-model" title="Model: ${this.escapeHtml(msg.model)}">
                            <i class="fa-solid fa-microchip"></i>
                            <span>${this.escapeHtml(msg.model)}</span>
                        </span>
                    ` : ''}
                    <button type="button" class="assistant-msg-action-btn" title="Copy response" onclick="Assistant.copyMessage('${msg.id}')">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
            `;
            this.updateMessageElement(row, msg, animated);
        }

        this.dom.messagesContainer.appendChild(row);
        if (animated) {
            this.scrollToBottom();
        }
        return row;
    },

    renderThoughtAccordionHtml(msg) {
        const hasTools = msg.toolSteps && msg.toolSteps.length > 0;
        let statusList = Array.isArray(msg.statusText) ? msg.statusText : (msg.statusText ? [msg.statusText] : []);
        statusList = statusList.filter(
            text =>
                !text.toLowerCase().includes("response") &&
                !text.toLowerCase().includes("streaming")
        );
        const hasStatus = statusList.length > 0;
        if (!hasTools && !msg.thoughtDuration && !hasStatus) return '';

        const isOpen = msg.thoughtOpen !== false;
        const durationText = msg.thoughtDuration ? `${msg.thoughtDuration}s` : '';

        // Render all status texts above tools section
        let stepsHtml = '';
        if (hasStatus) {
            stepsHtml = `
                <div class="ag-thought-steps">
                    ${statusList.map(step => `
                        <div class="ag-thought-step-item">
                            <i class="fa-solid fa-circle-check"></i>
                            <span>${this.escapeHtml(step)}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Render tool calls inside thought process
        let toolsHtml = '';
        if (hasTools) {
            toolsHtml = `
                <div class="ag-thought-tools-wrap">
                    <div class="ag-thought-tools-title">
                        <i class="fa-solid fa-screwdriver-wrench"></i>
                        <span>Webpage Automation &amp; Tools (${msg.toolSteps.length}):</span>
                    </div>
                    <div class="ag-trajectory-timeline">
                        ${msg.toolSteps.map(step => this.renderToolCardHtml(step, msg.id)).join('')}
                    </div>
                </div>
            `;
        }

        return `
            <div class="ag-thought-accordion ${isOpen ? 'open' : 'collapsed'}">
                <div class="ag-thought-header" onclick="Assistant.toggleThought('${msg.id}')">
                    <div class="ag-thought-title">
                        <i class="fa-solid fa-brain ag-brain-icon"></i>
                        <span>Thought for ${durationText ? `<span class="ag-thought-timer">${durationText}</span>` : ''}</span>
                    </div>
                    <div class="ag-thought-toggle">
                        <span>${isOpen ? 'Hide' : 'Show'} reasoning</span>
                        <i class="fa-solid fa-chevron-${isOpen ? 'up' : 'down'}"></i>
                    </div>
                </div>
                <div class="ag-thought-body ${isOpen ? '' : 'hidden'}">
                    ${stepsHtml}
                    ${toolsHtml || (!hasStatus ? '<div class="ag-thought-direct-note"><i class="fa-solid fa-check"></i> Direct response generated without tool calls.</div>' : '')}
                </div>
            </div>
        `;
    },

    renderToolCardHtml(step, msgId) {
        const isRunning = step.status === 'running';
        const hasInput = step.input && typeof step.input === 'object' && Object.keys(step.input).length > 0;
        const durationText = step.duration ? `${step.duration}s` : '';

        // Format Input Parameters into key-value pills
        let paramsHtml = '';
        if (hasInput) {
            paramsHtml = Object.entries(step.input).map(([k, v]) => `
                <span class="ag-param-pill">
                    <span class="ag-param-key">${this.escapeHtml(k)}:</span>
                    <span class="ag-param-val">${this.escapeHtml(typeof v === 'object' ? JSON.stringify(v) : String(v))}</span>
                </span>
            `).join('');
        }

        // Format Output JSON / text
        let formattedOutput = '';
        if (step.output) {
            try {
                const parsed = typeof step.output === 'string' ? JSON.parse(step.output) : step.output;
                formattedOutput = JSON.stringify(parsed, null, 2);
            } catch (e) {
                formattedOutput = String(step.output);
            }
        }

        const isOutputOpen = !!step.outputOpen;

        return `
            <div class="ag-tool-card ${isRunning ? 'running' : 'completed'}" id="${step.id}">
                <div class="ag-tool-header">
                    <div class="ag-tool-identity">
                        <div class="ag-tool-info">
                            <span class="ag-tool-title">${this.escapeHtml(step.tool)}</span>
                        </div>
                    </div>
                    <div class="ag-tool-meta-badges">
                        ${durationText ? `<span class="ag-tool-duration"><i class="fa-regular fa-clock"></i> ${durationText}</span>` : ''}
                        <span class="ag-tool-status ${isRunning ? 'running' : 'completed'}">
                            ${isRunning
                ? '<i class="fa-solid fa-circle-notch fa-spin"></i> Running'
                : '<i class="fa-solid fa-circle-check"></i> Success'}
                        </span>
                    </div>
                </div>

                ${hasInput ? `
                    <div class="ag-tool-params-section">
                        <span class="ag-params-label">Arguments:</span>
                        <div class="ag-params-list">${paramsHtml}</div>
                    </div>
                ` : ''}

                <div class="ag-tool-automation-tag">
                    <i class="fa-solid fa-bolt-lightning"></i>
                    <span>${step.description}</span>
                </div>

                ${step.output ? `
                    <div class="ag-tool-output-drawer ${isOutputOpen ? 'open' : 'collapsed'}">
                        <button type="button" class="ag-output-toggle-btn" onclick="Assistant.toggleToolOutput('${msgId}', '${step.id}')">
                            <span><i class="fa-solid fa-terminal"></i> Response Payload</span>
                            <span class="ag-output-hint">${isOutputOpen ? 'Hide' : 'View'} JSON Payload <i class="fa-solid fa-chevron-${isOutputOpen ? 'up' : 'down'}"></i></span>
                        </button>
                        <div class="ag-output-body ${isOutputOpen ? '' : 'hidden'}">
                            <div class="ag-output-actions">
                                <span class="ag-output-type">JSON</span>
                                <button type="button" class="ag-copy-payload-btn" onclick="Assistant.copyToolPayload('${msgId}', '${step.id}')">
                                    <i class="fa-regular fa-copy"></i> Copy Output
                                </button>
                            </div>
                            <pre class="ag-output-pre"><code>${this.escapeHtml(formattedOutput)}</code></pre>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    },

    updateMessageElement(rowEl, msg, isStreaming = false) {
        if (!rowEl) return;

        // 1. Render Antigravity Thought & Tool Calling Accordion
        const thoughtContainer = rowEl.querySelector('.ag-thought-container');
        if (thoughtContainer) {
            thoughtContainer.innerHTML = this.renderThoughtAccordionHtml(msg);
        }

        // 2. Render Streamed Markdown Text or Live Typing Status inside AI bubble
        const textContainer = rowEl.querySelector('.assistant-msg-text-content');
        const compactTextContainer = document.getElementById('compact-assistant-msg-text-content');
        if (textContainer) {
            if (msg.text && msg.text.trim().length > 0) {
                // When markdown text is streaming or finished, render directly with no tail cursor
                textContainer.innerHTML = this.formatMarkdown(msg.text);
                if (compactTextContainer) {
                    compactTextContainer.innerHTML= `<span style="margin:5px;padding: 1px; background: plum;"> </span> Open full chat to see the responses.`;
                }
            } else if (isStreaming) {
                // When actively generating before the first text token arrives, show the typing status inside the message bubble
                const latestStatus = Array.isArray(msg.statusText)
                    ? (msg.statusText[msg.statusText.length - 1] || 'DriveLuxe AI is thinking...')
                    : (msg.statusText || 'DriveLuxe AI is thinking...');
                textContainer.innerHTML = `
                    <div class="assistant-typing-indicator">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <span class="typing-label">${this.escapeHtml(latestStatus)}</span>
                    </div>
                `;
                if (compactTextContainer) {
                    compactTextContainer.innerHTML= `<span style="margin:5px;padding: 1px; background: plum;"> </span> ${this.escapeHtml(latestStatus)} ...`;
                }
            } else {
                textContainer.innerHTML = '';
            }
        }

        // 3. Render Auth Banner if required
        const authContainer = rowEl.querySelector('.assistant-auth-container');
        if (authContainer) {
            if (msg.authRequired) {
                authContainer.innerHTML = `
                    <div class="assistant-auth-banner">
                        <div><i class="fa-solid fa-lock" style="margin-right:4px;"></i> Authentication required for personalized concierge</div>
                        <button type="button" class="btn btn-primary btn-sm" onclick="Auth.openAuthModal('password')">
                            <i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In to Account
                        </button>
                    </div>
                `;
            } else {
                authContainer.innerHTML = '';
            }
        }

        // 4. Update Meta (Time, Model Pill, Copy Button)
        const metaContainer = rowEl.querySelector('.assistant-msg-meta');
        if (metaContainer && msg.sender === 'assistant') {
            const timeStr = this.formatTime(msg.timestamp);
            metaContainer.innerHTML = `
                <span class="assistant-msg-time">${timeStr}</span>
                ${msg.model ? `
                    <span class="assistant-msg-model" title="Model: ${this.escapeHtml(msg.model)}">
                        <i class="fa-solid fa-microchip"></i>
                        <span>${this.escapeHtml(msg.model)}</span>
                    </span>
                ` : ''}
                <button type="button" class="assistant-msg-action-btn" title="Copy response" onclick="Assistant.copyMessage('${msg.id}')">
                    <i class="fa-regular fa-copy"></i>
                </button>
            `;
        }

        if (isStreaming) {
            this.scrollToBottom();
        }
    },

    openBookingDetailsModal(eventData = {}) {
        const modal = document.getElementById('assistant-booking-details-modal');
        if (!modal) return;

        const missing = Array.isArray(eventData.missing_fields) ? eventData.missing_fields : [];
        const isMissingLoc = missing.includes('pickup_location');
        const isMissingPDate = missing.includes('pickup_date');
        const isMissingRDate = missing.includes('return_date');

        const today = new Date().toISOString().split('T')[0];

        const pLocInput = document.getElementById('popup-pickup-location');
        const rLocInput = document.getElementById('popup-return-location');
        const pDateInput = document.getElementById('popup-pickup-date');
        const pTimeInput = document.getElementById('popup-pickup-time');
        const rDateInput = document.getElementById('popup-return-date');
        const rTimeInput = document.getElementById('popup-return-time');
        const carIdInput = document.getElementById('popup-car-id');
        const carGroup = document.getElementById('group-popup-car');
        const carLabel = document.getElementById('popup-car-label');

        let pDate = eventData.pickup_date ? String(eventData.pickup_date).split(' ')[0] : '';
        let pTime = eventData.pickup_time || (eventData.pickup_date && String(eventData.pickup_date).includes(' ') ? String(eventData.pickup_date).split(' ')[1] : '10:00');
        let rDate = eventData.return_date ? String(eventData.return_date).split(' ')[0] : '';
        let rTime = eventData.return_time || (eventData.return_date && String(eventData.return_date).includes(' ') ? String(eventData.return_date).split(' ')[1] : '10:00');

        if (pLocInput) {
            pLocInput.value = eventData.pickup_location || '';
            document.getElementById('group-popup-ploc')?.classList.toggle('highlight-missing', isMissingLoc);
        }
        if (rLocInput) {
            rLocInput.value = eventData.return_location || '';
        }
        if (pDateInput) {
            pDateInput.min = today;
            pDateInput.value = pDate;
            document.getElementById('group-popup-pdate')?.classList.toggle('highlight-missing', isMissingPDate);
        }
        if (pTimeInput) {
            pTimeInput.value = pTime;
        }
        if (rDateInput) {
            rDateInput.min = pDate || today;
            rDateInput.value = rDate;
            document.getElementById('group-popup-rdate')?.classList.toggle('highlight-missing', isMissingRDate);
        }
        if (rTimeInput) {
            rTimeInput.value = rTime;
        }

        if (carGroup && carIdInput) {
            const carName = eventData.car_name || (eventData.brand ? `${eventData.brand} ${eventData.model || ''}`.trim() : '');
            if (carName || eventData.car_id) {
                carIdInput.value = eventData.car_id || '';
                if (carLabel) carLabel.textContent = carName || 'Selected Vehicle';
                carGroup.style.display = 'block';
            } else {
                carIdInput.value = '';
                carGroup.style.display = 'none';
            }
        }

        this.pendingBookingData = eventData;
        modal.classList.add('active');

        // Focus first missing or empty input
        setTimeout(() => {
            if (isMissingLoc || !pLocInput?.value) {
                pLocInput?.focus();
            } else if (isMissingPDate || !pDateInput?.value) {
                pDateInput?.focus();
            } else if (isMissingRDate || !rDateInput?.value) {
                rDateInput?.focus();
            }
        }, 150);
    },

    closeBookingDetailsModal() {
        const modal = document.getElementById('assistant-booking-details-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    },

    submitBookingDetailsModal() {
        const pLocInput = document.getElementById('popup-pickup-location');
        const rLocInput = document.getElementById('popup-return-location');
        const pDateInput = document.getElementById('popup-pickup-date');
        const pTimeInput = document.getElementById('popup-pickup-time');
        const rDateInput = document.getElementById('popup-return-date');
        const rTimeInput = document.getElementById('popup-return-time');
        const carIdInput = document.getElementById('popup-car-id');
        const carLabel = document.getElementById('popup-car-label');

        const pickup_location = pLocInput ? pLocInput.value.trim() : '';
        let return_location = rLocInput ? rLocInput.value.trim() : '';
        const pickup_date = pDateInput ? pDateInput.value.trim() : '';
        const pickup_time = pTimeInput ? pTimeInput.value.trim() : '10:00';
        const return_date = rDateInput ? rDateInput.value.trim() : '';
        const return_time = rTimeInput ? rTimeInput.value.trim() : '10:00';
        const car_id = carIdInput ? carIdInput.value.trim() : '';

        if (!pickup_location) {
            Toast.error('Please enter a pickup location.');
            pLocInput?.focus();
            return;
        }

        if (!pickup_date) {
            Toast.error('Please select a pickup date.');
            pDateInput?.focus();
            return;
        }

        if (!return_date) {
            Toast.error('Please select a return date.');
            rDateInput?.focus();
            return;
        }

        if (return_date < pickup_date) {
            Toast.error('Return date cannot be earlier than pickup date.');
            rDateInput?.focus();
            return;
        }

        if (!return_location) {
            return_location = pickup_location;
        }

        this.closeBookingDetailsModal();

        // Construct message prompt for agent
        const carDisplayName = (carLabel && carLabel.textContent && carLabel.textContent !== 'DriveLuxe Vehicle' && carLabel.textContent !== 'Selected Vehicle')
            ? carLabel.textContent.trim()
            : '';
        const carText = carDisplayName ? ` for the ${carDisplayName}` : '';
        const promptText = `Book vehicle${carText} with pickup at ${pickup_location} on ${pickup_date} ${pickup_time} and return at ${return_location} on ${return_date} ${return_time}.`;

        this.sendMessage(promptText);
    },

    toggleThought(msgId) {
        const msg = this.messages.find(m => m.id === msgId);
        if (!msg) return;
        msg.thoughtOpen = msg.thoughtOpen === false ? true : false;
        this.saveHistory();

        const rowEl = document.getElementById(msgId);
        if (!rowEl) return;

        const accordion = rowEl.querySelector('.ag-thought-accordion');
        if (!accordion) return;

        const body = accordion.querySelector('.ag-thought-body');
        const toggleSpan = accordion.querySelector('.ag-thought-toggle span');
        const toggleIcon = accordion.querySelector('.ag-thought-toggle i');

        if (msg.thoughtOpen) {
            accordion.classList.remove('collapsed');
            accordion.classList.add('open');
            if (body) body.classList.remove('hidden');
            if (toggleSpan) toggleSpan.textContent = 'Hide reasoning';
            if (toggleIcon) toggleIcon.className = 'fa-solid fa-chevron-up';
        } else {
            accordion.classList.remove('open');
            accordion.classList.add('collapsed');
            if (body) body.classList.add('hidden');
            if (toggleSpan) toggleSpan.textContent = 'Show reasoning';
            if (toggleIcon) toggleIcon.className = 'fa-solid fa-chevron-down';
        }
    },

    toggleToolOutput(msgId, stepId) {
        const msg = this.messages.find(m => m.id === msgId);
        if (!msg || !msg.toolSteps) return;
        const step = msg.toolSteps.find(s => s.id === stepId);
        if (!step) return;
        step.outputOpen = !step.outputOpen;
        this.saveHistory();

        const stepEl = document.getElementById(stepId);
        if (!stepEl) return;

        const drawer = stepEl.querySelector('.ag-tool-output-drawer');
        if (!drawer) return;

        const body = drawer.querySelector('.ag-output-body');
        const hintSpan = drawer.querySelector('.ag-output-hint');

        if (step.outputOpen) {
            drawer.classList.remove('collapsed');
            drawer.classList.add('open');
            if (body) body.classList.remove('hidden');
            if (hintSpan) hintSpan.innerHTML = `Hide JSON Payload <i class="fa-solid fa-chevron-up"></i>`;
        } else {
            drawer.classList.remove('open');
            drawer.classList.add('collapsed');
            if (body) body.classList.add('hidden');
            if (hintSpan) hintSpan.innerHTML = `View JSON Payload <i class="fa-solid fa-chevron-down"></i>`;
        }
    },

    copyToolPayload(msgId, stepId) {
        const msg = this.messages.find(m => m.id === msgId);
        if (!msg || !msg.toolSteps) return;
        const step = msg.toolSteps.find(s => s.id === stepId);
        if (!step || !step.output) return;

        let formatted = step.output;
        try {
            const parsed = typeof step.output === 'string' ? JSON.parse(step.output) : step.output;
            formatted = JSON.stringify(parsed, null, 2);
        } catch (e) { }

        this.fallbackCopyText(formatted);
        Toast.success('Copied tool output to clipboard');
    },

    copyPreCode(btn) {
        const pre = btn.closest('.ag-code-block')?.querySelector('pre code');
        if (!pre) return;
        const text = pre.innerText;
        this.fallbackCopyText(text);
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<i class="fa-solid fa-check" style="color:var(--success);"></i> Copied!`;
        setTimeout(() => {
            btn.innerHTML = originalHtml;
        }, 1500);
    },

    setLoading(loading) {
        this.isLoading = loading;
        if (this.dom.sendBtn) {
            this.dom.sendBtn.classList.toggle('hidden', loading);
        }
        if (this.dom.stopBtn) {
            this.dom.stopBtn.classList.toggle('hidden', !loading);
        }
        if (!loading && this.dom.input) {
            this.dom.sendBtn.disabled = !this.dom.input.value.trim();
        }
        if (loading) {
            this.scrollToBottom();
        }
    },

    scrollToBottom() {
        if (!this.dom.messagesContainer) return;
        requestAnimationFrame(() => {
            this.dom.messagesContainer.scrollTop = this.dom.messagesContainer.scrollHeight;
        });
    },

    formatTime(isoString) {
        try {
            const date = isoString ? new Date(isoString) : new Date();
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return '';
        }
    },

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return String(unsafe)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    },

    formatMarkdown(text) {
        if (!text) return '';
        let escaped = this.escapeHtml(text);

        // Code blocks with Antigravity header bar & copy button
        escaped = escaped.replace(/```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```/g, (match, lang, code) => {
            const langLabel = (lang || 'JSON').toUpperCase();
            return `
                <div class="ag-code-block">
                    <div class="ag-code-header">
                        <span class="ag-code-lang"><i class="fa-solid fa-code"></i> ${langLabel}</span>
                        <button type="button" class="ag-code-copy-btn" onclick="Assistant.copyPreCode(this)">
                            <i class="fa-regular fa-copy"></i> Copy
                        </button>
                    </div>
                    <pre class="ag-code-body"><code>${code.trim()}</code></pre>
                </div>
            `;
        });

        // Inline code: `code`
        escaped = escaped.replace(/`([^`]+)`/g, '<code class="ag-inline-code">$1</code>');

        // Headers: ### Header -> <h4>, ## Header -> <h3>
        escaped = escaped.replace(/^### (.*$)/gim, '<h4 class="ag-md-h4">$1</h4>');
        escaped = escaped.replace(/^## (.*$)/gim, '<h3 class="ag-md-h3">$1</h3>');

        // Bold: **text**
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong class="ag-strong">$1</strong>');

        // Italic: *text* or _text_
        escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Links: [label](url)
        escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="ag-link" target="_blank" rel="noopener noreferrer">$1 <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:0.7em;"></i></a>');

        // Lists: lines starting with * or - or •
        const lines = escaped.split('\n');
        let inList = false;
        let resultLines = [];

        for (let line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
                if (!inList) {
                    inList = true;
                    resultLines.push('<ul class="ag-list">');
                }
                resultLines.push(`<li>${trimmed.replace(/^[-*•]\s*/, '')}</li>`);
            } else {
                if (inList) {
                    inList = false;
                    resultLines.push('</ul>');
                }
                resultLines.push(line);
            }
        }
        if (inList) {
            resultLines.push('</ul>');
        }

        let html = resultLines.join('\n');

        html = html.replace(/\n\n+/g, '</p><p class="ag-p">');
        html = html.replace(/\n/g, '<br/>');

        return html;
    },

    copyMessage(msgId) {
        const msg = this.messages.find(m => m.id === msgId);
        if (!msg || !msg.text) return;

        this.fallbackCopyText(msg.text);
        Toast.success('Copied response to clipboard');
    },

    fallbackCopyText(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).catch(() => {
                const temp = document.createElement('textarea');
                temp.value = text;
                document.body.appendChild(temp);
                temp.select();
                document.execCommand('copy');
                document.body.removeChild(temp);
            });
        } else {
            const temp = document.createElement('textarea');
            temp.value = text;
            document.body.appendChild(temp);
            temp.select();
            document.execCommand('copy');
            document.body.removeChild(temp);
        }
    }
};
