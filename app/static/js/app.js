/**
 * Personal Library Tracker — Main Application JavaScript
 * ========================================================
 * Módulo principal de JavaScript vanilla que maneja:
 * - Toast notifications (éxito/error)
 * - Modal de confirmación para eliminación de libros
 * - Preview de Markdown en tiempo real (marked.js)
 * - Subida de archivos ePub vía AJAX
 * - Búsqueda y filtrado dinámico
 */

// =============================================================================
// Toast Notifications
// =============================================================================

/**
 * Muestra una notificación tipo toast en la esquina inferior derecha.
 * @param {string} message - Texto del mensaje.
 * @param {string} type    - Tipo: 'success' o 'error'.
 * @param {number} duration - Duración en ms antes de ocultarse (default 3000).
 */
function showToast(message, type = 'success', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Auto-remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}


// =============================================================================
// Delete Confirmation Modal
// =============================================================================

/**
 * Muestra un modal de confirmación antes de eliminar un libro.
 * @param {number} bookId    - ID del libro a eliminar.
 * @param {string} bookTitle - Título del libro (para mostrar en el modal).
 */
function confirmDelete(bookId, bookTitle) {
    // Crear overlay del modal
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'delete-modal';

    overlay.innerHTML = `
        <div class="modal-content">
            <h3 class="text-lg font-semibold text-slate-100 mb-2">
                ¿Eliminar este libro?
            </h3>
            <p class="text-slate-400 text-sm mb-6">
                Estás a punto de eliminar <strong class="text-slate-200">"${bookTitle}"</strong> 
                de tu biblioteca. Esta acción no se puede deshacer.
            </p>
            <div class="flex gap-3 justify-end">
                <button onclick="closeDeleteModal()"
                        class="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 bg-slate-600/50 hover:bg-slate-600 rounded-lg transition-all duration-200"
                        id="btn-cancel-delete">
                    Cancelar
                </button>
                <button onclick="executeDelete(${bookId})"
                        class="px-4 py-2 text-sm text-white bg-red-600 hover:bg-red-700 rounded-lg transition-all duration-200"
                        id="btn-confirm-delete">
                    Eliminar
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // Activar con delay para la animación CSS
    requestAnimationFrame(() => {
        overlay.classList.add('active');
    });

    // Cerrar con Escape
    document.addEventListener('keydown', handleEscapeClose);
}

/**
 * Cierra el modal de eliminación.
 */
function closeDeleteModal() {
    const modal = document.getElementById('delete-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 250);
    }
    document.removeEventListener('keydown', handleEscapeClose);
}

/**
 * Handler para cerrar modal con la tecla Escape.
 */
function handleEscapeClose(e) {
    if (e.key === 'Escape') closeDeleteModal();
}

/**
 * Ejecuta la eliminación del libro vía API.
 * @param {number} bookId - ID del libro a eliminar.
 */
async function executeDelete(bookId) {
    try {
        const response = await fetch(`/api/books/${bookId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showToast(data.message || 'Libro eliminado', 'success');
            closeDeleteModal();
            // Redirigir a la estantería después de un breve delay
            setTimeout(() => window.location.href = '/', 500);
        } else {
            showToast(data.error || 'Error al eliminar', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
        console.error('Delete error:', error);
    }
}


// =============================================================================
// ePub Upload Handler
// =============================================================================

/**
 * Maneja la subida de un archivo ePub vía AJAX.
 * Envía el archivo al endpoint /api/books/upload y, si es exitoso,
 * redirige al formulario de edición del libro recién creado.
 * @param {HTMLInputElement} fileInput - Input file con el ePub seleccionado.
 */
async function uploadEpub(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;

    // Validar extensión del lado del cliente
    if (!file.name.toLowerCase().endsWith('.epub')) {
        showToast('Solo se aceptan archivos .epub', 'error');
        return;
    }

    // Mostrar indicador de carga
    const uploadBtn = document.getElementById('btn-upload-epub');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Procesando...';
    }

    const formData = new FormData();
    formData.append('epub', file);

    try {
        const response = await fetch('/api/books/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showToast(data.message || 'ePub importado exitosamente', 'success');
            // Redirigir al formulario de edición para completar datos
            setTimeout(() => {
                window.location.href = `/books/${data.id}/edit`;
            }, 800);
        } else {
            showToast(data.error || 'Error al procesar el ePub', 'error');
        }
    } catch (error) {
        showToast('Error de conexión al subir el archivo', 'error');
        console.error('Upload error:', error);
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Subir ePub';
        }
    }
}


// =============================================================================
// Form Submission (Create / Update Book)
// =============================================================================

/**
 * Envía el formulario de creación o edición de un libro vía API.
 * @param {Event}  event   - Evento submit del formulario.
 * @param {number} bookId  - ID del libro (null para creación).
 */
async function submitBookForm(event, bookId = null) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    // Determinar si es creación o actualización
    const isUpdate = bookId !== null;
    const url = isUpdate ? `/api/books/${bookId}` : '/api/books';
    const method = isUpdate ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            // Al usar FormData como body, fetch configura automáticamente 
            // Content-Type a multipart/form-data con el boundary correcto
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message || 'Operación exitosa', 'success');
            const targetId = isUpdate ? bookId : result.id;
            setTimeout(() => {
                window.location.href = `/books/${targetId}`;
            }, 500);
        } else {
            showToast(result.error || 'Error en la operación', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
        console.error('Form submit error:', error);
    }
}


// =============================================================================
// Markdown Preview (Real-time)
// =============================================================================

/**
 * Inicializa la vista previa de Markdown en tiempo real.
 * Escucha cambios en el textarea de reseña y renderiza HTML
 * usando marked.js en el contenedor de preview.
 */
function initMarkdownPreview() {
    const textarea = document.getElementById('review-input');
    const preview = document.getElementById('review-preview');

    if (!textarea || !preview) return;

    // Configurar marked.js con opciones seguras
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,      // Convertir saltos de línea simples en <br>
            gfm: true,         // GitHub Flavored Markdown
            sanitize: false,   // Se confía en el contenido local (sistema privado)
        });
    }

    function updatePreview() {
        const markdown = textarea.value;
        if (markdown.trim() === '') {
            preview.innerHTML = '<p class="text-slate-500 italic">La vista previa aparecerá aquí...</p>';
        } else {
            preview.innerHTML = marked.parse(markdown);
        }
    }

    // Escuchar cambios con debounce de 150ms
    let debounceTimer;
    textarea.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(updatePreview, 150);
    });

    // Renderizar contenido inicial si existe
    updatePreview();
}


// =============================================================================
// Tab Switching (Editor/Preview para reseñas)
// =============================================================================

/**
 * Alterna entre las pestañas de edición y preview del editor Markdown.
 * @param {string} tab - 'editor' o 'preview'.
 */
function switchTab(tab) {
    const editorPane = document.getElementById('editor-pane');
    const previewPane = document.getElementById('preview-pane');
    const tabEditor = document.getElementById('tab-editor');
    const tabPreview = document.getElementById('tab-preview');

    if (!editorPane || !previewPane) return;

    if (tab === 'editor') {
        editorPane.classList.remove('hidden');
        previewPane.classList.add('hidden');
        tabEditor.classList.add('border-amber-400', 'text-amber-400');
        tabEditor.classList.remove('border-transparent', 'text-slate-400');
        tabPreview.classList.remove('border-amber-400', 'text-amber-400');
        tabPreview.classList.add('border-transparent', 'text-slate-400');
    } else {
        editorPane.classList.add('hidden');
        previewPane.classList.remove('hidden');
        tabPreview.classList.add('border-amber-400', 'text-amber-400');
        tabPreview.classList.remove('border-transparent', 'text-slate-400');
        tabEditor.classList.remove('border-amber-400', 'text-amber-400');
        tabEditor.classList.add('border-transparent', 'text-slate-400');

        // Forzar update del preview al cambiar de pestaña
        const textarea = document.getElementById('review-input');
        const preview = document.getElementById('review-preview');
        if (textarea && preview && typeof marked !== 'undefined') {
            const md = textarea.value.trim();
            preview.innerHTML = md ? marked.parse(md) : '<p class="text-slate-500 italic">La vista previa aparecerá aquí...</p>';
        }
    }
}


// =============================================================================
// Initialization
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Inicializar preview de Markdown si existe el textarea
    initMarkdownPreview();
});
