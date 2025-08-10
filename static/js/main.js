// Main JavaScript for the application
document.addEventListener('DOMContentLoaded', function () {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle form submissions with fetch API
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', async function (e) {
            if (this.dataset.ajax === 'true') {
                e.preventDefault();

                const formData = new FormData(this);
                const action = this.getAttribute('action');
                const method = this.getAttribute('method');

                try {
                    const response = await fetch(action, {
                        method: method,
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        if (result.redirect) {
                            window.location.href = result.redirect;
                        } else {
                            // Handle success (e.g., show message, update UI)
                            showFlashMessage(result.message || 'Action completed successfully', 'success');
                        }
                    } else {
                        showFlashMessage(result.error || 'An error occurred', 'error');
                    }
                } catch (error) {
                    showFlashMessage('Network error: ' + error.message, 'error');
                }
            }
        });
    });

    // Flash message function
    window.showFlashMessage = function (message, type) {
        const flashContainer = document.createElement('div');
        flashContainer.className = `flash-message ${type}`;
        flashContainer.textContent = message;

        document.body.appendChild(flashContainer);

        setTimeout(() => {
            flashContainer.classList.add('fade-out');
            setTimeout(() => flashContainer.remove(), 500);
        }, 5000);
    };
});

// Helper function to format dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}


// Add this to the end of your main.js file

document.addEventListener('DOMContentLoaded', function () {
    // Find the container for flash messages
    const flashContainer = document.querySelector('.flash-container');

    if (flashContainer) {
        // Listen for clicks inside the container
        flashContainer.addEventListener('click', function (event) {
            // Check if a close button was clicked
            if (event.target.classList.contains('flash-close')) {
                // Find the parent message and remove it
                const flashMessage = event.target.closest('.flash-message');
                if (flashMessage) {
                    flashMessage.remove();
                }
            }
        });
    }
});

// Add this to the end of your main.js file
document.addEventListener('DOMContentLoaded', function () {
    const chatButton = document.getElementById('ai-chat-button');
    const chatModal = document.getElementById('ai-chat-modal');
    const closeChatBtn = document.getElementById('ai-chat-close');
    const chatForm = document.getElementById('ai-chat-form');
    const chatInput = document.getElementById('ai-chat-input');
    const messagesContainer = document.getElementById('ai-chat-messages');

    // Show/Hide Chat Modal
    chatButton.addEventListener('click', () => {
        chatModal.style.display = 'flex';
    });
    closeChatBtn.addEventListener('click', () => {
        chatModal.style.display = 'none';
    });
    chatModal.addEventListener('click', (e) => {
        if (e.target === chatModal) {
            chatModal.style.display = 'none';
        }
    });

    // Handle sending a message
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = chatInput.value.trim();
        if (!prompt) return;

        // Display user's message immediately
        addMessage(prompt, 'user');
        chatInput.value = '';

        // Show typing indicator
        addMessage('...', 'assistant', true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });
            const data = await response.json();

            // Remove typing indicator and show AI response
            document.querySelector('.typing-indicator').remove();
            addMessage(data.reply, 'assistant');

        } catch (error) {
            document.querySelector('.typing-indicator').remove();
            addMessage('Error connecting to the assistant.', 'assistant');
            console.error('Chat error:', error);
        }
    });

    function addMessage(text, role, isTyping = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-chat-message ${role}`;

        if (isTyping) {
            messageDiv.classList.add('typing-indicator');
            messageDiv.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
        } else {
            // FIX: Use .innerHTML instead of .textContent
            // This will render the bold text, lists, and paragraphs correctly.
            messageDiv.innerHTML = text;
        }

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});