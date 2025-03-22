document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const navToggle = document.getElementById('nav-toggle');
    const headerNav = document.getElementById('header-nav');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const chatSidebar = document.getElementById('chat-sidebar');
    const themeToggle = document.getElementById('theme-toggle');
    const suggestionsElements = document.querySelectorAll('.dynamic-suggestion');
    const quickActionButtons = document.querySelectorAll('.action-chip');
    const scrollBottomBtn = document.getElementById('scroll-bottom');

    function isScrolledToBottom() {
        return chatMessages.scrollHeight - chatMessages.clientHeight <= chatMessages.scrollTop + 10;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function updateScrollButtonVisibility() {
        if (!isScrolledToBottom()) {
            scrollBottomBtn.classList.add('visible');
        } else {
            scrollBottomBtn.classList.remove('visible');
        }
    }

    function addMessage(message, isUser = false, type = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        if (type && !isUser) {
            messageDiv.classList.add(type);
        }

        const messageText = document.createElement('p');
        messageText.innerHTML = message.replace(/\n/g, '<br>');
        messageDiv.appendChild(messageText);

        const timestamp = document.createElement('span');
        timestamp.className = 'timestamp';
        const now = new Date();
        timestamp.innerText = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        messageDiv.appendChild(timestamp);

        chatMessages.appendChild(messageDiv);

        if (isScrolledToBottom()) {
            scrollToBottom();
        }

        updateScrollButtonVisibility();
    }

    function showTypingIndicator() {
        removeTypingIndicator();

        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingDiv.appendChild(dot);
        }

        chatMessages.appendChild(typingDiv);

        if (isScrolledToBottom()) {
            scrollToBottom();
        }
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    function handleSuggestionClick(text) {
        userInput.value = text;
        sendMessage();
    }

    function sendMessage() {
        const message = userInput.value.trim();

        if (!message) return;

        addMessage(message, true);
        userInput.value = '';

        showTypingIndicator();

        fetch('/chatbot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message, action: null })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();

            if (data.error) {
                addMessage("Sorry, there was an error processing your request. Please try again.", false);
                return;
            }

            let messageType = '';
            if (data.response.toLowerCase().includes('tip') || data.response.toLowerCase().includes('eco-friendly')) {
                messageType = 'eco-tip';
            } else if (data.response.toLowerCase().includes('collection') || data.response.toLowerCase().includes('schedule')) {
                messageType = 'schedule';
            }

            addMessage(data.response, false, messageType);

            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
            }

            if (data.calendar) {
                addCollectionCalendar(data.calendar);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage("Sorry, there was an error connecting to the server. Please try again later.", false);
        });
    }

    function sendAction(action) {
        showTypingIndicator();

        fetch('/chatbot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: null, action: action })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();

            if (data.error) {
                addMessage("Sorry, there was an error processing your request. Please try again.", false);
                return;
            }

            let messageType = '';
            if (action === 'tips' || data.response.toLowerCase().includes('tip')) {
                messageType = 'eco-tip';
            } else if (action === 'schedule' || data.response.toLowerCase().includes('schedule')) {
                messageType = 'schedule';
            }

            addMessage(data.response, false, messageType);

            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
            }

            if (data.calendar) {
                addCollectionCalendar(data.calendar);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage("Sorry, there was an error connecting to the server. Please try again later.", false);
        });
    }

    function displaySuggestions(suggestions) {
        const oldSuggestions = document.querySelectorAll('.dynamic-suggestion');
        oldSuggestions.forEach(suggestion => suggestion.remove());

        suggestions.forEach(text => {
            const suggestionEl = document.createElement('div');
            suggestionEl.className = 'dynamic-suggestion';
            suggestionEl.innerText = text;
            suggestionEl.dataset.suggestion = text;
            suggestionEl.addEventListener('click', () => handleSuggestionClick(text));
            chatMessages.appendChild(suggestionEl);
        });

        if (isScrolledToBottom()) {
            scrollToBottom();
        }

        updateScrollButtonVisibility();
    }

    function addCollectionCalendar(calendarData) {
        const calendarSection = document.createElement('div');
        calendarSection.className = 'message bot-message schedule';

        const titleP = document.createElement('p');
        titleP.innerHTML = `<strong>${calendarData.title}</strong>`;
        calendarSection.appendChild(titleP);

        const calendarDiv = document.createElement('div');
        calendarDiv.className = 'collection-calendar';

        const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        daysOfWeek.forEach(day => {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'calendar-day day-header';
            dayDiv.textContent = day;
            calendarDiv.appendChild(dayDiv);
        });

        const today = new Date();
        const currentDay = today.getDate();

        for (let i = 1; i <= calendarData.days; i++) {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'calendar-day';
            if (i === currentDay) {
                dayDiv.classList.add('today');
            }

            dayDiv.textContent = i;

            if (calendarData.collections && calendarData.collections[i]) {
                const wasteType = document.createElement('div');
                wasteType.className = `waste-type ${calendarData.collections[i].toLowerCase()}`;
                wasteType.textContent = calendarData.collections[i];
                dayDiv.appendChild(wasteType);
            }

            calendarDiv.appendChild(dayDiv);
        }

        calendarSection.appendChild(calendarDiv);

        const timestamp = document.createElement('span');
        timestamp.className = 'timestamp';
        const now = new Date();
        timestamp.innerText = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        calendarSection.appendChild(timestamp);

        chatMessages.appendChild(calendarSection);

        if (isScrolledToBottom()) {
            scrollToBottom();
        }

        updateScrollButtonVisibility();
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    if (userInput) {
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';

            if (this.value === '') {
                this.style.height = '';
            }
        });
    }

    if (navToggle) {
        navToggle.addEventListener('click', () => {
            headerNav.classList.toggle('active');
        });
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            chatSidebar.classList.toggle('active');
        });
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');

            const icon = themeToggle.querySelector('i');
            if (document.body.classList.contains('dark-mode')) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        });
    }

    quickActionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const action = button.dataset.action;
            const actionText = button.textContent.trim();
            addMessage(`Show me ${actionText}`, true);

            sendAction(action);
        });
    });

    suggestionsElements.forEach(suggestion => {
        suggestion.addEventListener('click', () => {
            const text = suggestion.dataset.suggestion;
            handleSuggestionClick(text);
        });
    });

    if (scrollBottomBtn) {
        scrollBottomBtn.addEventListener('click', scrollToBottom);
    }

    if (chatMessages) {
        chatMessages.addEventListener('scroll', updateScrollButtonVisibility);
    }

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            if (headerNav) headerNav.classList.remove('active');
            if (chatSidebar && !chatSidebar.classList.contains('active')) {
                chatSidebar.classList.add('active');
            }
        } else {
            if (chatSidebar) chatSidebar.classList.remove('active');
        }
    });

    if (window.innerWidth > 768 && chatSidebar) {
        chatSidebar.classList.add('active');
    }

    updateScrollButtonVisibility();

    scrollToBottom();
});