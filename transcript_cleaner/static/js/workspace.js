// Teams Transcript Cleaner - Workspace JavaScript

// Global variables
let sessionCost = 0.0;
let originalText = '';
let correctedText = '';

// Utility function to get CSRF token
function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

// Model pricing (per 1000 tokens)
const MODEL_PRICING = {
    'gpt-4o': 0.01,
    'gpt-4-turbo': 0.01,
    'gpt-4': 0.03,
    'gpt-3.5-turbo': 0.0015
};


// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    updateModelPrice();
    checkApiKey();
    updateProcessingMode();
    initializeCSVEditor();
});

// API Key check
function checkApiKey() {
    fetch('/api/v1/check-api-key/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            const statusElement = document.getElementById('api-key-status');
            const textElement = document.getElementById('api-key-text');
            
            if (data.status === 'valid') {
                statusElement.className = 'cost-info';
                textElement.innerHTML = '<i class="fas fa-check-circle text-success me-2"></i>APIキー設定済み';
            } else if (data.status === 'missing') {
                statusElement.className = 'warning-info';
                textElement.innerHTML = '<i class="fas fa-exclamation-triangle text-warning me-2"></i>APIキーが設定されていません';
            } else {
                statusElement.className = 'warning-info';
                textElement.innerHTML = '<i class="fas fa-exclamation-triangle text-warning me-2"></i>APIキーが無効です';
            }
        })
        .catch(error => {
            const statusElement = document.getElementById('api-key-status');
            const textElement = document.getElementById('api-key-text');
            statusElement.className = 'warning-info';
            textElement.innerHTML = '<i class="fas fa-exclamation-triangle text-danger me-2"></i>APIキーチェック失敗';
        });
}

// Update model price display
function updateModelPrice() {
    const model = document.getElementById('ai-model').value;
    const price = MODEL_PRICING[model] || 0.01;
    document.getElementById('model-price').textContent = `料金: $${price} USD / 1000トークン`;
}

// Update processing mode UI
function updateProcessingMode() {
    const radios = document.querySelectorAll('input[name="processing_mode"]');
    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            const csvSection = document.getElementById('csv-section');
            const csvEditorSection = document.getElementById('csv-editor-section');
            
            if (this.value === 'misspelling') {
                csvSection.style.display = 'block';
                csvEditorSection.style.display = 'block';
            } else {
                csvSection.style.display = 'none';
                csvEditorSection.style.display = 'none';
            }
            
            updateCorrectionButton();
        });
    });
}

// Initialize CSV editor
function initializeCSVEditor() {
    const csvEditor = document.getElementById('csv-editor');
    csvEditor.value = '誤,正\nマイクロソフト,Microsoft\nエクセル,Excel';
    
    csvEditor.addEventListener('input', function() {
        updateCorrectionButton();
    });
}

// Load TXT file
function loadTxtFile(input) {
    const file = input.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        originalText = content;
        document.getElementById('original-text').value = content;
        
        // Show file info
        const tokens = estimateTokens(content);
        const model = document.getElementById('ai-model').value;
        const cost = estimateCost(tokens, model);
        
        const infoDiv = document.getElementById('txt-file-info');
        infoDiv.innerHTML = `
            <div class="file-info mt-2">
                <i class="fas fa-info-circle me-2"></i>
                テキスト長: ${content.length}文字, 
                概算トークン数: ${tokens}, 
                概算コスト: $${cost.toFixed(4)} USD
            </div>
        `;
        
        updateCorrectionButton();
    };
    reader.readAsText(file, 'utf-8');
}

// Load CSV file
function loadCsvFile(input) {
    const file = input.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        document.getElementById('csv-editor').value = content;
        updateCorrectionButton();
    };
    reader.readAsText(file, 'utf-8');
}

// Estimate tokens (rough calculation)
function estimateTokens(text) {
    // Very rough estimation: 1 token ≈ 0.75 words for English, adjust for Japanese
    const words = text.split(/\s+/).length;
    return Math.ceil(words * 1.3); // Adjust for Japanese character density
}

// Estimate cost
function estimateCost(tokens, model) {
    const pricePerToken = MODEL_PRICING[model] / 1000;
    return tokens * pricePerToken;
}

// Update correction button state
function updateCorrectionButton() {
    const button = document.getElementById('correction-button');
    const originalText = document.getElementById('original-text').value;
    const processingMode = document.querySelector('input[name="processing_mode"]:checked').value;
    
    let canExecute = !!originalText;
    
    if (processingMode === 'misspelling') {
        const csvContent = document.getElementById('csv-editor').value.trim();
        canExecute = canExecute && csvContent && validateCSV(csvContent);
    }
    
    button.disabled = !canExecute;
    updateOtherButtons();
}

// Validate CSV content
function validateCSV(csvContent) {
    const lines = csvContent.split('\n').filter(line => line.trim());
    if (lines.length < 2) return false; // At least header + 1 data row
    
    const header = lines[0].split(',');
    if (header.length < 2 || header[0].trim() !== '誤' || header[1].trim() !== '正') {
        return false;
    }
    
    // Check data rows
    for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',');
        if (cols.length < 2 || !cols[0].trim() || !cols[1].trim()) {
            return false;
        }
    }
    
    return true;
}

// Execute correction
function executeCorrection() {
    const button = document.getElementById('correction-button');
    const originalText = document.getElementById('original-text').value;
    const processingMode = document.querySelector('input[name="processing_mode"]:checked').value;
    const customPrompt = document.getElementById('custom-prompt').value;
    const model = document.getElementById('ai-model').value;
    const csvContent = document.getElementById('csv-editor').value;
    
    if (!originalText) {
        alert('訂正前議事録をアップロードしてください');
        return;
    }
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>処理中...';
    
    const requestData = {
        input_text: originalText,
        processing_mode: processingMode,
        custom_prompt: customPrompt,
        model: model,
        csv_content: processingMode === 'misspelling' ? csvContent : ''
    };
    
    
    fetch('/api/v1/corrections/execute/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            correctedText = data.corrected_text;
            document.getElementById('corrected-text').value = correctedText;
            
            // Update costs
            const actualCost = parseFloat(data.cost);
            sessionCost += actualCost;
            document.getElementById('session-cost').textContent = sessionCost.toFixed(4);
            
            // Update remaining budget
            const currentTotal = parseFloat(document.getElementById('total-cost').textContent) + actualCost;
            document.getElementById('total-cost').textContent = currentTotal.toFixed(4);
            
            // Calculate remaining budget from current display values
            const remainingElement = document.getElementById('remaining-budget');
            const currentRemaining = parseFloat(remainingElement.textContent);
            const newRemaining = currentRemaining - actualCost;
            remainingElement.textContent = newRemaining.toFixed(4);
            
            // Enable other buttons
            updateOtherButtons();
            
            alert(`${getModeDisplayName(processingMode)}が完了しました（コスト: $${actualCost.toFixed(4)} USD）`);
        } else {
            alert('処理中にエラーが発生しました: ' + data.error);
        }
    })
    .catch(error => {
        alert('処理中にエラーが発生しました');
    })
    .finally(() => {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-magic me-2"></i>訂正実行';
        updateOtherButtons();
    });
}

// Get mode display name
function getModeDisplayName(mode) {
    const names = {
        'misspelling': '訂正',
        'grammar': '校正',
        'summarize': '要約'
    };
    return names[mode] || '処理';
}

// Toggle diff display
function toggleDiff() {
    const checkbox = document.getElementById('show-diff');
    const viewer = document.getElementById('diff-viewer');
    
    if (checkbox.checked) {
        viewer.style.display = 'block';
        updateDiff();
    } else {
        viewer.style.display = 'none';
    }
}

// Update diff display
function updateDiff() {
    const checkbox = document.getElementById('show-diff');
    if (!checkbox.checked) return;
    
    const original = document.getElementById('original-text').value;
    const corrected = document.getElementById('corrected-text').value;
    const viewer = document.getElementById('diff-viewer');
    
    if (!original || !corrected) {
        viewer.innerHTML = '<em>差分を表示するには両方のテキストが必要です</em>';
        return;
    }
    
    const diffHtml = generateDiffHTML(original, corrected);
    viewer.innerHTML = diffHtml;
}

// Generate diff HTML (simplified version)
function generateDiffHTML(original, corrected) {
    const originalLines = original.split('\n');
    const correctedLines = corrected.split('\n');
    const maxLines = Math.max(originalLines.length, correctedLines.length);
    
    let html = '';
    for (let i = 0; i < maxLines; i++) {
        const origLine = originalLines[i] || '';
        const corrLine = correctedLines[i] || '';
        
        if (origLine === corrLine) {
            html += `<div>${escapeHtml(origLine)}</div>`;
        } else {
            html += `<div>`;
            if (origLine) {
                html += `<span class="diff-removed">${escapeHtml(origLine)}</span> `;
            }
            if (corrLine) {
                html += `<span class="diff-added">${escapeHtml(corrLine)}</span>`;
            }
            html += `</div>`;
        }
    }
    
    return html;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Copy corrected text to original
function copyToOriginal() {
    const corrected = document.getElementById('corrected-text').value;
    if (!corrected) return;
    
    document.getElementById('original-text').value = corrected;
    originalText = corrected;
    
    // Clear corrected text
    document.getElementById('corrected-text').value = '';
    correctedText = '';
    
    // Hide diff
    document.getElementById('show-diff').checked = false;
    document.getElementById('diff-viewer').style.display = 'none';
    
    updateOtherButtons();
}

// Download result
function downloadResult() {
    const content = document.getElementById('corrected-text').value;
    if (!content) return;
    
    const now = new Date();
    const timestamp = now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_');
    const filename = `final_transcript_${timestamp}.txt`;
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Update other buttons state
function updateOtherButtons() {
    const correctedText = document.getElementById('corrected-text').value;
    const hasCorrectedText = !!correctedText;
    
    document.getElementById('copy-button').disabled = !hasCorrectedText;
    document.getElementById('download-button').disabled = !hasCorrectedText;
    document.getElementById('show-diff').disabled = !hasCorrectedText;
}

// Reset cost
function resetCost() {
    if (!confirm('コスト履歴をリセットしますか？')) return;
    
    fetch('/api/v1/users/reset-cost/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('total-cost').textContent = '0.0000';
            document.getElementById('remaining-budget').textContent = '{{ user.api_usage_limit }}';
            alert('コスト履歴をリセットしました。');
        } else {
            alert('リセットに失敗しました。');
        }
    })
    .catch(error => {
        alert('リセットに失敗しました。');
    });
}