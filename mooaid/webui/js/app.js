/**
 * MooAId Web UI - Main Application
 * Vue.js 3 Single File Component Logic
 */

// ============================================
// Import Components
// ============================================
// SearchableSelect component is loaded via script tag in HTML

// ============================================
// Application State
// ============================================
const { createApp } = Vue;

// ============================================
// API Service
// ============================================
const ApiService = {
    baseUrl: '',
    
    async call(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },
    
    get(endpoint) {
        return this.call(endpoint);
    },
    
    post(endpoint, data) {
        return this.call(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    put(endpoint, data) {
        return this.call(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    delete(endpoint) {
        return this.call(endpoint, { method: 'DELETE' });
    }
};

// ============================================
// Toast Notification Service
// ============================================
const ToastService = {
    toasts: [],
    listeners: [],
    
    add(message, type = 'info') {
        const toast = {
            id: Date.now(),
            message,
            type
        };
        this.toasts.push(toast);
        this.notifyListeners();
        
        setTimeout(() => this.remove(toast.id), 4000);
        return toast.id;
    },
    
    remove(id) {
        this.toasts = this.toasts.filter(t => t.id !== id);
        this.notifyListeners();
    },
    
    success(message) {
        return this.add(message, 'success');
    },
    
    error(message) {
        return this.add(message, 'error');
    },
    
    warning(message) {
        return this.add(message, 'warning');
    },
    
    info(message) {
        return this.add(message, 'info');
    },
    
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(l => l !== callback);
        };
    },
    
    notifyListeners() {
        this.listeners.forEach(listener => listener([...this.toasts]));
    }
};

// ============================================
// Main Application
// ============================================
const app = createApp({
    components: {
        'searchable-select': SearchableSelect
    },
    data() {
        return {
            // UI State
            currentTab: 'opinion',
            loading: false,
            saving: false,
            showKey: false,
            sidebarOpen: false,
            
            // Toast notifications
            toasts: [],
            
            // Data
            profiles: [],
            history: [],
            models: {
                openrouter: [],
                openai: [],
                gemini: [],
                ollama: []
            },
            
            // Configuration
            config: {},
            configForm: {
                provider: 'openrouter',
                openrouter_api_key: '',
                openrouter_model: '',
                openai_api_key: '',
                openai_model: 'gpt-4o',
                gemini_api_key: '',
                gemini_model: 'gemini-pro',
                ollama_host: 'http://localhost:11434',
                ollama_model: 'llama3'
            },
            
            // Opinion Form
            opinionForm: {
                question: '',
                profile: 'default',
                context: ''
            },
            opinionResult: null,
            
            // Profile Editing
            newProfileName: '',
            editingProfile: null,
            currentField: 'preferences',
            newTag: '',
            profileData: {
                preferences: [],
                values: [],
                personality: [],
                context: []
            },

            // Personality Builder
            personalityBuilderOpen: false,
            builderSessionId: null,
            builderStep: 0,
            builderCurrentQuestion: null,
            builderCustomInput: '',
            builderComplete: false,
            builderProfileName: 'default',
            builderExtractedData: {
                preferences: [],
                values: [],
                personality: [],
                context: []
            }
        };
    },
    
    computed: {
        healthStatus() {
            // Check if provider status is healthy OR if we have an API key set
            const hasProviderStatus = this.config.provider_status?.openrouter;
            const hasApiKey = this.config.openrouter_api_key ||
                             (this.configForm.openrouter_api_key && this.configForm.openrouter_api_key.length > 10);

            if (this.config.provider === 'openrouter') {
                return hasProviderStatus || hasApiKey ? 'healthy' : 'degraded';
            }

            // For other providers, just check the provider status
            return hasProviderStatus ? 'healthy' : 'degraded';
        },

        healthColor() {
            return this.healthStatus === 'healthy' ? '#10b981' : '#f59e0b';
        }
    },
    
    async mounted() {
        // Subscribe to toast updates
        ToastService.subscribe(toasts => {
            this.toasts = toasts;
        });
        
        // Load initial data
        await this.loadAll();
        
        // Listen for keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard);
    },
    
    beforeUnmount() {
        document.removeEventListener('keydown', this.handleKeyboard);
    },
    
    methods: {
        // ============================================
        // Data Loading
        // ============================================
        async loadAll() {
            try {
                await Promise.all([
                    this.loadProfiles(),
                    this.loadConfig(),
                    this.loadHistory()
                ]);
            } catch (error) {
                ToastService.error('Failed to load data');
            }
        },
        
        async loadProfiles() {
            try {
                this.profiles = await ApiService.get('/profile');
            } catch (error) {
                ToastService.error('Failed to load profiles');
            }
        },
        
        async loadConfig() {
            try {
                this.config = await ApiService.get('/config');
                
                // Populate form with current values
                this.configForm.provider = this.config.provider;
                this.configForm.openrouter_model = this.config.openrouter_model || '';
                this.configForm.openai_model = this.config.openai_model || 'gpt-4o';
                this.configForm.gemini_model = this.config.gemini_model || 'gemini-pro';
                this.configForm.ollama_model = this.config.ollama_model || 'llama3';
                
                // Load available models
                await this.loadModels();
            } catch (error) {
                ToastService.error('Failed to load configuration');
            }
        },
        
        async loadModels() {
            try {
                const response = await ApiService.get('/models');
                this.models = response.models || {};
            } catch (error) {
                console.warn('Failed to load models, using defaults');
            }
        },

        // Fetch all OpenRouter models for searchable select
        async fetchOpenRouterModels() {
            try {
                const response = await ApiService.get('/models');
                const models = response.models?.openrouter || [];
                return models.map(m => ({
                    value: m.id,
                    label: m.name,
                    description: m.id
                }));
            } catch (error) {
                // Return default models if API fails
                return [
                    { value: 'anthropic/claude-3-haiku', label: 'Claude 3 Haiku', description: 'anthropic/claude-3-haiku' },
                    { value: 'anthropic/claude-3-sonnet', label: 'Claude 3 Sonnet', description: 'anthropic/claude-3-sonnet' },
                    { value: 'anthropic/claude-3-opus', label: 'Claude 3 Opus', description: 'anthropic/claude-3-opus' },
                    { value: 'openai/gpt-3.5-turbo', label: 'GPT-3.5 Turbo', description: 'openai/gpt-3.5-turbo' },
                    { value: 'openai/gpt-4-turbo', label: 'GPT-4 Turbo', description: 'openai/gpt-4-turbo' },
                    { value: 'openai/gpt-4o', label: 'GPT-4o', description: 'openai/gpt-4o' },
                    { value: 'meta-llama/llama-3-70b-instruct', label: 'Llama 3 70B', description: 'meta-llama/llama-3-70b-instruct' },
                    { value: 'google/gemini-pro-1.5', label: 'Gemini Pro 1.5', description: 'google/gemini-pro-1.5' },
                    { value: 'mistralai/mistral-large', label: 'Mistral Large', description: 'mistralai/mistral-large' }
                ];
            }
        },
        
        async loadHistory() {
            try {
                this.history = await ApiService.get('/history?limit=50');
            } catch (error) {
                console.warn('Failed to load history');
            }
        },
        
        // ============================================
        // Opinion Prediction
        // ============================================
        async submitOpinion() {
            if (!this.opinionForm.question.trim()) {
                ToastService.warning('Please enter a question');
                return;
            }
            
            this.loading = true;
            this.opinionResult = null;
            
            try {
                const payload = {
                    question: this.opinionForm.question,
                    profile_name: this.opinionForm.profile,
                    additional_context: this.opinionForm.context ? [this.opinionForm.context] : undefined
                };
                
                this.opinionResult = await ApiService.post('/opinion', payload);
                ToastService.success('Opinion predicted!');
                
                // Refresh history
                await this.loadHistory();
            } catch (error) {
                ToastService.error(error.message);
            } finally {
                this.loading = false;
            }
        },
        
        // ============================================
        // Profile Management
        // ============================================
        async createProfile() {
            if (!this.newProfileName.trim()) {
                ToastService.warning('Please enter a profile name');
                return;
            }
            
            try {
                await ApiService.post('/profile', { name: this.newProfileName });
                ToastService.success('Profile created!');
                this.newProfileName = '';
                await this.loadProfiles();
            } catch (error) {
                ToastService.error(error.message);
            }
        },
        
        async editProfile(name) {
            try {
                const profile = await ApiService.get(`/profile/${name}`);
                this.editingProfile = name;
                this.profileData = {
                    preferences: profile.preferences || [],
                    values: profile.values || [],
                    personality: profile.personality || [],
                    context: profile.context || []
                };
                this.currentField = 'preferences';
                this.newTag = '';
            } catch (error) {
                ToastService.error('Failed to load profile');
            }
        },
        
        closeEditModal() {
            this.editingProfile = null;
        },
        
        addTag() {
            const tag = this.newTag.trim();
            if (tag && !this.profileData[this.currentField].includes(tag)) {
                this.profileData[this.currentField].push(tag);
                this.newTag = '';
            }
        },
        
        removeTag(index) {
            this.profileData[this.currentField].splice(index, 1);
        },
        
        async saveProfile() {
            try {
                await ApiService.put(`/profile/${this.editingProfile}`, this.profileData);
                ToastService.success('Profile saved!');
                this.closeEditModal();
                await this.loadProfiles();
            } catch (error) {
                ToastService.error(error.message);
            }
        },
        
        async deleteProfile(name) {
            if (!confirm(`Are you sure you want to delete profile "${name}"?`)) {
                return;
            }
            
            try {
                await ApiService.delete(`/profile/${name}`);
                ToastService.success('Profile deleted');
                if (this.editingProfile === name) {
                    this.closeEditModal();
                }
                await this.loadProfiles();
            } catch (error) {
                ToastService.error(error.message);
            }
        },
        
        // ============================================
        // Configuration
        // ============================================
        async saveConfig() {
            // Validate model selection for OpenRouter
            if (this.configForm.provider === 'openrouter' && !this.configForm.openrouter_model) {
                ToastService.warning('Please select a model');
                return;
            }

            this.saving = true;

            // Build config data - only send API keys if they were actually entered
            const configData = {
                provider: this.configForm.provider,
                openrouter_model: this.configForm.openrouter_model || undefined,
                openai_model: this.configForm.openai_model || undefined,
                gemini_model: this.configForm.gemini_model || undefined,
                ollama_host: this.configForm.ollama_host || undefined,
                ollama_model: this.configForm.ollama_model || undefined
            };

            // Only include API keys if they were actually entered (not empty)
            if (this.configForm.openrouter_api_key && this.configForm.openrouter_api_key.trim()) {
                configData.openrouter_api_key = this.configForm.openrouter_api_key;
            }
            if (this.configForm.openai_api_key && this.configForm.openai_api_key.trim()) {
                configData.openai_api_key = this.configForm.openai_api_key;
            }
            if (this.configForm.gemini_api_key && this.configForm.gemini_api_key.trim()) {
                configData.gemini_api_key = this.configForm.gemini_api_key;
            }

            try {
                await ApiService.put('/config', configData);
                ToastService.success('Configuration saved!');
                await this.loadConfig();
            } catch (error) {
                ToastService.error(error.message);
            } finally {
                this.saving = false;
            }
        },
        
        // ============================================
        // Utilities
        // ============================================
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        handleKeyboard(event) {
            // Ctrl+Enter to submit opinion
            if (event.ctrlKey && event.key === 'Enter' && this.currentTab === 'opinion') {
                this.submitOpinion();
            }
        },

        switchTab(tab) {
            this.currentTab = tab;
            if (window.innerWidth <= 1024) {
                this.sidebarOpen = false;
            }
        },

        // ============================================
        // Personality Builder
        // ============================================
        openPersonalityBuilder() {
            this.builderProfileName = 'default';
            this.builderSessionId = null;
            this.builderStep = 0;
            this.builderCurrentQuestion = null;
            this.builderCustomInput = '';
            this.builderComplete = false;
            this.builderExtractedData = {
                preferences: [],
                values: [],
                personality: [],
                context: []
            };
            this.personalityBuilderOpen = true;
            this.startProfileBuilder();
        },

        closePersonalityBuilder() {
            this.personalityBuilderOpen = false;
            if (this.builderSessionId) {
                this.cancelBuilderSession();
            }
        },

        async startProfileBuilder() {
            try {
                const result = await ApiService.post('/profile-builder/start', {
                    profile_name: this.builderProfileName
                });
                this.builderSessionId = result.session_id;
                await this.nextBuilderStep();
            } catch (error) {
                ToastService.error('Failed to start profile builder: ' + error.message);
                this.closePersonalityBuilder();
            }
        },

        async nextBuilderStep() {
            if (!this.builderSessionId) return;

            try {
                const question = await ApiService.post(`/profile-builder/${this.builderSessionId}/question`);
                this.builderCurrentQuestion = question;
                this.builderStep = question.question_number;
            } catch (error) {
                if (error.message === 'No more questions') {
                    await this.completeBuilder();
                } else {
                    ToastService.error('Failed to get question: ' + error.message);
                }
            }
        },

        async submitBuilderAnswer(answer) {
            if (!this.builderSessionId || !this.builderCurrentQuestion) return;

            try {
                const result = await ApiService.post(`/profile-builder/${this.builderSessionId}/answer`, {
                    answer: answer
                });

                // Accumulate extracted data
                if (result.extracted) {
                    for (const [field, items] of Object.entries(result.extracted)) {
                        for (const item of items) {
                            if (!this.builderExtractedData[field].includes(item)) {
                                this.builderExtractedData[field].push(item);
                            }
                        }
                    }
                }

                ToastService.info(result.summary || 'Answer recorded');
                await this.nextBuilderStep();
            } catch (error) {
                ToastService.error('Failed to submit answer: ' + error.message);
            }
        },

        async completeBuilder() {
            if (!this.builderSessionId) return;

            try {
                const result = await ApiService.post(`/profile-builder/${this.builderSessionId}/complete`);
                this.builderComplete = true;
                this.builderSessionId = null;
                ToastService.success('Profile built successfully!');

                // Reload profiles
                await this.loadProfiles();
            } catch (error) {
                ToastService.error('Failed to complete profile: ' + error.message);
            }
        },

        async cancelBuilderSession() {
            if (!this.builderSessionId) return;

            try {
                await ApiService.delete(`/profile-builder/${this.builderSessionId}`);
            } catch (error) {
                console.warn('Failed to cancel builder session:', error);
            }
        },

        async saveBuilderToProfile() {
            this.closePersonalityBuilder();
            ToastService.success('Profile saved!');
        }
    }
}).mount('#app');
