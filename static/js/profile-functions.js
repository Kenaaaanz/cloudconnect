function resetForm(form) {
    form.reset();
    showMessage('Form reset to original values', 'info');
}

function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    const colors = {
        'info': 'bg-blue-100 border-blue-400 text-blue-700',
        'success': 'bg-green-100 border-green-400 text-green-700', 
        'error': 'bg-red-100 border-red-400 text-red-700'
    };
    
    messageDiv.className = `${colors[type]} px-4 py-3 rounded-lg fixed top-4 right-4 z-50 transition-opacity duration-300`;
    messageDiv.innerHTML = message;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

function confirmDelete() {
    return confirm('Are you sure you want to delete your account? This action cannot be undone.');
}

// Auto-hide messages
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        const messages = document.querySelectorAll('[role="alert"]');
        messages.forEach(message => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        });
    }, 5000);
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Paystack functions from your template
function redirectToPaystack() {
    window.location.href = window.paystackSubscribeUrl || '/paystack/subscribe/';
}

function redirectToPaystackPlan(planId) {
    window.location.href = `/paystack/subscribe/${planId}/`;
}

async function initiatePaystackPayment(planId) {
    try {
        const response = await fetch(`/paystack/initiate-payment/${planId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            window.location.href = data.payment_url;
        } else {
            showMessage('Failed to initiate payment: ' + data.message, 'error');
        }
    } catch (error) {
        showMessage('Error initiating payment: ' + error, 'error');
    }
}

// Session revocation
function revokeSession(sessionId) {
    if (confirm('Are you sure you want to revoke this session?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/accounts/profile/sessions/revoke/${sessionId}/`;
        
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        form.appendChild(csrfInput);
        document.body.appendChild(form);
        form.submit();
    }
}

// 2FA toggle
function toggle2FA(enable) {
    const url = enable ? window.enable2faUrl : window.disable2faUrl;
    const message = enable ? 
        'Are you sure you want to enable two-factor authentication?' :
        'Are you sure you want to disable two-factor authentication? This will reduce your account security.';
    
    if (confirm(message)) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            showMessage(data.message, data.status);
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        })
        .catch(error => {
            showMessage('Error updating 2FA settings: ' + error, 'error');
        });
    }
}