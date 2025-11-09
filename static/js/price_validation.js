/**
 * Validaciones para campos de precio y cantidad
 * Evita valores nulos, negativos o cero en precios y cantidades
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Función para validar precios
    function validatePrice(input, fieldName = 'precio') {
        // Limpiar valor formateado antes de validar
        let cleanValue = input.value;
        if (typeof cleanValue === 'string') {
            // Remover puntos separadores de miles y convertir coma decimal a punto
            cleanValue = cleanValue.replace(/\./g, '').replace(',', '.');
        }
        
        const value = parseFloat(cleanValue);
        const errorContainer = input.parentElement.querySelector('.price-error') || 
                             createErrorContainer(input);
        
        // Limpiar errores previos
        errorContainer.textContent = '';
        input.classList.remove('is-invalid');
        
        if (isNaN(value) && cleanValue !== '' && cleanValue !== null) {
            showError(input, errorContainer, `El ${fieldName} debe ser un número válido.`);
            return false;
        }
        
        // Permitir campos vacíos (se interpretan como 0)
        if (cleanValue === '' || cleanValue === null) {
            input.classList.add('is-valid');
            return true;
        }
        
        if (value < 0) {
            showError(input, errorContainer, `El ${fieldName} no puede ser negativa.`);
            return false;
        }
        
        input.classList.add('is-valid');
        return true;
    }
    
    // Función para crear contenedor de errores
    function createErrorContainer(input) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'price-error text-danger small mt-1';
        input.parentElement.appendChild(errorDiv);
        return errorDiv;
    }
    
    // Función para mostrar errores
    function showError(input, errorContainer, message) {
        input.classList.add('is-invalid');
        errorContainer.textContent = message;
    }
    
    // Validar campos de precio en tiempo real
    const priceFields = document.querySelectorAll('input[name*="price"], input[name*="precio"], input[name*="cost"], input[name*="costo"]');
    
    priceFields.forEach(function(field) {
        // Validar al perder el foco
        field.addEventListener('blur', function() {
            const fieldLabel = this.getAttribute('data-field-name') || 
                              this.previousElementSibling?.textContent?.replace(':', '') || 
                              'precio';
            validatePrice(this, fieldLabel.toLowerCase());
        });
        
        // Validar mientras se escribe (con debounce)
        let timeout;
        field.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const fieldLabel = this.getAttribute('data-field-name') || 
                                  this.previousElementSibling?.textContent?.replace(':', '') || 
                                  'precio';
                validatePrice(this, fieldLabel.toLowerCase());
            }, 500);
        });
        
        // Prevenir valores negativos
        field.addEventListener('keydown', function(e) {
            // Permitir: backspace, delete, tab, escape, enter
            if ([46, 8, 9, 27, 13].indexOf(e.keyCode) !== -1 ||
                // Permitir Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
                (e.keyCode === 65 && e.ctrlKey === true) ||
                (e.keyCode === 67 && e.ctrlKey === true) ||
                (e.keyCode === 86 && e.ctrlKey === true) ||
                (e.keyCode === 88 && e.ctrlKey === true) ||
                // Permitir home, end, left, right
                (e.keyCode >= 35 && e.keyCode <= 39)) {
                return;
            }
            
            // Evitar el signo menos
            if (e.keyCode === 189 || e.keyCode === 109) {
                e.preventDefault();
            }
        });
    });
    
    // Validar campos de cantidad
    const quantityFields = document.querySelectorAll('input[name*="quantity"], input[name*="cantidad"], input[name*="qty"]');
    
    quantityFields.forEach(function(field) {
        field.addEventListener('blur', function() {
            validatePrice(this, 'cantidad');
        });
        
        let timeout;
        field.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                validatePrice(this, 'cantidad');
            }, 500);
        });
    });
    
    // Validar formularios antes del envío
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            let hasErrors = false;
            
            // PRIMERO: Limpiar formato de todos los campos numéricos antes de validar y enviar
            const numericFieldsInForm = form.querySelectorAll('input[type="number"], input[inputmode="numeric"], input[name*="price"], input[name*="precio"], input[name*="cost"], input[name*="costo"]');
            
            numericFieldsInForm.forEach(function(field) {
                if (field.value) {
                    // Remover puntos separadores de miles y dejar solo números y punto decimal
                    let cleanValue = field.value.replace(/\./g, '').replace(',', '.');
                    // Si tiene más de un punto, mantener solo el último como decimal
                    const parts = cleanValue.split('.');
                    if (parts.length > 2) {
                        cleanValue = parts.slice(0, -1).join('') + '.' + parts[parts.length - 1];
                    }
                    field.value = cleanValue;
                }
            });
            
            // SEGUNDO: Validar todos los campos de precio y cantidad
            const fieldsToValidate = form.querySelectorAll('input[name*="price"], input[name*="precio"], input[name*="cost"], input[name*="costo"], input[name*="quantity"], input[name*="cantidad"]');
            
            fieldsToValidate.forEach(function(field) {
                const fieldLabel = field.getAttribute('data-field-name') || 
                                  field.previousElementSibling?.textContent?.replace(':', '') || 
                                  'valor';
                
                if (!validatePrice(field, fieldLabel.toLowerCase())) {
                    hasErrors = true;
                }
            });
            
            if (hasErrors) {
                e.preventDefault();
                
                // Mostrar alerta general
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
                alertDiv.innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Error:</strong> Por favor corrige los errores en los campos marcados. 
                    Los precios y cantidades no pueden ser negativos.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                
                // Insertar alerta al inicio del formulario
                form.insertBefore(alertDiv, form.firstChild);
                
                // Scroll al primer error
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });
    });
    
    // Formatear números SOLO en campos específicos de visualización (no en campos de formulario)
    const displayFields = document.querySelectorAll('.format-currency');
    
    displayFields.forEach(function(field) {
        field.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value) && value > 0) {
                this.value = value.toLocaleString('es-CO', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2
                });
            }
        });
        
        field.addEventListener('focus', function() {
            // Remover formato para edición
            const value = this.value.replace(/[^\d.,]/g, '').replace(',', '.');
            this.value = value;
        });
    });
});

// Función global para validar un campo específico
function validatePriceField(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        const event = new Event('blur');
        field.dispatchEvent(event);
    }
}

// Función global para limpiar errores de un formulario
function clearPriceErrors(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const errorContainers = form.querySelectorAll('.price-error');
        const invalidFields = form.querySelectorAll('.is-invalid');
        
        errorContainers.forEach(container => container.textContent = '');
        invalidFields.forEach(field => {
            field.classList.remove('is-invalid');
            field.classList.remove('is-valid');
        });
    }
}