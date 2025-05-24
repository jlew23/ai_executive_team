/**
 * Chat Utility Functions for AI Executive Team
 * 
 * This file contains helper functions for the chat interface, including:
 * - Agent status checking
 * - Chat history persistence (save/restore)
 * - Message display functions (user, agent, system messages)
 * - Typing indicators
 * - Response polling
 * - Text processing and formatting
 * 
 * These utilities support the main chat functionality in chat.js
 */

/**
 * Checks the status of a specific agent
 * 
 * @param {string} agentName - The name of the agent to check (e.g., 'CEO', 'CTO')
 * @returns {string} - The agent's status ('active', 'inactive', 'error', or 'unknown')
 */
async function checkAgentStatus(agentName) {
    try {
        // Make an API call to the backend to check if the agent is running
        const response = await fetch(`/agents/${getAgentId(agentName.toUpperCase())}`, {
            method: 'GET',
            headers: {
                'Accept': 'text/html'
            }
        });

        // Handle HTTP errors
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        // Parse the HTML response
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const badge = doc.querySelector('.badge');

        if (badge) {
            const status = badge.textContent.toLowerCase();
            const statusBadge = document.getElementById('statusBadge');
            statusBadge.className = 'badge';

            if (status === 'active') {
                statusBadge.classList.add('bg-success');
                statusBadge.textContent = 'Online';
                return 'active';
            } else if (status === 'inactive') {
                statusBadge.classList.add('bg-warning');
                statusBadge.textContent = 'Inactive';
                return 'inactive';
            } else {
                statusBadge.classList.add('bg-danger');
                statusBadge.textContent = 'Error';
                return 'error';
            }
        }

        return 'unknown';
    } catch (error) {
        console.error('Error checking agent status:', error);
        return 'unknown';
    }
}

/**
 * Saves the current chat settings to localStorage
 * This allows user preferences to persist between sessions
 * 
 * Stores the following settings:
 * - Whether to use the knowledge base
 * - Whether to use a local model
 * - Which model is selected
 */
function saveChatSettings() {
    // Collect current settings from UI elements
    const settings = {
        useKnowledgeBase: document.getElementById('useKnowledgeBase').checked,
        useLocalModel: document.getElementById('useLocalModel').checked,
        model: document.getElementById('modelSelect').value
    };
    
    // Save to localStorage as a JSON string
    localStorage.setItem('chatSettings', JSON.stringify(settings));
    console.log('Chat settings saved:', settings);
}

/**
 * Restores previously saved chat settings from localStorage
 * 
 * @returns {boolean} - True if settings were successfully restored, false otherwise
 */
function restoreChatSettings() {
    // Try to get saved settings from localStorage
    const savedSettings = localStorage.getItem('chatSettings');
    if (!savedSettings) return false; // No saved settings found
    
    try {
        // Parse the JSON string back into an object
        const settings = JSON.parse(savedSettings);
        console.log('Restoring chat settings:', settings);
        
        // Restore each setting to the UI if it exists in the saved settings
        
        // Restore knowledge base toggle
        if (settings.useKnowledgeBase !== undefined) {
            document.getElementById('useKnowledgeBase').checked = settings.useKnowledgeBase;
        }
        
        // Restore local model toggle
        if (settings.useLocalModel !== undefined) {
            document.getElementById('useLocalModel').checked = settings.useLocalModel;
        }
        
        // Restore selected model
        if (settings.model) {
            const modelSelect = document.getElementById('modelSelect');
            // Only set the value if that model option exists in the dropdown
            // This prevents errors if available models have changed
            const optionExists = Array.from(modelSelect.options).some(option => option.value === settings.model);
            if (optionExists) {
                modelSelect.value = settings.model;
            }
        }
        
        return true; // Settings successfully restored
    } catch (error) {
        // Handle any errors during parsing or restoration
        console.error('Error restoring chat settings:', error);
        return false;
    }
}

/**
 * Saves the current chat history to localStorage
 * 
 * This function preserves the entire chat conversation, including:
 * - User messages
 * - Agent responses
 * - System messages
 * - Typing indicators
 * - Current state (if a response is being generated)
 * 
 * This allows the chat to be restored exactly as it was if the user
 * refreshes the page or navigates away and comes back.
 */
function saveChatHistory() {
    // Get the chat container and all message elements
    const chatMessages = document.getElementById('chatMessages');
    const messages = [];
    const messageElements = chatMessages.querySelectorAll('.message');
    
    // Process each message element in the DOM
    messageElements.forEach(el => {
        // Determine message type based on CSS classes
        let type = 'system';  // Default type
        if (el.classList.contains('user-message')) type = 'user';
        if (el.classList.contains('agent-message')) type = 'agent';
        if (el.classList.contains('typing-indicator-container')) type = 'typing';
        
        // Extract the message content from the DOM
        const contentEl = el.querySelector('.message-content');
        const content = contentEl ? contentEl.innerHTML : '';
        
        // For agent messages, get the agent name
        const agentNameEl = el.querySelector('.agent-name');
        const agentName = agentNameEl ? agentNameEl.textContent.replace(':', '') : '';
        
        // Create a structured object for this message and add to the array
        messages.push({
            type,           // 'user', 'agent', 'system', or 'typing'
            content,        // The HTML content of the message
            agentName,      // Which agent sent the message (if applicable)
            timestamp: el.dataset.timestamp || new Date().toISOString() // When the message was sent
        });
    });
    
    // Create a complete chat state object
    const chatData = {
        messages: messages,  // All messages in the conversation
        isGeneratingResponse: window.isGeneratingResponse, // Whether we're waiting for a response
        currentMessageId: window.currentMessageId,         // ID of the current in-progress message
        lastUpdated: new Date().toISOString()              // When this state was saved
    };
    
    // Save the chat state to localStorage
    localStorage.setItem('chatHistory', JSON.stringify(chatData));
    console.log('Chat history saved:', chatData);
}

/**
 * Restores chat history from localStorage
 * 
 * This function rebuilds the entire chat conversation from saved data,
 * including all messages and the current state (if a response was being generated).
 * 
 * @returns {boolean} - True if chat history was successfully restored, false otherwise
 */
function restoreChatHistory() {
    // Get the chat container and previously saved chat data
    const chatMessages = document.getElementById('chatMessages');
    const savedChat = localStorage.getItem('chatHistory');
    
    // If no saved chat history exists, return false
    if (!savedChat) return false;
    
    try {
        // Parse the saved chat data
        const chatData = JSON.parse(savedChat);
        console.log('Restoring chat history:', chatData);
        
        // Clear the current chat container to start fresh
        chatMessages.innerHTML = '';
        
        // Rebuild each message in the conversation
        chatData.messages.forEach(msg => {
            // Add different types of messages using the appropriate functions
            if (msg.type === 'user') {
                // Add user messages
                addUserMessage(msg.content);
            } else if (msg.type === 'agent') {
                // Add agent responses with the correct agent name
                addAgentMessage(msg.content, msg.agentName);
            } else if (msg.type === 'system') {
                // Add system messages (errors, notifications, etc.)
                addSystemMessage(msg.content);
            }
            // Note: 'typing' indicators are handled separately below
        });
        
        // If there was a response being generated when the chat was saved,
        // restore that state and continue polling for the response
        if (chatData.isGeneratingResponse && chatData.currentMessageId) {
            // Set the global state variables
            window.isGeneratingResponse = true;
            window.currentMessageId = chatData.currentMessageId;
            
            // Show the typing indicator (default to CEO if agent not specified)
            addTypingIndicator(chatData.agent || 'CEO');
            
            // Resume polling for the response
            startPollingForResponse(window.currentMessageId);
        } else {
            // Otherwise, reset the state variables
            window.isGeneratingResponse = false;
            window.currentMessageId = null;
        }
        
        // Scroll to the bottom of the chat to show the latest messages
        scrollToBottom();
        
        return true; // History successfully restored
    } catch (error) {
        // Handle any errors during parsing or restoration
        console.error('Error restoring chat history:', error);
        return false;
    }
}

/**
 * Adds a user message to the chat interface
 * 
 * This function creates a new message element for user messages,
 * processes the content for formatting, and adds it to the chat container.
 * 
 * @param {string} message - The message content to display (can be HTML)
 */
function addUserMessage(message) {
    // Get the chat container
    const chatMessages = document.getElementById('chatMessages');
    
    // Create a new message element
    const div = document.createElement('div');
    div.className = 'message user-message'; // Apply user message styling
    div.dataset.timestamp = new Date().toISOString(); // Store the timestamp for history
    
    // Set the HTML content with the processed message
    // The processMessageContent function handles formatting, code blocks, etc.
    div.innerHTML = `
        <div class="message-content">
            ${processMessageContent(message)}
        </div>
    `;
    
    // Add the message to the chat
    chatMessages.appendChild(div);
    
    // Scroll to make the new message visible
    scrollToBottom();
}

/**
 * Adds an agent message to the chat interface
 * 
 * This function creates a styled message element for agent responses,
 * including the agent's avatar, name, and formatted message content.
 * 
 * @param {string} message - The message content from the agent
 * @param {string} agentName - The name of the agent (CEO, CTO, etc.)
 */
function addAgentMessage(message, agentName) {
    // Remove any existing typing indicator first
    removeTypingIndicator();
    
    // Get the chat container
    const chatMessages = document.getElementById('chatMessages');
    
    // Use the provided agent name or fall back to the currently selected agent
    const agent = agentName || document.getElementById('agentSelector').value.toUpperCase();
    
    // Create a new message element
    const div = document.createElement('div');
    div.className = 'message agent-message'; // Apply agent message styling
    div.dataset.timestamp = new Date().toISOString(); // Store the timestamp for history
    
    // Set the HTML content with agent styling and the processed message
    // This includes the agent's avatar, name with appropriate color, and the message content
    div.innerHTML = `
        <div class="message-avatar">
            <div class="avatar ${getAgentColor(agent)} text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                ${getAgentIcon(agent)}
            </div>
        </div>
        <div class="message-content">
            <span class="agent-name fw-bold ${getAgentTextColor(agent)}">${agent}:</span> ${processMessageContent(message)}
        </div>
    `;
    
    // Add the message to the chat
    chatMessages.appendChild(div);
    
    // Scroll to make the new message visible
    scrollToBottom();
}

/**
 * Processes message content to handle formatting, code blocks, and security
 * 
 * This function takes raw message text and processes it to:
 * 1. Handle security by escaping HTML to prevent XSS attacks
 * 2. Format code blocks with syntax highlighting
 * 3. Format inline code
 * 4. Convert line breaks to HTML breaks
 * 
 * @param {string} message - The raw message content to process
 * @returns {string} - The processed HTML-safe message with formatting
 */
function processMessageContent(message) {
    // Handle empty messages
    if (!message) {
        return '';
    }
    
    // If the message is already HTML (starts with a tag), return it as is
    // This is used for system messages or pre-formatted content
    if (typeof message === 'string' && message.trim().startsWith('<')) {
        return message;
    }
    
    // Security: Escape HTML to prevent XSS attacks
    // This converts <, >, &, ", and ' to their HTML entity equivalents
    let processedMessage = escapeHtml(message);
    
    // Convert newlines to HTML line breaks for proper display
    processedMessage = processedMessage.replace(/\n/g, '<br>');
    
    // Format code blocks with syntax highlighting
    // Matches text between triple backticks with optional language specification
    // Example: ```javascript console.log('hello'); ```
    processedMessage = processedMessage.replace(/```(\w*)\s*([\s\S]*?)```/g, function(match, language, code) {
        return `<pre><code class="${language}">${code}</code></pre>`;
    });
    
    // Format inline code with single backticks
    // Example: `const x = 1;`
    processedMessage = processedMessage.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    return processedMessage;
}

/**
 * Adds a system message to the chat interface
 * 
 * This function creates a styled message element for system messages,
 * which are used for notifications, errors, and other system-generated content.
 * System messages are visually distinct from user and agent messages.
 * 
 * @param {string} message - The message content to display (can contain HTML)
 */
function addSystemMessage(message) {
    // Get the chat container
    const chatMessages = document.getElementById('chatMessages');
    
    // Create a new message element
    const messageElement = document.createElement('div');
    messageElement.className = 'message system-message'; // Apply system message styling
    messageElement.dataset.timestamp = new Date().toISOString(); // Store timestamp for history
    
    // Set the HTML content directly (system messages can contain HTML)
    messageElement.innerHTML = `<div class="message-content">${message}</div>`;
    
    // Add the message to the chat
    chatMessages.appendChild(messageElement);
    
    // Scroll to make the new message visible
    scrollToBottom();
}

/**
 * Adds a typing indicator to the chat interface
 * 
 * This function creates a styled message element that simulates a typing indicator,
 * which is used to indicate that an agent is currently typing a response.
 * The typing indicator is visually distinct from other messages and includes
 * an animated typing effect.
 * 
 * @param {string} agentName - The name of the agent who is typing (used for styling)
 */
function addTypingIndicator(agentName) {
    // Get the chat container
    const chatMessages = document.getElementById('chatMessages');
    
    // Create a new message element
    const div = document.createElement('div');
    div.className = 'message agent-message typing-indicator-container';
    div.id = 'typingIndicator'; // Add an ID for easy removal later
    
    // Use the provided agent name or fall back to the currently selected agent
    const agent = agentName || document.getElementById('agentSelector').value.toUpperCase();
    
    // Set the HTML content with agent styling and the animated typing indicator
    div.innerHTML = `
        <div class="message-avatar">
            <div class="avatar ${getAgentColor(agent)} text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                ${getAgentIcon(agent)}
            </div>
        </div>
        <div class="message-content">
            <span class="agent-name fw-bold ${getAgentTextColor(agent)}">${agent}:</span>
            <div class="typing-indicator">
                <span></span> <!-- Animated dot -->
                <span></span> <!-- Animated dot -->
                <span></span> <!-- Animated dot -->
            </div>
        </div>
    `;
    
    // Add the typing indicator to the chat
    chatMessages.appendChild(div);
    
    // Scroll to make the typing indicator visible
    scrollToBottom();
}

/**
 * Removes the typing indicator from the chat interface
 * 
 * This function finds and removes the typing indicator element when
 * an agent's response is ready to be displayed or if an error occurs.
 * It's called before adding an agent's message to the chat.
 */
function removeTypingIndicator() {
    // Find the typing indicator element by its ID
    const typingIndicator = document.getElementById('typingIndicator');
    
    // If it exists, remove it from the DOM
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

/**
 * Scrolls the chat container to the bottom
 * 
 * This function ensures that the most recent messages are visible
 * to the user by scrolling the chat container to its maximum scroll height.
 * It's called after adding new messages or typing indicators.
 */
function scrollToBottom() {
    // Get the chat messages container element
    // This element contains all the messages in the chat interface
    const chatMessages = document.getElementById('chatMessages');
    
    // Set the scroll top position to the maximum scroll height
    // This effectively scrolls the container to the bottom, making the most recent message visible
    // The scrollHeight property returns the total height of the content in the element
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Starts polling for a response from the server
 * 
 * This function sets up an interval to periodically check if the server has
 * generated a response to the user's message. This is particularly useful for
 * long-running AI responses that might take several seconds to generate.
 * 
 * The polling continues until either:
 * 1. A complete response is received
 * 2. An error occurs
 * 3. The user sends a new message (changing the currentMessageId)
 * 4. The isGeneratingResponse flag is set to false
 * 
 * @param {string} messageId - The unique ID of the message being waited for
 */
function startPollingForResponse(messageId) {
    // Clear any existing polling interval to avoid multiple polling loops
    if (window.pollingInterval) {
        clearInterval(window.pollingInterval);
    }
    
    // Set up a new polling interval that runs every 2 seconds
    window.pollingInterval = setInterval(() => {
        // Stop polling if we're no longer waiting for a response
        if (!window.isGeneratingResponse) {
            clearInterval(window.pollingInterval);
            return;
        }
        
        // Stop polling if the user has sent a new message
        // (indicated by a different messageId)
        if (window.currentMessageId !== messageId) {
            clearInterval(window.pollingInterval);
            return;
        }
        
        // Make an API call to check the status of the response
        fetch(`/chat/api/check-response?message_id=${messageId}`)
            .then(response => response.json())
            .then(data => {
                // If the response is complete, display it
                if (data.status === 'complete' && data.response) {
                    // Stop polling
                    clearInterval(window.pollingInterval);
                    
                    // Remove the typing animation
                    removeTypingIndicator();
                    
                    // Update the global state
                    window.isGeneratingResponse = false;
                    
                    // Display the agent's response in the chat
                    const agent = document.getElementById('agentSelector').value.toUpperCase();
                    addAgentMessage(data.response, agent);
                    
                    // Save the updated chat history
                    saveChatHistory();
                    
                    // Re-enable the input form
                    document.getElementById('messageInput').disabled = false;
                    document.getElementById('sendButton').disabled = false;
                }
                // If an error occurred, display the error
                else if (data.status === 'error') {
                    // Stop polling
                    clearInterval(window.pollingInterval);
                    
                    // Remove the typing animation
                    removeTypingIndicator();
                    
                    // Update the global state
                    window.isGeneratingResponse = false;
                    
                    // Display the error message
                    addSystemMessage(`Error: ${data.error || 'Failed to generate response'}`);
                    
                    // Save the updated chat history
                    saveChatHistory();
                    
                    // Re-enable the input form
                    document.getElementById('messageInput').disabled = false;
                    document.getElementById('sendButton').disabled = false;
                }
                // If status is still 'generating', continue polling
                // The interval will run again automatically
            })
            .catch(error => {
                // Log any errors that occur during the API call
                // but continue polling (don't clear the interval)
                console.error('Error checking response:', error);
            });
    }, 2000); // Poll every 2 seconds
}

/**
 * Escapes HTML special characters to prevent XSS attacks
 * 
 * This function converts special characters to their HTML entity equivalents,
 * making them safe to include in HTML content.
 * 
 * @param {string} unsafe - The potentially unsafe string to escape
 * @returns {string} - The escaped string safe for HTML insertion
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Gets the agent ID from the agent name
 * 
 * This function maps agent names to their corresponding IDs
 * for use in API calls and other operations.
 * 
 * @param {string} agentName - The name of the agent (CEO, CTO, etc.)
 * @returns {number} - The ID of the agent
 */
function getAgentId(agentName) {
    const agentMap = {
        'CEO': 1,
        'CTO': 2,
        'CFO': 3,
        'CMO': 4,
        'COO': 5
    };
    
    return agentMap[agentName] || 1; // Default to CEO (ID 1) if not found
}

/**
 * Gets the color class for an agent's avatar
 * 
 * @param {string} agentName - The name of the agent
 * @returns {string} - The CSS class for the agent's color
 */
function getAgentColor(agentName) {
    const colorMap = {
        'CEO': 'bg-primary',
        'CTO': 'bg-success',
        'CFO': 'bg-warning',
        'CMO': 'bg-danger',
        'COO': 'bg-info'
    };
    
    return colorMap[agentName] || 'bg-secondary';
}

/**
 * Gets the text color class for an agent's name
 * 
 * @param {string} agentName - The name of the agent
 * @returns {string} - The CSS class for the agent's text color
 */
function getAgentTextColor(agentName) {
    const colorMap = {
        'CEO': 'text-primary',
        'CTO': 'text-success',
        'CFO': 'text-warning',
        'CMO': 'text-danger',
        'COO': 'text-info'
    };
    
    return colorMap[agentName] || 'text-secondary';
}

/**
 * Gets the icon for an agent's avatar
 * 
 * @param {string} agentName - The name of the agent
 * @returns {string} - The HTML for the agent's icon
 */
function getAgentIcon(agentName) {
    const iconMap = {
        'CEO': '<i class="bi bi-person-circle"></i>',
        'CTO': '<i class="bi bi-code-square"></i>',
        'CFO': '<i class="bi bi-cash-coin"></i>',
        'CMO': '<i class="bi bi-graph-up"></i>',
        'COO': '<i class="bi bi-gear"></i>'
    };
    
    return iconMap[agentName] || '<i class="bi bi-person"></i>';
}
