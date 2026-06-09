; (function () {
    document.addEventListener('DOMContentLoaded', function () {
        var container = document.getElementById('chatWidget');
        if (!container) {
            container = document.createElement('div');
            container.id = 'chatWidget';
            document.body.appendChild(container);
        }

        if (container.dataset.chatInitialized === '1') return;

        container.innerHTML = `
            <button type="button" class="chat-fab" id="chatFab" aria-label="مساعد المحادثة">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M8 10h.01M12 10h.01M16 10h.01M21 11.5A8.38 8.38 0 0112.5 20 8.38 8.38 0 014 11.5 8.38 8.38 0 0112.5 3 8.38 8.38 0 0121 11.5z"/>
                </svg>
            </button>
            <div class="chat-dialog-backdrop" id="chatDialog">
                <div class="chat-dialog">
                    <div class="chat-dialog__header">
                        <div>
                            <div class="chat-dialog__title">مساعد الأكاديمية</div>
                            <div class="chat-dialog__subtitle">اسأل عن الدورات أو حالتك</div>
                        </div>
                        <button type="button" class="chat-dialog__close" id="chatCloseBtn">✕</button>
                    </div>
                    <div class="chat-dialog__body" id="chatBody">
                        <div class="chat-dialog__bubble chat-dialog__bubble--bot">
                            أهلاً بك، سأكون متاحاً لمساعدتك قريباً.
                        </div>
                    </div>
                    <div class="chat-dialog__footer">
                        <input type="text" class="chat-dialog__input" id="chatInput" placeholder="اكتب سؤالك هنا..." />
                        <button type="button" class="chat-dialog__send" id="chatSendBtn">إرسال</button>
                    </div>
                </div>
            </div>`;

        container.dataset.chatInitialized = '1';

        const chatFab = document.getElementById('chatFab');
        const chatDialog = document.getElementById('chatDialog');
        const chatInput = document.getElementById('chatInput');
        const chatBody = document.getElementById('chatBody');
        const chatCloseBtn = document.getElementById('chatCloseBtn');
        const chatSendBtn = document.getElementById('chatSendBtn');

        function addBubble(text, isBot = false) {
            const bubble = document.createElement('div');
            bubble.className = `chat-dialog__bubble ${isBot ? 'chat-dialog__bubble--bot' : 'chat-dialog__bubble--user'}`;
            bubble.textContent = text;
            chatBody.appendChild(bubble);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function showTyping() {
            const typing = document.createElement('div');
            typing.id = 'chatTyping';
            typing.className = 'chat-dialog__bubble chat-dialog__bubble--bot chat-typing';
            typing.innerHTML = '<span>.</span><span>.</span><span>.</span>';
            chatBody.appendChild(typing);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function removeTyping() {
            const typing = document.getElementById('chatTyping');
            if (typing) typing.remove();
        }

        async function loadHistory() {
            const session = JSON.parse(sessionStorage.getItem('ntaTrainee') || '{}');
            const isGuest = !session.token;

            if (isGuest) {
                const guestHistory = JSON.parse(sessionStorage.getItem('ntaChatGuestHistory') || '[]');
                if (guestHistory.length > 0) {
                    chatBody.innerHTML = '';
                    guestHistory.forEach(item => {
                        addBubble(item.question, false);
                        addBubble(item.reply, true);
                    });
                }
                return;
            }

            try {
                // For logged in users, fetch from DB
                const res = await window.authenticatedFetch('/api/chat/history', { skipRedirect: true });
                if (res.ok) {
                    const history = await res.json();
                    if (history && history.length > 0) {
                        chatBody.innerHTML = ''; 
                        history.forEach(item => {
                            addBubble(item.question, false);
                            addBubble(item.reply, true);
                        });
                    }
                }
            } catch (err) {
                console.error("Failed to load chat history:", err);
            }
        }

        async function sendMessage() {
            const text = chatInput.value.trim();
            if (!text) return;

            addBubble(text, false);
            chatInput.value = '';
            showTyping();

            try {
                const response = await window.authenticatedFetch('/api/chat/ask', {
                    method: 'POST',
                    body: JSON.stringify({ question: text }),
                    skipRedirect: true
                });
                
                removeTyping();
                
                if (response.ok) {
                    const data = await response.json();
                    if (data && data.reply) {
                        addBubble(data.reply, true);
                        
                        // Save to session storage if guest
                        const session = JSON.parse(sessionStorage.getItem('ntaTrainee') || '{}');
                        if (!session.token) {
                            const guestHistory = JSON.parse(sessionStorage.getItem('ntaChatGuestHistory') || '[]');
                            guestHistory.push({ question: text, reply: data.reply });
                            sessionStorage.setItem('ntaChatGuestHistory', JSON.stringify(guestHistory));
                        }
                    }
                } else if (response.status === 429) {
                    addBubble("لقد تجاوزت حد الأسئلة المسموح به حالياً. يرجى الانتظار قليلاً.", true);
                } else {
                    addBubble("عذراً، حدث خطأ في معالجة طلبك.", true);
                }
            } catch (err) {
                removeTyping();
                addBubble("عذراً، حدث خطأ في الاتصال. يرجى المحاولة لاحقاً.", true);
            }
        }

        chatFab.addEventListener('click', () => {
            chatDialog.classList.toggle('is-open');
            if (chatDialog.classList.contains('is-open')) {
                chatInput.focus();
                loadHistory();
            }
        });

        chatCloseBtn.addEventListener('click', () => chatDialog.classList.remove('is-open'));
        chatSendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    });
})();
