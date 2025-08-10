document.addEventListener('DOMContentLoaded', function () {
    // Handle login/register form validation
    const forms = document.querySelectorAll('.auth-card form');

    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const password = this.querySelector('input[type="password"]');

            if (password && password.value.length < 6) {
                e.preventDefault();
                alert('Password must be at least 6 characters long');
            }
        });
    });

    // Toggle password visibility
    const togglePassword = document.querySelectorAll('.toggle-password');
    togglePassword.forEach(button => {
        button.addEventListener('click', function () {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.querySelector('i').classList.toggle('fa-eye');
            this.querySelector('i').classList.toggle('fa-eye-slash');
        });
    });
});