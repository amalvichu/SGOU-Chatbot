document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const messagesContainer = document.querySelector('.messages');
    
    let activeTab = 'education';
    
    // Tab switching functionality
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            activeTab = this.dataset.tab;
            // Clear messages when switching tabs
            messagesContainer.innerHTML = '';
        });
    });
    
    // Send message functionality
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

// Show character introduction when tab changes
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const tabName = this.dataset.tab;
        const character = tabCharacters[tabName];
        if (character) {
            addMessage('bot', character.intro);
        }
    });
});

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
                    responseText = 'Here\'s more information about our programs...';
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
    function addMessage(sender, text) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message-wrapper');
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        if (sender === 'bot') {
            const avatarContainer = document.createElement('div');
            avatarContainer.classList.add('avatar-container');
            
            const avatar = document.createElement('img');
            avatar.src = `/static/images/${activeTab}-character_logo.jpg`;
            avatar.classList.add('avatar', 'rounded');
            
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