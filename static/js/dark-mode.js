document.addEventListener('DOMContentLoaded', function () {
    // FIX: The ID in the HTML is 'dark-mode-switch', not 'dark-mode-toggle'
    const darkModeSwitch = document.getElementById('dark-mode-switch');
    const body = document.body;

    if (darkModeSwitch) {
        darkModeSwitch.addEventListener('change', function () {
            // Toggle the theme immediately for instant UI feedback
            body.dataset.theme = this.checked ? 'dark' : 'light';

            // Send the change to the server to save the preference
            fetch('/toggle-dark-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Dark mode preference saved.');
                    } else {
                        console.error('Failed to save dark mode preference.');
                        // Revert the switch if the save fails to keep UI consistent
                        body.dataset.theme = !this.checked ? 'dark' : 'light';
                        this.checked = !this.checked;
                    }
                }).catch(error => console.error('Error:', error));
        });
    }
});