
// Function to fetch programs directly from your API
function fetchPrograms() {
    const apiUrl = 'http://192.168.20.2:8000/api/programmes';
    const apiKey = '$2y$10$M0JLrgVmX2AUUqMZkrqaKOrgaMMaVFusOVjiXkVjc1YLyqcYFY9Bi';
    
    return fetch(apiUrl, {
        headers: {
            'X-API-KEY': apiKey
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Unauthorized - Please check API credentials');
            } else if (response.status === 404) {
                throw new Error('API endpoint not found');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (!data || !data.programme || !Array.isArray(data.programme)) {
            throw new Error('Invalid program data format received');
        }
        return data.programme;
    })
    .catch(error => {
        console.error('Error fetching programs:', error);
        throw error;
    });
}

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
    console.log("DOM fully loaded");
    const tabs = document.querySelectorAll('.tab');
    const messageInput = document.querySelector('.message-input');
    const sendButton = document.querySelector('.send-button');
    const messagesContainer = document.querySelector('.messages');
    
    // Debug element presence
    console.log("Message input found:", !!messageInput);
    console.log("Send button found:", !!sendButton);
    console.log("Messages container found:", !!messagesContainer);
    
    let activeTab = 'programs';
    
    // Set Programs tab as active and show intro on page load
    const programsTab = document.querySelector('[data-tab="programs"]');
    if (programsTab) {
        programsTab.classList.add('active');
        const character = tabCharacters['programs'];
        if (character) {
            setTimeout(() => {
                addMessage('bot', character.intro);
            }, 300); // Small delay to ensure DOM is ready
        }
    }
    
    // Store chat history for each tab
    const chatHistory = {};
    
    // Tab switching functionality
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            console.log("Tab clicked:", this.dataset.tab);
            
            // Save current tab's messages before switching
            if (messagesContainer.innerHTML.trim() !== '') {
                chatHistory[activeTab] = messagesContainer.innerHTML;
            }
            
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            activeTab = this.dataset.tab;
            
            // Clear and restore messages for the new tab
            messagesContainer.innerHTML = '';
            
            // Restore messages if they exist, otherwise show intro
            if (chatHistory[activeTab]) {
                messagesContainer.innerHTML = chatHistory[activeTab];
                // Scroll to bottom
                setTimeout(() => {
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }, 100);
            } else {
                // Show character introduction for the new tab
                const character = tabCharacters[activeTab];
                if (character) {
                    addMessage('bot', character.intro);
                }
            }
        });
    });
    
    // Function to format program list
    function formatProgramList(text) {
        // Check if this is the programs list
        if (text.includes("Here are our current programs:")) {
            try {
                // Split the text to separate the intro from the list
                const parts = text.split("Here are our current programs:");
                const intro = parts[0] + "Here are our current programs:";
                
                // Get the programs part and split by bullet points
                let programsList = parts[1].trim();
                const programs = programsList.split("• ").filter(item => item.trim() !== "");
                
                // Create formatted HTML with numbering and proper alignment
                let formattedHTML = intro + "<div class='program-list'>";
                
                programs.forEach((program, index) => {
                    const number = index + 1;
                    // Add CSS for proper alignment using a table-like structure
                    formattedHTML += `<div class="program-item" style="display: flex;">
                        <div style="min-width: 40px; text-align: right; margin-right: 10px;"><strong>${number}.</strong></div>
                        <div><strong>${program.trim()}</strong></div>
                    </div>`;
                });
                
                formattedHTML += "</div>";
                return formattedHTML;
            } catch (error) {
                console.error('Error formatting program list:', error);
                return text; // Return original text if there's an error
            }
        }
        
        // Check if this is a loading message
        if (text === 'Fetching our current programs...') {
            return text + '<div class="loading-spinner"></div>';
        }
        
        return text; // Return original text if it's not a program list
    }
    
    // Send message functionality
    function sendMessage() {
        const messageText = messageInput.value.trim();
        console.log("Attempting to send message:", messageText);
        
        if (messageText) {
            // Add user message
            addMessage('user', messageText);
            messageInput.value = '';
            
            // Check if user is selecting a program by number
            const programNumber = parseInt(messageText);
            if (activeTab === 'programs' && !isNaN(programNumber)) {
                // Show loading message
                addMessage('bot', 'Fetching program details...');
                
                // Fetch programs from API
                fetchPrograms().then(programs => {
                    if (programs && programs.length > 0) {
                        const selectedProgram = programs[programNumber - 1];
                        if (selectedProgram) {
                            let responseText = `Details for <strong>${selectedProgram.pgm_name || 'Program'}</strong>:<br><br>`;
                            responseText += `<div style="margin-bottom: 10px;"><strong>Name:</strong> ${selectedProgram.pgm_name || 'N/A'}</div>`;
                            if (selectedProgram.pgm_desc) responseText += `<div style="margin-bottom: 10px;"><strong>Description:</strong> ${selectedProgram.pgm_desc}</div>`;
                            //if (selectedProgram.pgm_category) responseText += `<div style="margin-bottom: 10px;"><strong>Category:</strong> ${selectedProgram.pgm_category}</div>`;
                            if (selectedProgram.pgm_year) responseText += `<div style="margin-bottom: 10px;"><strong>Year of Duration:</strong> ${selectedProgram.pgm_year}</div>`;
                            //if (selectedProgram.pgm_school) responseText += `<div style="margin-bottom: 10px;"><strong>Program School:</strong> ${selectedProgram.pgm_school}</div>`;
                            addMessage('bot', responseText);
                        } else {
                            addMessage('bot', 'Invalid program number. Please enter a number from the list.');
                        }
                    } else {
                        addMessage('bot', 'I\'m sorry, I couldn\'t retrieve the program details at the moment. Please try again later.');
                    }
                }).catch(error => {
                    console.error('Error fetching programs:', error);
                    addMessage('bot', 'I\'m sorry, there was an issue retrieving program details. Please try again later.');
                });
                return;
            }
            
            // Check for program list request
            if (activeTab === 'programs' && isProgramListRequest(messageText)) {
                // Show loading message
                addMessage('bot', 'Fetching our current programs...');
                
                // Fetch programs from API
                fetchPrograms().then(programs => {
                    if (programs && programs.length > 0) {
                        // Format the programs into a list
                        let responseText = 'Here are our current programs:';
                        programs.forEach(program => {
                            if (program && program.pgm_name) {
                                responseText += `\n• ${program.pgm_name}`;
                            } else {
                                console.warn('Invalid program data:', program);
                            }
                        });
                        responseText += '\n\n<div style="margin-top: 20px;">If you want to know more about a program, type its number and send.</div>';
                        addMessage('bot', responseText);
                    } else {
                        addMessage('bot', 'I\'m sorry, I couldn\'t retrieve the program list at the moment. Please try again later or contact our admissions office for more information.');
                    }
                }).catch(error => {
                    console.error('Error fetching programs:', error);
                    addMessage('bot', 'I\'m sorry, there was an issue retrieving our program list. Please try again later or contact our admissions office for assistance.');
                });
            } else {
                // Default responses based on active tab
                setTimeout(() => {
                    let responseText = '';
                    
                    switch(activeTab) {
                        case 'programs':
                            responseText = 'I can provide information about our academic programs. Ask me about specific courses or say "show programs" to see a complete list.';
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
    }
    
    // Helper function to check if the message is requesting a program list
    function isProgramListRequest(message) {
        const lowerMessage = message.toLowerCase();
        return lowerMessage.includes('program') || 
               lowerMessage.includes('course') || 
               lowerMessage.includes('list') ||
               lowerMessage.includes('offering') ||
               lowerMessage.includes('what') ||
               lowerMessage.includes('show');
    }
    
    // Function to format program details
    function formatProgramDetails(text) {
        if (text.includes('Details for program')) {
            return text.replace(/\n/g, '<br>').replace(/<strong>(.*?)<\/strong>/g, '<strong>$1</strong><br>');
        }
        return text;
    }
    
    // Add message to chat
    function addMessage(sender, text) {
        console.log(`Adding ${sender} message:`, text);
        
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message-wrapper');
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        if (sender === 'bot') {
            const avatarContainer = document.createElement('div');
            avatarContainer.classList.add('avatar-container');
            
            // Get avatar safely
            const avatarElement = document.getElementById(`${activeTab}-avatar`);
            if (avatarElement) {
                const avatar = avatarElement.cloneNode(true);
                avatarContainer.appendChild(avatar);
                messageWrapper.appendChild(avatarContainer);
            } else {
                console.error(`Avatar element not found: ${activeTab}-avatar`);
                // Use a fallback
                const fallbackAvatar = document.createElement('div');
                fallbackAvatar.classList.add('avatar');
                fallbackAvatar.style.background = '#4cc9f0';
                avatarContainer.appendChild(fallbackAvatar);
                messageWrapper.appendChild(avatarContainer);
            }
        }
        
        // Format text if needed (for programs list)
        const formattedText = formatProgramList(text);
        
        // Use innerHTML instead of textContent to render HTML formatting
        messageDiv.innerHTML = formattedText;
        
        messageWrapper.appendChild(messageDiv);
        messagesContainer.appendChild(messageWrapper);
        
        // Ensure scroll to bottom
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
    
    // Event listeners
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
        console.log("Send button listener added");
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        console.log("Message input listener added");
    }
});