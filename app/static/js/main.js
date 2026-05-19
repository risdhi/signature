// Main JavaScript for Signature Verification System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeAlerts();
    initializeTooltips();
});

/**
 * Initialize alert close functionality
 */
function initializeAlerts() {
    const closeButtons = document.querySelectorAll('.alert-close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.closest('.alert');
            alert.style.animation = 'slideUp 0.3s ease';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        });
    });

    // Auto-close alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.alert-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const tooltip = event.target.getAttribute('data-tooltip');
    const tooltipEl = document.createElement('div');
    tooltipEl.className = 'tooltip';
    tooltipEl.textContent = tooltip;
    document.body.appendChild(tooltipEl);

    const rect = event.target.getBoundingClientRect();
    tooltipEl.style.top = (rect.top - tooltipEl.offsetHeight - 10) + 'px';
    tooltipEl.style.left = (rect.left + rect.width / 2 - tooltipEl.offsetWidth / 2) + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Show loading spinner
 */
function showLoading(element = null) {
    if (element) {
        element.innerHTML = '<span class="loading"></span>';
    }
    document.body.style.opacity = '0.6';
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    document.body.style.opacity = '1';
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        ${message}
        <button class="alert-close">&times;</button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(notification, container.firstChild);

    const closeBtn = notification.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
        notification.remove();
    });

    setTimeout(() => {
        notification.remove();
    }, duration);
}

/**
 * Validate form
 */
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#dc3545';
            isValid = false;
        } else {
            input.style.borderColor = '';
        }

        input.addEventListener('input', function() {
            if (this.value.trim()) {
                this.style.borderColor = '';
            }
        });
    });

    return isValid;
}

/**
 * API helper function
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(endpoint, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'API call failed');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Add animation styles
 */
const style = document.createElement('style');
style.innerHTML = `
    @keyframes slideUp {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }

    .tooltip {
        position: fixed;
        background-color: #333;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        z-index: 1000;
        white-space: nowrap;
        pointer-events: none;
        animation: slideDown 0.3s ease;
    }

    .tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 5px solid transparent;
        border-top-color: #333;
    }
`;
document.head.appendChild(style);
