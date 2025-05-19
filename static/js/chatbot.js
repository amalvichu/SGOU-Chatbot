
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
    'academics': {
        name: 'Academic Pro',
        intro: 'Hello! I\'m Academic Pro, your guide to all our educational programs. How can I assist you today?'
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
    // Tab-specific suggestions
    const tabSuggestions = {
        'academics': [
            'List all programs',
            'What are the faculties?',
            'How long is the BA program?',
            'What are the admission requirements?'
        ],
        'certification': [
            'Tell me about certification courses',
            'How to apply for certification?',
            'What are the certification fees?',
            'Certification exam dates'
        ],
        'centers': [
            'List all study centers',
            'Center contact information',
            'Center facilities',
            'Center operating hours'
        ],
        'learning-center': [
            'Available learning resources',
            'How to access e-learning?',
            'Library services',
            'Tutorial schedules'
        ]
    };

    const suggestionsContainer = document.querySelector('.suggestions-container');
    
    function updateSuggestions(tab) {
        suggestionsContainer.innerHTML = '';
        tabSuggestions[tab].forEach(query => {
            const suggestion = document.createElement('div');
            suggestion.className = 'suggestion';
            suggestion.setAttribute('data-query', query);
            suggestion.textContent = query;
            
            suggestion.addEventListener('mouseenter', function() {
                this.classList.add('hover');
            });
            
            suggestion.addEventListener('mouseleave', function() {
                this.classList.remove('hover');
            });
            
            suggestion.addEventListener('click', function() {
                messageInput.value = query;
                sendMessage();
            });
            
            suggestionsContainer.appendChild(suggestion);
        });
    }
    

    
    // Ensure messages container is visible immediately
    if (messagesContainer) {
        messagesContainer.style.display = 'block';
    }
    
    // Debug element presence
    console.log("Message input found:", !!messageInput);
    console.log("Send button found:", !!sendButton);
    console.log("Messages container found:", !!messagesContainer);
    
    let activeTab = 'academics';
    
    // Set Academics tab as active and show intro on page load
    const academicsTab = document.querySelector('[data-tab="academics"]');
    if (academicsTab) {
        academicsTab.classList.add('active');
        const character = tabCharacters['academics'];
        if (character) {
            // Create avatar container if it doesn't exist
            const ensureAvatar = () => {
                let avatarContainer = document.querySelector('.avatar-container');
                if (!avatarContainer) {
                    avatarContainer = document.createElement('div');
                    avatarContainer.className = 'avatar-container';
                    document.body.appendChild(avatarContainer);
                }
                
                let avatar = document.getElementById('academics-avatar');
                if (!avatar) {
                    avatar = document.createElement('div');
                    avatar.id = 'academics-avatar';
                    avatar.className = 'avatar';
                    avatarContainer.appendChild(avatar);
                }
                return avatar;
            };

            // Double check DOM elements are ready
            const checkElements = () => {
                const messagesContainer = document.querySelector('.messages');
                const avatar = ensureAvatar();
                
                if (messagesContainer) {
                    addMessage('bot', character.intro);
                    messagesContainer.style.display = 'block';
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    return true;
                }
                return false;
            };
            
            // Try immediately and then with increasing delays
            if (!checkElements()) {
                setTimeout(() => {
                    if (!checkElements()) {
                        setTimeout(checkElements, 500);
                    }
                }, 300);
            }
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
            
            // Update suggestions for the new tab
            updateSuggestions(activeTab);
        });
    });
    
    // Initialize suggestions for the default tab
    updateSuggestions(activeTab);
    
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
            if (activeTab === 'academics' && !isNaN(programNumber)) {
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
                            if (selectedProgram.pgm_category) responseText += `<div style="margin-bottom: 10px;"><strong>Category:</strong> ${selectedProgram.pgm_category}</div>`;
                            if (selectedProgram.pgm_year) responseText += `<div style="margin-bottom: 10px;"><strong>Year of Duration:</strong> ${selectedProgram.pgm_year}</div>`;
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
            
            // Helper function to check if message is about duration
            function isDurationQuery(message) {
                const lowerMessage = message.toLowerCase();
                return lowerMessage.includes('duration') || 
                       lowerMessage.includes('length') || 
                       lowerMessage.includes('how long') ||
                       lowerMessage.includes('years') ||
                       lowerMessage.includes('time') ||
                       lowerMessage.includes('period');
            }
            
            function extractProgramNameFromQuery(message) {
                const programKeywords = ['ba', 'ma', 'bachelor', 'master', 'bcom', 'msc', 'bba'];
                const words = message.toLowerCase().split(' ');
                
                // Find the index of program keyword
                const keywordIndex = words.findIndex(word => programKeywords.includes(word));
                if (keywordIndex === -1) return null;
                
                // Extract program name starting from keyword
                const programName = words.slice(keywordIndex).join(' ');
                return programName;
            }
            
            // Process academic queries through decision model
            if (activeTab === 'academics' && !isProgramListRequest(messageText) && isNaN(parseInt(messageText))) {
                // Check for duration queries first
                if (isDurationQuery(messageText)) {
                    // Show loading message
                    addMessage('bot', 'Fetching program duration information...');
                    
                    // Fetch programs from API
                    fetchPrograms().then(programs => {
                        if (programs && programs.length > 0) {
                            // Find programs with duration info
                            const programsWithDuration = programs.filter(p => p.pgm_year);
                            if (programsWithDuration.length > 0) {
                                const programName = extractProgramNameFromQuery(messageText);
                                
                                if (programName) {
                                    // Find specific program
                                    const program = programsWithDuration.find(p => 
                                        p.pgm_name.toLowerCase().includes(programName)
                                    );
                                    
                                    if (program) {
                                        addMessage('bot', 
                                            `The duration of ${program.pgm_name} is ${program.pgm_year} year(s).`
                                        );
                                    } else {
                                        addMessage('bot', 
                                            `Couldn't find duration information for ${programName}. ` +
                                            'Here are all available programs with durations:\n' +
                                            programsWithDuration.map(p => 
                                                `• ${p.pgm_name}: ${p.pgm_year} year(s)`
                                            ).join('\n')
                                        );
                                    }
                                } else {
                                    // If no specific program mentioned, show all durations
                                    let responseText = 'Program durations:\n';
                                    programsWithDuration.forEach(program => {
                                        responseText += `• ${program.pgm_name}: ${program.pgm_year} year(s)\n`;
                                    });
                                    addMessage('bot', responseText);
                                }
                            } else {
                                addMessage('bot', 'Duration information is not currently available for our programs.');
                            }
                        } else {
                            addMessage('bot', 'I\'m sorry, I couldn\'t retrieve the program information at the moment. Please try again later.');
                        }
                    }).catch(error => {
                        console.error('Error fetching programs:', error);
                        addMessage('bot', 'I\'m sorry, there was an issue retrieving program information. Please try again later.');
                    });
                    return;
                }
                
                // Default academic query processing
                // Show loading message
                addMessage('bot', 'Processing your academic query...');
                
                // Call backend API to process query through academic decision model
                fetch('/api/process_query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: messageText })
                })
                .then(response => response.json())
                .then(data => {
                    if (data && data.message) {
                        addMessage('bot', data.message);
                    } else {
                        addMessage('bot', 'I\'m sorry, I couldn\'t process your query at the moment. Please try again later.');
                    }
                })
                .catch(error => {
                    console.error('Error processing query:', error);
                    addMessage('bot', 'I\'m sorry, there was an issue processing your query. Please try again later.');
                });
                return;
            }
            
            // Check for program list request
            if (activeTab === 'academics' && isProgramListRequest(messageText)) {
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
                        case 'academics':
                            responseText = 'I can provide information about our academic programs. Ask me about specific courses or say "show academics" to see a complete list.';
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
            const avatarId = `${activeTab}-avatar`;
            const avatarElement = document.getElementById(avatarId);
            
            if (!avatarElement && activeTab === 'academics') {
                // Create academics avatar if it doesn't exist
                const newAvatar = document.createElement('div');
                newAvatar.id = avatarId;
                newAvatar.classList.add('avatar');
                document.body.appendChild(newAvatar);
            }
            
            const avatarToUse = document.getElementById(avatarId) || 
                document.querySelector('.avatar') || 
                document.createElement('div');
                
            const avatar = avatarToUse.cloneNode(true);
            avatarContainer.appendChild(avatar);
            messageWrapper.appendChild(avatarContainer);
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