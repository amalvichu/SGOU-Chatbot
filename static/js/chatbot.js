// Character configurations for each tab
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

// Global variables for DOM elements
let activeTab = 'programs';
let messagesContainer;
let messageInput;
let sendButton;
let tabs;

// Initialize the chat interface
function initializeChat() {
    // Get DOM elements
    messagesContainer = document.querySelector('.messages');
    messageInput = document.querySelector('.message-input');
    sendButton = document.querySelector('.send-button');
    tabs = document.querySelectorAll('.tab');

    // Set up initial active tab and display welcome message
    const activeTabElement = document.querySelector('.tab.active');
    if (activeTabElement) {
        activeTab = activeTabElement.dataset.tab;
        displayWelcomeMessage(activeTab);
    }

    // Set up event listeners
    setupEventListeners();
}

// Display welcome message for the current tab
function displayWelcomeMessage(tabId) {
    const character = tabCharacters[tabId];
    if (character) {
        addMessage('bot', character.intro);
    }
}

// Set up all event listeners
function setupEventListeners() {
    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => handleTabSwitch(tab));
    });

    // Message sending
    sendButton.addEventListener('click', handleMessageSend);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleMessageSend();
        }
    });
}

// Handle tab switching
function handleTabSwitch(tab) {
    // Update active tab styling
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    // Update active tab and clear messages
    activeTab = tab.dataset.tab;
    messagesContainer.innerHTML = '';

    // Display welcome message for new tab
    displayWelcomeMessage(activeTab);
}

// Handle sending messages
function handleMessageSend() {
    const message = messageInput.value.trim();
    if (message) {
        // Add user message
        addMessage('user', message);
        messageInput.value = '';

        // Simulate bot response after a short delay
        setTimeout(() => {
            generateBotResponse(message);
        }, 500);
    }
}

// Add a message to the chat
function addMessage(type, text) {
    const messageWrapper = document.createElement('div');
    messageWrapper.className = 'message-wrapper';

    // Create avatar container and image only for bot messages
    if (type === 'bot') {
        const avatarContainer = document.createElement('div');
        avatarContainer.className = 'avatar-container';
        
        const avatar = document.createElement('img');
        avatar.className = 'avatar rounded';
        avatar.src = document.getElementById(`${activeTab}-avatar`).src;
        avatar.alt = tabCharacters[activeTab].name;
        
        avatarContainer.appendChild(avatar);
        messageWrapper.appendChild(avatarContainer);
    }

    // Create message content
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    messageWrapper.appendChild(message);
    messagesContainer.appendChild(messageWrapper);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Generate bot response based on user input and active tab
function generateBotResponse(userMessage) {
    const responses = {
        'programs': [
            'We offer various educational programs including Bachelor\'s, Master\'s, and Certificate programs.',
            'Our most popular programs are in Business, Technology, and Healthcare.',
            'Would you like to know more about a specific program?'
        ],
        'certification': [
            'We provide industry-recognized certifications in multiple fields.',
            'Popular certifications include Project Management, IT Security, and Business Analytics.',
            'Which certification interests you?'
        ],
        'centers': [
            'We have learning centers located across multiple cities.',
            'Each center is equipped with modern facilities and expert instructors.',
            'Would you like to know about a specific center?'
        ],
        'learning-center': [
            'Our learning center provides various resources including online libraries, study materials, and tutorials.',
            'We also offer virtual labs and interactive learning tools.',
            'What specific resources are you looking for?'
        ]
    };

    // Get random response for the active tab
    const tabResponses = responses[activeTab];
    const randomResponse = tabResponses[Math.floor(Math.random() * tabResponses.length)];
    addMessage('bot', randomResponse);
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeChat);