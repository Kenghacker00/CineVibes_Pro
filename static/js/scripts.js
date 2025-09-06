document.addEventListener("DOMContentLoaded", function() {
    // Funciones de utilidad
    function handleFetchError(error) {
        console.error('Error:', error); // Muestra el error en la consola
    }

    function updateMessage(message) {
        document.getElementById('message').innerText = message; // Actualiza el mensaje en la interfaz
    }

    // Manejo del formulario de registro
    function handleRegisterForm() {
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', function(event) {
                event.preventDefault(); // Previene el comportamiento por defecto del formulario
                const nickname = document.getElementById('nickname').value;
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                // Envío de datos al servidor
                fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nickname, email, password })
                })
                .then(response => response.json())
                .then(data => updateMessage(data.message)) // Actualiza el mensaje con la respuesta del servidor
                .catch(handleFetchError); // Maneja errores de la solicitud
            });
        }
    }

    // Manejo del formulario de inicio de sesión
    function handleLoginForm() {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', function(event) {
                event.preventDefault(); // Previene el comportamiento por defecto del formulario
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;

                // Envío de datos al servidor
                fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                })
                .then(response => response.json())
                .then(data => {
                    updateMessage(data.message); // Actualiza el mensaje con la respuesta del servidor
                    if (data.success) {
                        window.location.href = '/profile'; // Redirige al perfil si el inicio de sesión es exitoso
                    }
                })
                .catch(handleFetchError); // Maneja errores de la solicitud
            });
        }
    }

    // Detección de bloqueador de anuncios
    function setupAdBlockDetection() {
        function adBlockDetected() {
            console.log("Bloqueador de anuncios detectado"); // Mensaje en consola si se detecta un bloqueador
            // Lógica adicional si se detecta un bloqueador de anuncios
        }

        function adBlockNotDetected() {
            console.log("No se detectó bloqueador de anuncios"); // Mensaje en consola si no se detecta un bloqueador
            // Lógica adicional si no se detecta un bloqueador de anuncios
        }

        // Verifica si el bloqueador de anuncios está presente
        if (typeof fuckAdBlock === 'undefined') {
            adBlockDetected();
        } else {
            fuckAdBlock.onDetected(adBlockDetected);
            fuckAdBlock.onNotDetected(adBlockNotDetected);
        }
    }

    // Manejo de la carga de imagen de perfil
    function handleProfileImageUpload() {
        const profilePicInput = document.getElementById('profile_pic');
        if (profilePicInput) {
            profilePicInput.onchange = function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        document.querySelector('.profile-image').src = e.target.result; // Muestra la imagen seleccionada
                    };
                    reader.readAsDataURL(this.files[0]);

                    // Mostrar indicador de carga
                    document.querySelector('.profile-image').style.opacity = '0.5';
                    document.querySelector('.profile-card').insertAdjacentHTML('beforeend', '<div id="loading">Subiendo...</div>');

                    // Enviar el formulario
                    this.form.submit();
                }
            };
        }
    }

    // Validación de formularios
    function setupFormValidation() {
        'use strict';
        var forms = document.querySelectorAll('.needs-validation');
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault(); // Previene el envío si el formulario no es válido
                    event.stopPropagation(); // Detiene la propag ación del evento
                }
                form.classList.add('was-validated'); // Añade clase para mostrar validación
            }, false);
        });
    }

    // Inicialización de funciones
    handleRegisterForm();
    handleLoginForm();
    setupAdBlockDetection();
    handleProfileImageUpload();
    setupFormValidation();
});

// Función autoejecutable para validación de formularios
(function () {
    'use strict';
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault(); // Previene el envío si el formulario no es válido
                event.stopPropagation(); // Detiene la propagación del evento
            }
            form.classList.add('was-validated'); // Añade clase para mostrar validación
        }, false);
    });
})();
