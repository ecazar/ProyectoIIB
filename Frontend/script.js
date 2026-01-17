// Variables globales
let currentImage = null;
let currentImagePreview = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const fileInput = document.getElementById('fileInput');
    const imageBtn = document.getElementById('imageBtn');
    const sendBtn = document.getElementById('sendBtn');

    searchInput.addEventListener('keypress', handleKeyPress);
    fileInput.addEventListener('change', handleImageUpload);
    imageBtn.addEventListener('click', () => fileInput.click());
    sendBtn.addEventListener('click', handleSearch);
});

// Funciones principales
function addMessage(content, isUser = false) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (typeof content === 'string') {
        contentDiv.innerHTML = content;
    } else {
        contentDiv.appendChild(content);
    }

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        handleSearch();
    }
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        currentImage = file;
        const reader = new FileReader();
        reader.onload = function(e) {
            currentImagePreview = e.target.result;
            showImagePreview(file.name, file.size, e.target.result);

            const searchInput = document.getElementById('searchInput');
            searchInput.placeholder = 'Describe qué buscas en esta imagen (opcional)...';
            searchInput.focus();
        };
        reader.readAsDataURL(file);
    }
}

function showImagePreview(fileName, fileSize, imageSrc) {
    const previewContainer = document.getElementById('imagePreviewContainer');
    const sizeInKB = (fileSize / 1024).toFixed(2);

    previewContainer.innerHTML = `
        <div class="image-preview-container">
            <img src="${imageSrc}" alt="Preview">
            <div class="image-info">
                <div class="image-name">📎 ${fileName}</div>
                <div class="image-size">${sizeInKB} KB</div>
            </div>
            <button class="remove-image" onclick="removeImage()">✕</button>
        </div>
    `;
}

function removeImage() {
    currentImage = null;
    currentImagePreview = null;
    document.getElementById('imagePreviewContainer').innerHTML = '';
    document.getElementById('fileInput').value = '';

    const searchInput = document.getElementById('searchInput');
    searchInput.placeholder = 'Describe lo que buscas...';
}

async function handleSearch() {
    const input = document.getElementById('searchInput');
    const query = input.value.trim();

    if (!query && !currentImage) {
        addMessage('⚠️ Por favor, escribe una búsqueda o sube una imagen.', false);
        return;
    }

    // Mostrar mensaje del usuario
    const userMessageContent = document.createElement('div');

    if (currentImage && currentImagePreview) {
        const img = document.createElement('img');
        img.src = currentImagePreview;
        img.className = 'image-preview';
        userMessageContent.appendChild(img);
    }

    if (query) {
        const text = document.createElement('p');
        text.textContent = query;
        text.style.marginTop = currentImage ? '12px' : '0';
        userMessageContent.appendChild(text);
    } else if (currentImage) {
        const text = document.createElement('p');
        text.textContent = '🔍 Búsqueda por imagen';
        text.style.marginTop = '12px';
        text.style.fontSize = '16px';
        text.style.opacity = '0.9';
        userMessageContent.appendChild(text);
    }

    addMessage(userMessageContent, true);

    // Limpiar input y preview
    input.value = '';
    document.getElementById('imagePreviewContainer').innerHTML = '';

    // Mostrar loading
    const loadingMsg = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <div class="loading"></div>
            <span style="font-size: 17px; font-weight: 600;">Buscando los mejores productos para ti...</span>
        </div>
    `;
    addMessage(loadingMsg, false);

    try {
        const formData = new FormData();

        if (currentImage) {
            formData.append('image', currentImage);
            formData.append('type', 'image');
            if (query) {
                formData.append('query', query);
            }
        } else {
            formData.append('query', query);
            formData.append('type', 'text');
        }

        // Llamada al backend
        const response = await fetch('http://localhost:5000/search', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Error en la búsqueda');
        }

        const data = await response.json();

        // Remover loading
        const messages = document.querySelectorAll('.message');
        messages[messages.length - 1].remove();

        // Mostrar explicación de IA primero
        if (data.ai_explanation) {
            addMessage(data.ai_explanation, false);
        }

        // Mostrar resultados
        if (data.results && data.results.length > 0) {
            displayResults(data.results);
        } else {
            addMessage('😔 No se encontraron resultados para tu búsqueda.', false);
        }

    } catch (error) {
        console.error('Error:', error);

        // Remover loading
        const messages = document.querySelectorAll('.message');
        if (messages.length > 0) {
            messages[messages.length - 1].remove();
        }

        addMessage(`❌ Hubo un error al procesar tu búsqueda: ${error.message}. Por favor, asegúrate de que el servidor está corriendo.`, false);
    } finally {
        // Limpiar imagen actual y restaurar placeholder
        currentImage = null;
        currentImagePreview = null;
        document.getElementById('fileInput').value = '';
        const searchInput = document.getElementById('searchInput');
        searchInput.placeholder = 'Describe lo que buscas...';
    }
}

function displayResults(results) {
    if (!results || results.length === 0) {
        return;
    }

    const container = document.createElement('div');

    const title = document.createElement('p');
    title.style.fontSize = '20px';
    title.style.fontWeight = '700';
    title.style.marginBottom = '16px';
    title.innerHTML = `✨ Aquí están los <strong style="color: #8b5cf6; font-size: 24px;">${results.length}</strong> productos que encontré:`;
    container.appendChild(title);

    const grid = document.createElement('div');
    grid.className = 'results-grid';

    results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'result-card';
        card.onclick = () => showProductDetail(item);

        card.innerHTML = `
            <img src="${item.ImageURL || 'https://via.placeholder.com/400x500/8b5cf6/ffffff?text=No+Image'}"
                 alt="${item.ProductTitle}"
                 onerror="this.src='https://via.placeholder.com/400x500/8b5cf6/ffffff?text=Error'">
            <div class="result-info">
                <div class="result-title">${item.ProductTitle}</div>
                <div class="result-meta">📦 ${item.SubCategory}</div>
                <div class="result-meta">🎨 ${item.Colour}</div>
                <div class="result-meta">👔 ${item.Usage}</div>
                <div class="result-score">⭐ ${item.rerank_score}</div>
            </div>
        `;

        grid.appendChild(card);
    });

    container.appendChild(grid);
    addMessage(container, false);
}

function showProductDetail(item) {
    const detail = `
        <div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(236, 72, 153, 0.08) 100%);
                    padding: 20px;
                    border-radius: 16px;
                    border: 2px solid rgba(139, 92, 246, 0.3);">
            <h3 style="font-size: 22px; font-weight: 700; color: #8b5cf6; margin-bottom: 14px;">
                ${item.ProductTitle}
            </h3>
            <div style="font-size: 17px; line-height: 1.8; color: #1e293b;">
                <div style="margin-bottom: 8px;"><strong>📦 Categoría:</strong> ${item.SubCategory}</div>
                <div style="margin-bottom: 8px;"><strong>🎨 Color:</strong> ${item.Colour}</div>
                <div style="margin-bottom: 8px;"><strong>👔 Uso:</strong> ${item.Usage}</div>
                <div style="margin-top: 12px;">
                    <strong>⭐ Relevancia:</strong>
                    <span style="color: #8b5cf6; font-weight: 700; font-size: 18px;">${item.rerank_score}</span>
                </div>
            </div>
        </div>
    `;
    addMessage(detail, false);
}