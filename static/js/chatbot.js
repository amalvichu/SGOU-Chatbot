// Character introductions for each tab
const tabCharacters = {
    'programs': {
        name: 'Program Pro',
        intro: 'Hello! I\'m Program Pro, your guide to all our educational programs. How can I assist you today?'
    },
    'certification': {
        name: 'Cert Expert',
        intro: 'Hi there! I\'m Cert Expert, here to help with all certification questions. What would you like to know?'
    },
    'centers': {
        name: 'Center Guide',
        intro: 'Greetings! I\'m Center Guide, ready to provide information about our centers. How can I help?'
    },
    'learning-center': {
        name: 'Learning Buddy',
        intro: 'Welcome! I\'m Learning Buddy, your partner in educational resources. What would you like to explore?'
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const messagesContainer = document.querySelector('.messages');
    
    let activeTab = 'programs';
    
    // Set Programs tab as active and show intro on page load
    const programsTab = document.querySelector('[data-tab="programs"]');
    if (programsTab) {
        programsTab.classList.add('active');
        const character = tabCharacters['programs'];
        if (character) {
            addMessage('bot', character.intro);
        }
    }
    
    // Tab switching functionality
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            activeTab = this.dataset.tab;
            // Clear messages when switching tabs
            messagesContainer.innerHTML = '';
            // Show character introduction for the new tab
            const character = tabCharacters[activeTab];
            if (character) {
                addMessage('bot', character.intro);
            }
        });
    });
    
    // Send message functionality


function sendMessage() {
    const messageText = messageInput.value.trim();
    if (messageText) {
        // Add user message
        addMessage('user', messageText);
        messageInput.value = '';
        
        // Simulate bot response based on active tab
        setTimeout(() => {
            let responseText = '';
            switch(activeTab) {
                case 'programs':
                    // Call SGOU API to get program information
                    fetch('http://192.168.20.11:8000/api/programmes', {
                        method: 'GET',
                        headers: {
                            'X-API-KEY': '$2y$10$M0JLrgVmX2AUUqMZkrqaKOrgaMMaVFusOVjiXkVjc1YLyqcYFY9Bi'
                        }
                    })
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Unauthorized or failed request');
                            }
                            return response.json();
                        })
                        .then(data => {
                            responseText = formatProgramResponse(data, messageText);
                            addMessage('bot', responseText);
                        })
                        .catch(error => {
                            console.error('Error fetching programs:', error);
                            responseText = 'Sorry, I couldn\'t retrieve program information at this time.';
                            addMessage('bot', responseText);
                        });
                    break;
                case 'certification':
                    responseText = 'Let me tell you about our certification process...';
                    break;
                case 'centers':
                    responseText = 'Here are details about our centers...';
                    break;
                case 'learning-center':
                    responseText = 'Here\'s what our learning center offers...';
                    break;
            }
            addMessage('bot', responseText);
        }, 500);
    }
}
    
    // Add message to chat
    function formatProgramResponse(data, query) {
    // Format API response based on user query
    if (data.programme && data.programme.length > 0) {
        let response = 'Here are our available programs:\n';
        data.programme.forEach(programme => {
            response += `- ${programme.name || 'Unnamed program'}\n`;
        });
        return response;
    }
    return 'No programs found matching your query.';
}

function addMessage(sender, text) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message-wrapper');
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        if (sender === 'bot') {
            const avatarContainer = document.createElement('div');
            avatarContainer.classList.add('avatar-container');
            
            const avatar = document.getElementById(`${activeTab}-avatar`).cloneNode(true);
            avatarContainer.appendChild(avatar);
            messageWrapper.appendChild(avatarContainer);
        }
        
        const textNode = document.createElement('span');
        textNode.textContent = text;
        messageDiv.appendChild(textNode);
        
        messageWrapper.appendChild(messageDiv);
        messagesContainer.appendChild(messageWrapper);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});