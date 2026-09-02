/**
 * stegaNSS Core UI Logic
 * High-fidelity interactions and utility functions
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("stegaNSS System Online");
    initGlobalInteractions();
    initThemeManager();
});

function initThemeManager() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    const icon = themeToggle.querySelector('i');
    
    // Check for saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark-theme';
    applyTheme(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.className;
        const newTheme = currentTheme === 'dark-theme' ? 'light-theme' : 'dark-theme';
        applyTheme(newTheme);
    });

    function applyTheme(theme) {
        document.documentElement.className = theme;
        document.body.className = theme;
        localStorage.setItem('theme', theme);
        
        // Update icon
        if (theme === 'dark-theme') {
            icon.className = 'fas fa-sun';
            themeToggle.title = 'Switch to Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            themeToggle.title = 'Switch to Dark Mode';
        }
    }
}

function initGlobalInteractions() {
    // Reveal animations on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.glass, .feature-card, .activity-log tr').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Toast Notification System
 * @param {string} message 
 * @param {string} type - 'success' | 'error' | 'info'
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-triangle' : 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.4s cubic-bezier(0.2, 1, 0.3, 1) forwards';
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

/**
 * Animate a numeric value
 */
function animateValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    if (!obj) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/**
 * Initialize Drag and Drop for file inputs
 */
function initDragAndDrop(dropzoneId, inputId, fileNameId) {
    const dropzone = document.getElementById(dropzoneId);
    const input = document.getElementById(inputId);
    const fileName = document.getElementById(fileNameId);

    if (!dropzone || !input) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.add('drag-active');
            dropzone.style.borderColor = 'var(--accent-color)';
            dropzone.style.background = 'rgba(16, 185, 129, 0.1)';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.classList.remove('drag-active');
            dropzone.style.borderColor = 'var(--glass-border)';
            dropzone.style.background = 'rgba(0,0,0,0.2)';
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        input.files = files;
        
        // Trigger the change event manually
        const event = new Event('change');
        input.dispatchEvent(event);
    }, false);
}

// System Health Radar Animation (SVG Helper)
function initRadar(svgId) {
    const svg = document.getElementById(svgId);
    if (!svg) return;
    
    // Add pulsing circles or scanning lines via JS if needed
    // Most is handled in CSS, but this keeps it extensible
}