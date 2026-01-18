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
            document.getElementById('searchInput').placeholder = 'Describe qué buscas en esta imagen...';
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
    document.getElementById('searchInput').placeholder = 'Describe lo que buscas...';
}

async function handleSearch() {
    const input = document.getElementById('searchInput');
    const query = input.value.trim();

    if (!query && !currentImage) {
        addMessage('⚠️ Por favor, escribe una búsqueda o sube una imagen.', false);
        return;
    }

    // Mostrar mensaje del usuario en el chat
    const userMessageContent = document.createElement('div');
    if (currentImage && currentImagePreview) {
        const img = document.createElement('img');
        img.src = currentImagePreview;
        img.className = 'image-preview';
        img.style.maxWidth = '200px';
        userMessageContent.appendChild(img);
    }
    if (query) {
        const text = document.createElement('p');
        text.textContent = query;
        userMessageContent.appendChild(text);
    }
    addMessage(userMessageContent, true);

    // Limpiar UI
    input.value = '';
    removeImage();

    // Mostrar loading con ID único para removerlo luego
    const loadingId = 'loading-' + Date.now();
    const loadingMsg = `
        <div id="${loadingId}" style="display: flex; align-items: center; gap: 12px;">
            <div class="loading"></div>
            <span style="font-size: 16px;">Analizando tu estilo...</span>
        </div>
    `;
    addMessage(loadingMsg, false);

    try {
        const formData = new FormData();
        if (currentImage) {
            formData.append('file', currentImage);
            if (query) formData.append('message', query);
        } else {
            formData.append('message', query);
        }

        const endpoint = currentImage ? 'http://localhost:8000/search-image' : 'http://localhost:8000/chat';

        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Error en el servidor');

        const data = await response.json();

        // Remover el loading usando el ID
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.closest('.message').remove();
        }

        // --- INTEGRACIÓN CON LAS LLAVES DEL BACKEND ---
        // data.answer contiene el texto de Gemini
        if (data.answer) {
            addMessage(data.answer, false);
        }

        // data.items contiene la lista de productos
        if (data.items && data.items.length > 0) {
            displayResults(data.items);
        } else if (!data.answer) {
            addMessage('😔 No encontré productos exactos en nuestro catálogo.', false);
        }

    } catch (error) {
        console.error('Error:', error);
        addMessage(`❌ Error: ${error.message}. Verifica que el backend esté activo.`, false);
    }
}

function displayResults(results) {
    const container = document.createElement('div');
    container.innerHTML = `<p style="font-weight: 700; margin-bottom: 12px;">✨ Resultados encontrados:</p>`;

    const grid = document.createElement('div');
    grid.className = 'results-grid'; // Asegúrate de tener esto en tu CSS

    results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'result-card';
        card.onclick = () => showProductDetail(item);

        card.innerHTML = `
            <img src="${item.ImageURL || 'https://via.placeholder.com/200'}" alt="${item.ProductTitle}">
            <div class="result-info">
                <div class="result-title">${item.ProductTitle}</div>
                <div class="result-meta">🎨 ${item.Colour}</div>
                <div class="result-score">⭐ ${parseFloat(item.rerank_score).toFixed(2)}</div>
            </div>
        `;
        grid.appendChild(card);
    });

    container.appendChild(grid);
    addMessage(container, false);
}

function showProductDetail(item) {
    const detail = `
        <div style="background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0;">
            <h4 style="color: #8b5cf6;">${item.ProductTitle}</h4>
            <p><strong>Categoría:</strong> ${item.SubCategory}</p>
            <p><strong>Color:</strong> ${item.Colour}</p>
            <p><strong>Uso:</strong> ${item.Usage}</p>
            <p style="font-size: 0.9em; color: #64748b;">Puntaje de relevancia: ${item.rerank_score}</p>
        </div>
    `;
    addMessage(detail, false);
}