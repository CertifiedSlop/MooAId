// MooAId Web UI JavaScript

// API base path - empty when served from same origin
const API_BASE = '';

// State
let currentProfile = null;
let profileTags = {
    preferences: [],
    values: [],
    personality: [],
    context: []
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadProfiles();
    loadConfig();
    loadHistory();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Opinion form
    document.getElementById('opinionForm').addEventListener('submit', handleOpinionSubmit);

    // Create profile form
    document.getElementById('createProfileForm').addEventListener('submit', handleCreateProfile);

    // Config form
    document.getElementById('configForm').addEventListener('submit', handleConfigSubmit);

    // Provider select change
    document.getElementById('providerSelect').addEventListener('change', (e) => {
        updateProviderSettings(e.target.value);
    });

    // Profile modal buttons
    document.getElementById('saveProfileBtn').addEventListener('click', handleSaveProfile);
    document.getElementById('deleteProfileBtn').addEventListener('click', handleDeleteProfile);

    // Field tabs
    document.querySelectorAll('#fieldTabs .nav-link').forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const field = e.target.dataset.field;
            switchFieldTab(field);
        });
    });

    // Tag inputs
    ['preferences', 'values', 'personality', 'context'].forEach(field => {
        const input = document.getElementById(`${field}Input`);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addTag(field, input.value.trim());
                input.value = '';
            }
        });
    });
}

// API Helper
async function apiCall(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return response.json();
}

// Show alert
function showAlert(message, type = 'info') {
    const container = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    container.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}

// Load profiles
async function loadProfiles() {
    try {
        const profiles = await apiCall('/profile');
        const select = document.getElementById('profileSelect');
        const list = document.getElementById('profilesList');
        
        select.innerHTML = profiles.map(p => 
            `<option value="${p}">${p}</option>`
        ).join('');
        
        if (profiles.length === 0) {
            list.innerHTML = '<p class="text-muted text-center">No profiles yet. Create one!</p>';
        } else {
            list.innerHTML = profiles.map(p => `
                <div class="d-flex justify-content-between align-items-center p-3 border-bottom">
                    <span><i class="bi bi-person-badge"></i> ${p}</span>
                    <button class="btn btn-sm btn-outline-primary" onclick="editProfile('${p}')">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                </div>
            `).join('');
        }
    } catch (error) {
        showAlert(`Failed to load profiles: ${error.message}`, 'danger');
    }
}

// Load config
async function loadConfig() {
    try {
        const config = await apiCall('/config');

        // Populate form fields
        document.getElementById('providerSelect').value = config.provider;
        document.getElementById('ollamaHost').value = config.ollama_model || '';
        document.getElementById('ollamaModel').value = config.ollama_model || '';

        // Show config info
        document.getElementById('configInfo').innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                <strong>Current:</strong> Provider: ${config.provider} |
                Database: ${config.database_path} |
                API: ${config.api_host}:${config.api_port}
            </div>
        `;

        // Load available models first
        await loadModels();

        // NOW populate model dropdowns with current values (after models are loaded)
        if (config.openrouter_model) {
            const openrouterSelect = document.getElementById('openrouterModel');
            if (openrouterSelect) openrouterSelect.value = config.openrouter_model;
        }
        if (config.openai_model) {
            const openaiSelect = document.getElementById('openaiModel');
            if (openaiSelect) openaiSelect.value = config.openai_model;
        }
        if (config.gemini_model) {
            const geminiSelect = document.getElementById('geminiModel');
            if (geminiSelect) geminiSelect.value = config.gemini_model;
        }

        // Show/hide provider-specific settings
        updateProviderSettings(config.provider);
    } catch (error) {
        showAlert(`Failed to load config: ${error.message}`, 'danger');
    }
}

// Load available models from API
async function loadModels() {
    try {
        const response = await apiCall('/models');
        const models = response.models || {};

        console.log('Loaded models:', Object.keys(models));

        // Populate OpenRouter models
        const openrouterSelect = document.getElementById('openrouterModel');
        if (openrouterSelect && models.openrouter && models.openrouter.length > 0) {
            const currentValue = openrouterSelect.value;
            openrouterSelect.innerHTML = '<option value="">Select a model...</option>' +
                models.openrouter.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
            // Restore previous value if it exists
            if (currentValue) openrouterSelect.value = currentValue;
            console.log(`Populated ${models.openrouter.length} OpenRouter models`);
        }

        // Populate OpenAI models
        const openaiSelect = document.getElementById('openaiModel');
        if (openaiSelect && models.openai && models.openai.length > 0) {
            const currentValue = openaiSelect.value;
            openaiSelect.innerHTML = models.openai.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
            if (currentValue) openaiSelect.value = currentValue;
        }

        // Populate Gemini models
        const geminiSelect = document.getElementById('geminiModel');
        if (geminiSelect && models.gemini && models.gemini.length > 0) {
            const currentValue = geminiSelect.value;
            geminiSelect.innerHTML = models.gemini.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
            if (currentValue) geminiSelect.value = currentValue;
        }

        // Store models for later use
        window.availableModels = models;
    } catch (error) {
        console.error('Failed to load models:', error);
        showAlert('Failed to load models. Using defaults.', 'warning');
    }
}

// Update provider-specific settings visibility
function updateProviderSettings(provider) {
    document.getElementById('openrouterSettings').style.display =
        provider === 'openrouter' ? 'block' : 'none';
    document.getElementById('openaiSettings').style.display =
        provider === 'openai' ? 'block' : 'none';
    document.getElementById('geminiSettings').style.display =
        provider === 'gemini' ? 'block' : 'none';
}

// Toggle key visibility
function toggleKeyVisibility(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';
}

// Load history
async function loadHistory() {
    try {
        const history = await apiCall('/history?limit=20');
        const container = document.getElementById('historyList');

        if (!history || history.length === 0) {
            container.innerHTML = `
                <p class="text-muted text-center py-4">
                    <i class="bi bi-clock-history" style="font-size: 2rem;"></i><br>
                    No history yet. Ask a question to see predictions!
                </p>
            `;
            return;
        }

        container.innerHTML = `
            <div class="scrollable-content">
                ${history.map(item => `
                    <div class="history-item">
                        <div class="history-question">${escapeHtml(item.question)}</div>
                        <div class="history-opinion">${escapeHtml(item.predicted_opinion)}</div>
                        <div class="d-flex justify-content-between align-items-center mt-2">
                            <small class="text-muted">
                                <i class="bi bi-person-badge"></i> ${escapeHtml(item.profile_name)} •
                                <i class="bi bi-cpu"></i> ${escapeHtml(item.provider)} •
                                ${formatDate(item.created_at)}
                            </small>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        document.getElementById('historyList').innerHTML = `
            <p class="text-muted text-center">Unable to load history: ${escapeHtml(error.message)}</p>
        `;
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format date
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Handle config form submission
async function handleConfigSubmit(e) {
    e.preventDefault();

    const provider = document.getElementById('providerSelect').value;

    const configData = {
        provider: provider,
        openrouter_api_key: document.getElementById('openrouterKey').value || undefined,
        openrouter_model: document.getElementById('openrouterModel').value || undefined,
        openai_api_key: document.getElementById('openaiKey').value || undefined,
        openai_model: document.getElementById('openaiModel').value || undefined,
        gemini_api_key: document.getElementById('geminiKey').value || undefined,
        gemini_model: document.getElementById('geminiModel').value || undefined,
        ollama_host: document.getElementById('ollamaHost').value || undefined,
        ollama_model: document.getElementById('ollamaModel').value || undefined
    };

    // Validate OpenRouter model selection
    if (provider === 'openrouter' && !configData.openrouter_model) {
        showAlert('Please select an OpenRouter model', 'warning');
        return;
    }

    try {
        await apiCall('/config', {
            method: 'PUT',
            body: JSON.stringify(configData)
        });

        showAlert('Configuration saved successfully! Restart may be required for some changes.', 'success');
        loadConfig();
    } catch (error) {
        showAlert(`Failed to save configuration: ${error.message}`, 'danger');
    }
}

// Handle opinion submission
async function handleOpinionSubmit(e) {
    e.preventDefault();

    const question = document.getElementById('question').value.trim();
    const profileName = document.getElementById('profileSelect').value;
    const additionalContext = document.getElementById('additionalContext').value.trim();

    if (!question) {
        showAlert('Please enter a question', 'warning');
        return;
    }

    // Show loading overlay
    showLoadingOverlay('Analyzing your question...');

    try {
        const result = await apiCall('/opinion', {
            method: 'POST',
            body: JSON.stringify({
                question,
                profile_name: profileName,
                additional_context: additionalContext ? [additionalContext] : undefined
            })
        });

        // Display result with better formatting
        document.getElementById('resultOpinion').textContent = result.predicted_opinion;
        document.getElementById('resultReasoning').textContent = result.reasoning;
        document.getElementById('resultModel').textContent = `${result.provider} • ${result.model}`;
        document.getElementById('resultProfile').textContent = `Profile: ${result.profile_used}`;
        document.getElementById('opinionResult').style.display = 'block';

        // Scroll to result
        document.getElementById('opinionResult').scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        showAlert('Opinion predicted successfully!', 'success');
    } catch (error) {
        showAlert(`Failed to get prediction: ${error.message}`, 'danger');
    } finally {
        hideLoadingOverlay();
    }
}

// Show loading overlay
function showLoadingOverlay(message = 'Loading...') {
    document.getElementById('loadingText').textContent = message;
    document.getElementById('loadingOverlay').classList.add('active');
}

// Hide loading overlay
function hideLoadingOverlay() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// Handle create profile
async function handleCreateProfile(e) {
    e.preventDefault();
    
    const name = document.getElementById('newProfileName').value.trim();
    
    if (!name) {
        showAlert('Please enter a profile name', 'warning');
        return;
    }
    
    try {
        await apiCall('/profile', {
            method: 'POST',
            body: JSON.stringify({ name })
        });
        
        document.getElementById('newProfileName').value = '';
        showAlert(`Profile "${name}" created successfully!`, 'success');
        loadProfiles();
    } catch (error) {
        showAlert(`Failed to create profile: ${error.message}`, 'danger');
    }
}

// Edit profile
async function editProfile(name) {
    try {
        const profile = await apiCall(`/profile/${name}`);
        
        currentProfile = name;
        profileTags = {
            preferences: profile.preferences || [],
            values: profile.values || [],
            personality: profile.personality || [],
            context: profile.context || []
        };
        
        document.getElementById('editProfileName').value = name;
        document.getElementById('profileModalTitle').textContent = `Edit: ${name}`;
        
        renderTags('preferences');
        renderTags('values');
        renderTags('personality');
        renderTags('context');
        
        const modal = new bootstrap.Modal(document.getElementById('profileModal'));
        modal.show();
    } catch (error) {
        showAlert(`Failed to load profile: ${error.message}`, 'danger');
    }
}

// Switch field tab
function switchFieldTab(field) {
    document.querySelectorAll('#fieldTabs .nav-link').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.field === field);
    });
    
    document.querySelectorAll('.tab-content .tab-pane').forEach(pane => {
        pane.classList.toggle('show', pane.id === `${field}Tab`);
        pane.classList.toggle('active', pane.id === `${field}Tab`);
    });
    
    document.getElementById(`${field}Input`).focus();
}

// Render tags
function renderTags(field) {
    const container = document.getElementById(`${field}Tags`);
    container.innerHTML = profileTags[field].map((tag, index) => `
        <span class="profile-badge">
            ${tag}
            <i class="bi bi-x" style="cursor: pointer; margin-left: 5px;" 
               onclick="removeTag('${field}', ${index})"></i>
        </span>
    `).join('');
}

// Add tag
function addTag(field, tag) {
    if (tag && !profileTags[field].includes(tag)) {
        profileTags[field].push(tag);
        renderTags(field);
    }
}

// Remove tag
function removeTag(field, index) {
    profileTags[field].splice(index, 1);
    renderTags(field);
}

// Handle save profile
async function handleSaveProfile() {
    if (!currentProfile) return;
    
    try {
        await apiCall(`/profile/${currentProfile}`, {
            method: 'PUT',
            body: JSON.stringify({
                preferences: profileTags.preferences,
                values: profileTags.values,
                personality: profileTags.personality,
                context: profileTags.context
            })
        });
        
        showAlert('Profile saved successfully!', 'success');
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
        modal.hide();
    } catch (error) {
        showAlert(`Failed to save profile: ${error.message}`, 'danger');
    }
}

// Handle delete profile
async function handleDeleteProfile() {
    if (!currentProfile) return;
    
    if (!confirm(`Are you sure you want to delete profile "${currentProfile}"?`)) {
        return;
    }
    
    try {
        await apiCall(`/profile/${currentProfile}`, {
            method: 'DELETE'
        });
        
        showAlert(`Profile "${currentProfile}" deleted!`, 'success');
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
        modal.hide();
        
        loadProfiles();
    } catch (error) {
        showAlert(`Failed to delete profile: ${error.message}`, 'danger');
    }
}
