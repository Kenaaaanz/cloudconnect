// Profile page specific functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeProfilePage();
});

function initializeProfilePage() {
    setupProfileTabs();
    setupPasswordToggle();
    setupBillingAddressUpdate();
}

function setupProfileTabs() {
    const tabButtons = document.querySelectorAll('[data-tab]');
    const tabPanes = document.querySelectorAll('[data-tab-pane]');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Show target tab pane
            tabPanes.forEach(pane => {
                if (pane.getAttribute('data-tab-pane') === targetTab) {
                    pane.classList.remove('hidden');
                } else {
                    pane.classList.add('hidden');
                }
            });
            
            // Update URL hash
            window.location.hash = targetTab;
        });
    });
    
    // Activate tab from URL hash
    const hash = window.location.hash.substring(1);
    if (hash) {
        const targetButton = document.querySelector(`[data-tab="${hash}"]`);
        if (targetButton) {
            targetButton.click();
        }
    }
}

function setupPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    });
}

function setupBillingAddressUpdate() {
    const updateButton = document.getElementById('update-billing-address-btn');
    if (updateButton) {
        updateButton.addEventListener('click', updateBillingAddress);
    }
}

async function updateBillingAddress() {
    const button = document.getElementById('update-billing-address-btn');
    const originalText = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    button.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('address', document.querySelector('[name="address"]').value);
        formData.append('city', document.querySelector('[name="city"]').value);
        formData.append('state', document.querySelector('[name="state"]').value);
        formData.append('zip_code', document.querySelector('[name="zip_code"]').value);
        formData.append('country', document.querySelector('[name="country"]').value);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        const response = await fetch('/accounts/update-billing-address/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        });
        
        const data = await response.json();
        
        CloudConnect.showNotification(data.message, data.status);
        
        if (data.status === 'success' && data.billing_address) {
            document.getElementById('billing-address-display').innerHTML = 
                data.billing_address.replace(/\n/g, '<br>');
        }
    } catch (error) {
        CloudConnect.showNotification('Error updating billing address', 'error');
        console.error('Billing address update error:', error);
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}