/**
 * Chat Functionality for AI Executive Team
 * 
 * This file contains the core chat functionality including:
 * - DOM element initialization
 * - Event handlers for user interactions
 * - Agent selection and status checking
 * - Message sending and receiving
 * - Integration with local and cloud LLMs
 * 
 * The file works in conjunction with chat-utils.js which contains
 * helper functions for chat operations.
 */

// Initialize the chat interface when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements for better performance and readability
    const chatMessages = document.getElementById('chatMessages');      // Container for all chat messages
    const chatForm = document.getElementById('chatForm');              // Form for submitting messages
    const messageInput = document.getElementById('messageInput');      // Text input for user messages
    const currentAgent = document.getElementById('currentAgent');      // Display of current active agent
    const currentAgentAvatar = document.getElementById('currentAgentAvatar'); // Avatar for current agent
    const clearChatButton = document.getElementById('clearChat');      // Button to clear chat history
    const useKnowledgeBaseSwitch = document.getElementById('useKnowledgeBase'); // Toggle for KB usage
    const useLocalModelSwitch = document.getElementById('useLocalModel'); // Toggle for local model usage
    const modelSelect = document.getElementById('modelSelect');        // Dropdown for model selection
    const statusBadge = document.getElementById('statusBadge');        // Badge showing agent status
    const sendButton = document.querySelector('#chatForm button[type="submit"]'); // Send message button
    const agentSelector = document.getElementById('agentSelector');    // Dropdown to select which agent to message
    
    // Internal state variables for tracking chat status
    let isGeneratingResponse = false;  // Tracks if we're currently waiting for an agent response
    let currentMessageId = null;       // ID of the current message being processed
    let pollingInterval = null;        // Interval reference for polling the server for responses

    // Get all agent selection buttons from the sidebar
    const agentButtons = document.querySelectorAll('.agent-select'); // Buttons for selecting different agents
    
    /**
     * Helper functions for agent styling
     * These functions provide consistent visual styling for each agent
     * throughout the chat interface (colors, icons, etc.)
     */
    
    /**
     * Get the appropriate background color class for an agent
     * @param {string} agent - The agent role (CEO, CTO, etc.)
     * @returns {string} CSS class for the agent's background color
     */
    function getAgentColor(agent) {
        switch(agent.toUpperCase()) {
            case 'CEO': return 'bg-primary';  // Blue for CEO
            case 'CTO': return 'bg-info';     // Light blue for CTO
            case 'CFO': return 'bg-success';  // Green for CFO
            case 'CMO': return 'bg-warning';  // Yellow/orange for CMO
            case 'COO': return 'bg-danger';   // Red for COO
            default: return 'bg-secondary';   // Gray for unknown agents
        }
    }
    
    /**
     * Get the appropriate icon for an agent
     * @param {string} agent - The agent role (CEO, CTO, etc.)
     * @returns {string} HTML for the agent's icon
     */
    function getAgentIcon(agent) {
        switch(agent.toUpperCase()) {
            case 'CEO': return '<i class="fas fa-user-tie"></i>';      // Business person icon
            case 'CTO': return '<i class="fas fa-laptop-code"></i>';  // Code/laptop icon
            case 'CFO': return '<i class="fas fa-chart-line"></i>';   // Chart/graph icon
            case 'CMO': return '<i class="fas fa-bullhorn"></i>';     // Marketing/bullhorn icon
            case 'COO': return '<i class="fas fa-cogs"></i>';         // Operations/cogs icon
            default: return '<i class="fas fa-user"></i>';            // Generic user icon
        }
    }
    
    /**
     * Get the appropriate text color class for an agent
     * @param {string} agent - The agent role (CEO, CTO, etc.)
     * @returns {string} CSS class for the agent's text color
     */
    function getAgentTextColor(agent) {
        switch(agent.toUpperCase()) {
            case 'CEO': return 'text-primary';  // Blue text for CEO
            case 'CTO': return 'text-info';     // Light blue text for CTO
            case 'CFO': return 'text-success';  // Green text for CFO
            case 'CMO': return 'text-warning';  // Yellow/orange text for CMO
            case 'COO': return 'text-danger';   // Red text for COO
            default: return 'text-secondary';   // Gray text for unknown agents
        }
    }
    
    /**
     * Set up event listeners for agent selection buttons in the sidebar
     * When a user clicks on an agent button, we update the UI and set that agent as active
     */
    agentButtons.forEach(button => {
        button.addEventListener('click', async function() {
            // Remove active class from all buttons for proper highlighting
            agentButtons.forEach(btn => btn.classList.remove('active'));

            // Add active class to the clicked button
            this.classList.add('active');

            // Get the agent identifier from the button and update the message form selector
            const agent = this.getAttribute('data-agent');
            agentSelector.value = agent;

            // Check if the selected agent is active/online
            const status = await checkAgentStatus(agent);

            // Inform the user about the agent selection with a system message
            addSystemMessage(`You've selected the ${agent.toUpperCase()} as your primary contact`);

            // Persist the updated chat state to localStorage
            saveChatHistory();
        });
    });

    /**
     * Set up event listener for the Clear Chat button
     * This will remove all messages and reset the chat history
     */
    clearChatButton.addEventListener('click', function() {
        // Ask for confirmation before clearing to prevent accidental data loss
        if (confirm('Are you sure you want to clear the chat history?')) {
            // Remove all messages from the UI
            chatMessages.innerHTML = '';
            
            // Delete the saved chat history from localStorage
            localStorage.removeItem('chatHistory');
            
            // Add a system message confirming the action
            addSystemMessage('Chat history cleared.');
        }
    });

    /**
     * Set up event listener for the Knowledge Base toggle switch
     * When toggled, this determines whether the AI uses the knowledge base for responses
     */
    useKnowledgeBaseSwitch.addEventListener('change', function() {
        // Save the updated setting to localStorage
        saveChatSettings();
    });

    /**
     * Set up event listener for the Local Model toggle switch
     * This determines whether to use local LLMs (via LM Studio) or cloud models
     */
    useLocalModelSwitch.addEventListener('change', function() {
        if (this.checked) {
            // When switched to local models, fetch available models from LM Studio
            fetchLocalModels();
        } else {
            // When switched to cloud models, restore the default cloud model options
            populateCloudModels();
        }
        // Save the updated setting to localStorage
        saveChatSettings();
    });
    
    /**
     * Fetch available local models from LM Studio and populate the model dropdown
     * This is called when the user switches to local models or on page load if local models are enabled
     */
    function fetchLocalModels() {
        // Call the API endpoint that retrieves local models from LM Studio
        fetch('/api/local-models')
            .then(response => response.json())
            .then(data => {
                if (data.models && data.models.length > 0) {
                    // Clear existing options in the dropdown
                    modelSelect.innerHTML = '';
                    
                    // Add each local model as an option in the dropdown
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.name;       // Value used when submitting the form
                        option.textContent = model.name; // Display text shown to the user
                        modelSelect.appendChild(option);
                    });
                } else {
                    // If no models were found, show an error message
                    addSystemMessage('No local models found. Please check your LM Studio installation.');
                }
            })
            .catch(error => {
                // Handle any errors that occur during the fetch
                console.error('Error fetching local models:', error);
                addSystemMessage('Error fetching local models. Using default models.');
                // Fall back to cloud models if we can't get local models
                populateCloudModels();
            });
    }
    
    /**
     * Populate the model dropdown with cloud-based LLM options
     * This is called when the user switches from local to cloud models
     * or when local models fail to load
     */
    function populateCloudModels() {
        // Clear existing options in the dropdown
        modelSelect.innerHTML = '';
        
        // Define the available cloud models
        const cloudModels = [
            { value: 'gpt-3.5-turbo', text: 'GPT-3.5 Turbo' },  // OpenAI's GPT-3.5
            { value: 'gpt-4', text: 'GPT-4' },                  // OpenAI's GPT-4
            { value: 'claude-3-opus', text: 'Claude 3 Opus' },   // Anthropic's Claude 3 Opus
            { value: 'claude-3-sonnet', text: 'Claude 3 Sonnet' } // Anthropic's Claude 3 Sonnet
        ];
        
        // Add each cloud model as an option in the dropdown
        cloudModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.value;       // API identifier for the model
            option.textContent = model.text;   // User-friendly display name
            modelSelect.appendChild(option);
        });
        
        // Set GPT-4 as the default selected model
        modelSelect.value = 'gpt-4';
    }

    /**
     * Handle chat form submission when the user sends a message
     * This is the core function that processes user input and sends it to the backend
     */
    chatForm.addEventListener('submit', function(e) {
        // Prevent the default form submission behavior
        e.preventDefault();

        // Get the user's message and trim whitespace
        const message = messageInput.value.trim();
        // Don't process empty messages
        if (!message) return;

        // Display the user's message in the chat
        addUserMessage(message);

        // Clear the input field for the next message
        messageInput.value = '';

        // Get the currently selected agent from the dropdown
        const selectedAgent = agentSelector.value.toUpperCase();

        // Show the typing indicator to let the user know the agent is "thinking"
        addTypingIndicator(selectedAgent);
        
        // Update state to indicate we're waiting for a response
        isGeneratingResponse = true;
        // Generate a unique ID for this message using the current timestamp
        const messageId = Date.now().toString();
        currentMessageId = messageId;
        
        // Save the current chat state to localStorage (including the typing indicator)
        // This ensures the state persists if the user navigates away or refreshes
        saveChatHistory();

        /**
         * Load LLM settings from localStorage
         * These settings determine which model to use and how to configure it
         */
        // Initialize with default values
        let apiKey = '';                             // OpenAI API key (empty by default)
        let localApiUrl = 'http://127.0.0.1:1234/v1'; // Default LM Studio API URL
        let localModel = '';                         // Name of the local model to use
        let temperature = 0.7;                       // Controls randomness (0.0-1.0)
        let maxTokens = 2048;                        // Maximum response length
        let useLocal = useLocalModelSwitch.checked;  // Whether to use local models

        // Try to load saved settings from localStorage
        const savedSettings = localStorage.getItem('llmSettings');
        if (savedSettings) {
            try {
                // Parse the saved settings JSON
                const settings = JSON.parse(savedSettings);
                
                // Extract settings with fallbacks to defaults
                apiKey = settings.openaiApiKey || '';
                localApiUrl = settings.localApiUrl || 'http://127.0.0.1:1234/v1';
                localModel = settings.localModel || '';
                temperature = settings.temperature || 0.7;
                maxTokens = settings.maxTokens || 2048;

                // If the saved provider is set to local, override the UI switch
                if (settings.llmProvider === 'local') {
                    useLocal = true;
                    useLocalModelSwitch.checked = true;
                    localModel = settings.localModel;
                    console.log('Using local model from settings:', localModel);
                }
            } catch (error) {
                // Handle any errors parsing the settings
                console.error('Error loading saved settings:', error);
            }
        }

        /**
         * Determine which model to use based on settings and UI state
         */
        let modelToUse;
        if (useLocal && localModel) {
            // If local mode is enabled and we have a local model name
            modelToUse = localModel;
            console.log('Using local model:', localModel);
            // Ensure the UI reflects that we're using local models
            useLocal = true;
            useLocalModelSwitch.checked = true;
        } else {
            // Otherwise use the selected cloud model from the dropdown
            modelToUse = modelSelect.value;
            console.log('Using cloud model:', modelSelect.value);
        }

        // Log all settings for debugging purposes
        console.log('Settings:', {
            model: modelToUse,                      // Which model we're using
            use_local: useLocal,                   // Whether we're using local or cloud
            api_key: apiKey ? 'set' : 'not set',   // Whether an API key is provided (masked for security)
            local_api_url: localApiUrl,            // The URL for the local model API
            temperature: temperature,              // Temperature setting for response generation
            max_tokens: maxTokens                  // Maximum response length
        });

        /**
         * Start polling for a response from the server
         * This allows the chat to continue working even if the user navigates away
         */
        startPollingForResponse(messageId);
        
        /**
         * Send the message to the backend API
         * This initiates the request to the AI model through our server
         */
        fetch('/chat/api/send', {
            method: 'POST',                     // Using POST to send data to the server
            headers: {
                'Content-Type': 'application/json'  // Telling the server we're sending JSON
            },
            body: JSON.stringify({               // Convert the request data to JSON
                message: message,                  // The user's message text
                agent: selectedAgent.toLowerCase(), // Which agent should respond (lowercase for API)
                model: modelToUse,                 // The model to use for generation
                use_kb: useKnowledgeBaseSwitch.checked, // Whether to use the knowledge base
                use_local: useLocal,               // Whether to use local models
                api_key: apiKey,                   // API key for cloud models
                local_api_url: localApiUrl,        // URL for local model API
                temperature: temperature,          // Temperature setting for response
                max_tokens: maxTokens,             // Maximum response length
                message_id: messageId              // Unique ID for this message
            })
        })
        .then(response => {
            // Check if the HTTP request was successful
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            // Parse the JSON response
            return response.json();
        })
        .catch(error => {
            // Handle any errors that occurred during the fetch
            console.error('Error sending message:', error);
            
            // Clean up the UI when an error occurs
            removeTypingIndicator();              // Remove the typing animation
            isGeneratingResponse = false;         // Reset the response flag
            saveChatHistory();                    // Save the updated chat state
            
            // Show an error message to the user
            addSystemMessage(`<span class="text-danger">Error: ${error.message || 'Failed to send message. Please try again.'}</span>`);
            
            // Re-enable the input form
            messageInput.disabled = false;
            sendButton.disabled = false;
            
            // Return null to indicate an error occurred
            return null;
        }).then(data => {
            // This runs after the first then() if no error occurred
            // or after catch() if an error was handled
            
            // Clean up the typing indicator
            removeTypingIndicator();
            
            // Reset the response flag since we've received a response (or error)
            isGeneratingResponse = false;

            // If data is null, it means an error occurred and was handled in catch()
            if (!data) {
                // Save the current chat state
                saveChatHistory();
                
                // Re-enable the form and focus the input field
                messageInput.disabled = false;
                sendButton.disabled = false;
                messageInput.value = '';
                messageInput.focus();
                return;
            }
            
            // Log the response data for debugging
            console.log('Response data:', data);

            // Process the response based on its status
            if (data.status === 'success') {
                // If we got a successful response
                if (data.response) {
                    // Add the agent's response to the chat
                    addAgentMessage(data.response, selectedAgent);
                } else {
                    // Handle the case where success was reported but no response was provided
                    addSystemMessage('No response received from the agent. Please try again.');
                }
            } else if (data.error) {
                // If the server returned an error
                // Display the error message to the user
                addSystemMessage(`Error: ${data.error}`);

                // If the error is related to agent status, update the UI accordingly
                if (data.agent_status) {
                    const statusBadge = document.getElementById('statusBadge');
                    statusBadge.className = 'badge'; // Reset badge classes

                    // Update the badge based on the agent status
                    if (data.agent_status === 'inactive') {
                        // Yellow warning for inactive agents
                        statusBadge.classList.add('bg-warning');
                        statusBadge.textContent = 'Inactive';
                    } else if (data.agent_status === 'error') {
                        // Red for error state
                        statusBadge.classList.add('bg-danger');
                        statusBadge.textContent = 'Error';
                    }
                }
            }
            
            // Save the updated chat history to localStorage
            saveChatHistory();
            
            // Re-enable the form elements for the next message
            messageInput.disabled = false;     // Enable the text input
            sendButton.disabled = false;       // Enable the send button
            messageInput.value = '';           // Clear any text in the input
            messageInput.focus();              // Focus the input for the next message
        });
        
        // Disable the form while waiting for a response to prevent multiple submissions
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        // Scroll the chat window to show the latest messages
        scrollToBottom();
    });
    
    // Initialize the model dropdown based on the local model switch
    if (useLocalModelSwitch.checked) {
        fetchLocalModels();
    } else {
        populateCloudModels();
    }
    
    // Restore chat history when the page loads
    restoreChatHistory();
});
