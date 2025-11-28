// API Configuration
const API_BASE_URL = 'http://127.0.0.1:5001/api';

// State
let currentStore = null;
let uploadedFiles = [];

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const filesList = document.getElementById('filesList');
const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

// Debug Logger
function log(msg) {
    const logDiv = document.getElementById('debug-log');
    if (logDiv) {
        const time = new Date().toLocaleTimeString();
        logDiv.innerHTML += `<div>[${time}] ${msg}</div>`;
        logDiv.scrollTop = logDiv.scrollHeight;
    }
    console.log(msg);
}

// Initialize
async function init() {
    log('Starting initialization...');
    setupEventListeners();

    // Test basic connectivity first
    try {
        log(`Testing connection to ${API_BASE_URL}/health...`);
        const health = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
        log(`Health check status: ${health.status}`);
    } catch (e) {
        log(`Health check failed: ${e.message}`);
    }

    await createStore();
    await loadExistingFiles();
}

// Setup Event Listeners
function setupEventListeners() {
    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const mainContent = document.querySelector('.main-content');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            mainContent.classList.toggle('sidebar-collapsed');
        });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', () => {
            mainContent.classList.add('sidebar-collapsed');
        });
    }

    // File upload
    uploadArea.addEventListener('click', () => fileInput.click());
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // Chat
    sendBtn.addEventListener('click', sendQuestion);
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });
    questionInput.addEventListener('input', handleInputChange);
}

// Create File Search Store
async function createStore() {
    try {
        showLoading('Initializing File Search store...');
        log('Calling create-store...');

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${API_BASE_URL}/create-store`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ display_name: 'RAG-Document-Store' }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        log(`create-store response: ${response.status}`);

        const data = await response.json();

        if (data.success) {
            currentStore = data.store_name;
            updateStatus('Ready', true);
            log('Store created successfully');
        } else {
            updateStatus('Error', false);
            showError('Failed to create store: ' + data.error);
            log('Store creation failed: ' + data.error);
        }
    } catch (error) {
        updateStatus('Error', false);
        showError('Failed to connect: ' + error.message);
        log('Create store error: ' + error.message);
        log('Stack: ' + error.stack);
    } finally {
        hideLoading();
        log('Finished createStore');
    }
}

// Load Existing Files
async function loadExistingFiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/list-files`);
        const data = await response.json();

        if (data.success && data.files) {
            uploadedFiles = data.files.map(f => ({
                name: f.name,
                size: 0, // Size not stored in index, but that's okay
                metadata: {
                    summary: f.summary,
                    topics: f.topics
                },
                doc_id: f.id
            }));
            updateFilesList();

            if (uploadedFiles.length > 0) {
                showSuccess(`Loaded ${uploadedFiles.length} existing documents`);
                handleInputChange(); // Enable chat if files exist
            }
        }
    } catch (error) {
        console.error('Error loading existing files:', error);
    }
}

// File Upload Handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const files = Array.from(e.dataTransfer.files);
    uploadFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    uploadFiles(files);
    e.target.value = ''; // Reset input
}

async function uploadFiles(files) {
    for (const file of files) {
        // Validate file type
        const validTypes = ['text/plain', 'text/markdown', 'application/pdf'];
        const validExtensions = ['.txt', '.md', '.pdf'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

        if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
            showError(`Invalid file type: ${file.name}. Only TXT, MD, and PDF files are supported.`);
            continue;
        }

        await uploadFile(file);
    }
}

async function uploadFile(file) {
    try {
        showLoading(`Uploading ${file.name}...`);

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/upload-file`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            uploadedFiles.push({
                name: file.name,
                size: file.size,
                metadata: data.metadata,
                doc_id: data.doc_id
            });
            updateFilesList();
            showSuccess(`${file.name} uploaded successfully!`);
        } else {
            showError(`Failed to upload ${file.name}: ${data.error}`);
        }
    } catch (error) {
        showError(`Error uploading ${file.name}: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Update Files List
function updateFilesList() {
    if (uploadedFiles.length === 0) {
        filesList.innerHTML = '<p class="empty-state">No files uploaded yet</p>';
        return;
    }

    filesList.innerHTML = uploadedFiles.map(file => {
        const summary = file.metadata?.summary ? `<div class="file-summary" title="${file.metadata.summary}">${file.metadata.summary.substring(0, 80)}...</div>` : '';
        const topics = file.metadata?.topics ? `<div class="file-topics">${file.metadata.topics.slice(0, 3).map(t => `<span class="topic-tag">${t}</span>`).join('')}</div>` : '';

        return `
        <div class="file-item">
            <div class="file-icon">${file.name.split('.').pop().toUpperCase()}</div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                ${summary}
                ${topics}
            </div>
        </div>
    `}).join('');
}

// Chat Functions
function handleInputChange() {
    const hasText = questionInput.value.trim().length > 0;
    const hasFiles = uploadedFiles.length > 0;
    sendBtn.disabled = !hasText || !hasFiles;

    // Auto-resize textarea
    questionInput.style.height = 'auto';
    questionInput.style.height = questionInput.scrollHeight + 'px';
}

async function sendQuestion() {
    const question = questionInput.value.trim();

    if (!question || uploadedFiles.length === 0) return;

    // Clear input
    questionInput.value = '';
    questionInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Remove welcome message if present
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add user message
    addMessage('user', question);

    try {
        showLoading('Thinking...');
        console.log('Sending request to /api/ask...');

        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        console.log('Response received:', response.status, response.statusText);
        hideLoading(); // Hide loading immediately as stream starts

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        // Create empty message for streaming
        const messageId = addMessage('assistant', '', [], null, true);
        const messageContent = document.getElementById(`msg-text-${messageId}`);
        const messageContainer = document.getElementById(`msg-container-${messageId}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';

        console.log('Starting stream reading...');

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                console.log('Stream complete');
                break;
            }

            const chunk = decoder.decode(value, { stream: true });
            console.log('Received chunk:', chunk);
            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;

                try {
                    const data = JSON.parse(line);

                    if (data.type === 'chunk') {
                        fullText += data.text;
                        // Optimize: Append text node instead of setting innerHTML repeatedly
                        // But since we might have markdown/html later, we can stick to innerHTML 
                        // BUT only update if we really need to. 
                        // Actually, for simple text streaming, textContent is faster but we lose formatting.
                        // Let's keep innerHTML but use instant scroll.
                        messageContent.innerHTML = escapeHtml(fullText);
                        scrollToBottom('auto'); // Instant scroll to prevent jitter
                    } else if (data.type === 'complete') {
                        // Add citations and retrieval info
                        updateMessageMetadata(messageId, data.citations, data.retrieval_info);
                    } else if (data.type === 'error') {
                        showError('Streaming error: ' + data.error);
                    } else if (data.type === 'tool_call') {
                        addToolLog(messageId, 'call', data.tool, data.args);
                    } else if (data.type === 'tool_result') {
                        addToolLog(messageId, 'result', data.tool, data.result);
                    } else if (data.type === 'judge_result') {
                        addJudgeLog(messageId, data);
                    }
                } catch (e) {
                    console.error('Error parsing stream line:', line, e);
                }
            }
        }
    } catch (error) {
        console.error('Fetch error:', error);
        hideLoading();
        showError('Error: ' + error.message);
    } finally {
        sendBtn.disabled = false;
    }
}

function addMessage(role, text, citations = [], retrievalInfo = null, isStreaming = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    const messageId = Date.now();
    messageDiv.id = `msg-container-${messageId}`;

    const avatar = role === 'user' ? 'You' : 'AI';

    let toolLogsHtml = '';
    if (role === 'assistant') {
        toolLogsHtml = `
            <div class="reasoning-accordion">
                <div class="reasoning-header" onclick="toggleReasoning(${messageId})">
                    <span class="reasoning-title">Thought Process</span>
                    <span class="reasoning-icon" id="reasoning-icon-${messageId}">▼</span>
                </div>
                <div class="reasoning-content tool-logs" id="tool-logs-${messageId}"></div>
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div id="retrieval-${messageId}"></div>
            ${toolLogsHtml}
            <div class="message-text" id="msg-text-${messageId}">${escapeHtml(text)}</div>
            <div id="citations-${messageId}"></div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    if (!isStreaming && (citations.length > 0 || retrievalInfo)) {
        updateMessageMetadata(messageId, citations, retrievalInfo);
    }

    return messageId;
}

function toggleReasoning(messageId) {
    const content = document.getElementById(`tool-logs-${messageId}`);
    const icon = document.getElementById(`reasoning-icon-${messageId}`);

    if (content.style.display === 'none') {
        content.style.display = 'flex';
        icon.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        icon.style.transform = 'rotate(-90deg)';
    }
}

function updateMessageMetadata(messageId, citations, retrievalInfo) {
    // Update Retrieval Info
    if (retrievalInfo) {
        const retrievalDiv = document.getElementById(`retrieval-${messageId}`);
        const intent = retrievalInfo.question_analysis?.intent || 'Unknown intent';
        const chunks = retrievalInfo.total_chunks_used || 0;

        retrievalDiv.innerHTML = `
            <div class="retrieval-info">
                <div class="retrieval-header">
                    <span>🔍 Analysis</span>
                    <span class="retrieval-stats">${chunks} chunks used</span>
                </div>
                <div class="retrieval-details">
                    <div class="retrieval-intent"><strong>Intent:</strong> ${intent}</div>
                </div>
            </div>
        `;
    }

    // Update Citations
    if (citations && citations.length > 0) {
        const citationsDiv = document.getElementById(`citations-${messageId}`);
        const topCitations = citations.slice(0, 5);
        const remainingCount = citations.length - 5;

        citationsDiv.innerHTML = `
            <div class="citations">
                <div class="citations-title">Sources${citations.length > 5 ? ` (showing top 5 of ${citations.length})` : ''}</div>
                ${topCitations.map((c, i) => `
                    <div class="citation-item">
                        <div class="citation-header" onclick="document.getElementById('snippet-${messageId}-${i}').classList.toggle('visible')">
                            <span class="citation-icon">📄</span>
                            <span class="citation-title">${c.title}</span>
                            ${c.chunks_used ? `<span class="chunk-badge">${c.chunks_used} chunks</span>` : ''}
                            <span class="citation-toggle">▼</span>
                        </div>
                        <div id="snippet-${messageId}-${i}" class="citation-snippet">
                            ${c.snippet ? escapeHtml(c.snippet) : 'No preview available'}
                        </div>
                    </div>
                `).join('')}
                ${remainingCount > 0 ? `<div class="citation-item" style="opacity: 0.6; font-style: italic;">+ ${remainingCount} more source${remainingCount > 1 ? 's' : ''}</div>` : ''}
            </div>
        `;
    }

    const chatMessages = document.getElementById('chatMessages');
    scrollToBottom();
}

function addToolLog(messageId, type, toolName, data) {
    const logsContainer = document.getElementById(`tool-logs-${messageId}`);
    if (!logsContainer) return;

    const logItem = document.createElement('div');
    logItem.className = `tool-log-item ${type}`;

    const icon = type === 'call' ? '🔧' : '✅';
    const title = type === 'call' ? `Calling ${toolName}...` : `${toolName} Result`;

    // Format JSON for display
    const jsonContent = JSON.stringify(data, null, 2);

    logItem.innerHTML = `
        <div class="tool-log-header" onclick="this.nextElementSibling.classList.toggle('expanded')">
            <span class="tool-icon">${icon}</span>
            <span class="tool-name">${title}</span>
            <span class="tool-toggle">▼</span>
        </div>
        <div class="tool-log-content">
            <pre>${escapeHtml(jsonContent)}</pre>
        </div>
    `;

    logsContainer.appendChild(logItem);

    logsContainer.appendChild(logItem);

    // Auto-scroll
    scrollToBottom();
}

function addJudgeLog(messageId, data) {
    const logsContainer = document.getElementById(`tool-logs-${messageId}`);
    if (!logsContainer) return;

    const logItem = document.createElement('div');
    logItem.className = `tool-log-item judge ${data.verdict}`;

    const icon = '⚖️';
    const title = `Judge Verdict: ${data.verdict.toUpperCase()}`;

    // Format explanation
    const explanation = data.explanation || "No explanation provided.";

    logItem.innerHTML = `
        <div class="tool-log-header" onclick="this.nextElementSibling.classList.toggle('expanded')">
            <span class="tool-icon">${icon}</span>
            <span class="tool-name">${title}</span>
            <span class="tool-toggle">▼</span>
        </div>
        <div class="tool-log-content expanded">
            <div class="judge-explanation">
                <strong>Critique:</strong><br>
                ${escapeHtml(explanation).replace(/\n/g, '<br>')}
            </div>
            ${data.requires_more_evidence ? '<div class="judge-status">Requesting more evidence...</div>' : ''}
        </div>
    `;

    logsContainer.appendChild(logItem);

    logsContainer.appendChild(logItem);

    // Auto-scroll
    scrollToBottom();
}

// Utility Functions
function updateStatus(text, isOnline) {
    statusText.textContent = text;
    statusDot.style.background = isOnline ? 'var(--success-color)' : 'var(--error-color)';
}

function showLoading(text) {
    loadingText.textContent = text;
    loadingOverlay.classList.add('active');
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
}

function showError(message) {
    console.error(message);
    addMessage('assistant', `❌ Error: ${message}`);
}

function showSuccess(message) {
    console.log(message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom(behavior = 'smooth') {
    requestAnimationFrame(() => {
        if (chatMessages.lastElementChild) {
            chatMessages.lastElementChild.scrollIntoView({ behavior: behavior, block: 'end' });
        } else {
            chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: behavior });
        }
    });
}

// Initialize app
init();
