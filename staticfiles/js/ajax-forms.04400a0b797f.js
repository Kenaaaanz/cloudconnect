// Handle preference updates from your template
function updatePreferences(formElement = null) {
    const formData = new FormData();
    
    // Get preferences data exactly as in your template
    const language = document.querySelector('[name="language"]')?.value;
    const timezone = document.querySelector('[name="timezone"]')?.value;
    const dateFormat = document.querySelector('[name="date_format"]')?.value;
    const darkMode = document.querySelector('[name="dark_mode"]')?.checked;
    
    if (language) formData.append('language', language);
    if (timezone) formData.append('timezone', timezone);
    if (dateFormat) formData.append('date_format', dateFormat);
    if (darkMode !== undefined) formData.append('dark_mode', darkMode);
    
    // Notification preferences
    formData.append('email_notifications', document.querySelector('[name="email_notifications"]')?.checked || false);
    formData.append('sms_notifications', document.querySelector('[name="sms_notifications"]')?.checked || false);
    formData.append('billing_reminders', document.querySelector('[name="billing_reminders"]')?.checked || false);
    formData.append('service_updates', document.querySelector('[name="service_updates"]')?.checked || false);
    formData.append('promotional_offers', document.querySelector('[name="promotional_offers"]')?.checked || false);
    
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    const saveButton = document.querySelector('#save-preferences-btn');
    if (saveButton) {
        const originalText = saveButton.innerHTML;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Saving...';
        saveButton.disabled = true;
    }
    
    fetch(window.updatePreferencesUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (saveButton) {
            saveButton.innerHTML = originalText;
            saveButton.disabled = false;
        }
        showMessage(data.message, data.status);
    })
    .catch(error => {
        if (saveButton) {
            saveButton.innerHTML = originalText;
            saveButton.disabled = false;
        }
        showMessage('Error updating preferences: ' + error, 'error');
    });
}

// Billing address update
function updateBillingAddress(formElement = null) {
    const formData = new FormData();
    
    const address = document.querySelector('[name="address"]')?.value || '';
    const city = document.querySelector('[name="city"]')?.value || '';
    const state = document.querySelector('[name="state"]')?.value || '';
    const zipCode = document.querySelector('[name="zip_code"]')?.value || '';
    const country = document.querySelector('[name="country"]')?.value || '';
    
    if (address) formData.append('address', address);
    if (city) formData.append('city', city);
    if (state) formData.append('state', state);
    if (zipCode) formData.append('zip_code', zipCode);
    if (country) formData.append('country', country);
    
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    const updateButton = document.querySelector('#update-billing-address-btn');
    if (updateButton) {
        const originalText = updateButton.innerHTML;
        updateButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Updating...';
        updateButton.disabled = true;
    }
    
    fetch(window.updateBillingAddressUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (updateButton) {
            updateButton.innerHTML = originalText;
            updateButton.disabled = false;
        }
        showMessage(data.message, data.status);
        if (data.status === 'success' && data.billing_address) {
            document.getElementById('billing-address-display').innerHTML = 
                data.billing_address.replace(/\n/g, '<br>');
        }
    })
    .catch(error => {
        if (updateButton) {
            updateButton.innerHTML = originalText;
            updateButton.disabled = false;
        }
        showMessage('Error updating billing address: ' + error, 'error');
    });
}

// Real-time preference updates
document.addEventListener('DOMContentLoaded', function() {
    const toggleSwitches = document.querySelectorAll('.toggle-switch input[type="checkbox"]');
    toggleSwitches.forEach(switchElement => {
        switchElement.addEventListener('change', function() {
            clearTimeout(window.preferenceUpdateTimeout);
            window.preferenceUpdateTimeout = setTimeout(() => {
                updatePreferences();
            }, 500);
        });
    });
    
    const dropdowns = document.querySelectorAll('select[name="language"], select[name="timezone"], select[name="date_format"]');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('change', function() {
            clearTimeout(window.preferenceUpdateTimeout);
            window.preferenceUpdateTimeout = setTimeout(() => {
                updatePreferences();
            }, 500);
        });
    });
});