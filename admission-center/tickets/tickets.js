
document.addEventListener('DOMContentLoaded', () => {
    let currentTicketId = null;
    let myUserId = null;

    const ticketsList = document.getElementById('ticketsList');
    const chatHeader = document.getElementById('chatHeader');
    const chatInputArea = document.getElementById('chatInputArea');
    const chatMessages = document.getElementById('chatMessages');
    const targetUserSelect = document.getElementById('targetUserSelect');
    const targetRoleSelect = document.getElementById('targetRoleSelect');
    const targetUserSelectContainer = document.getElementById('targetUserSelectContainer');
    const targetSearchContainer = document.getElementById('targetSearchContainer');
    const targetUserSearch = document.getElementById('targetUserSearch');
    const modal = document.getElementById('newTicketModal');

    // Extract user info from session if available
    try {
        const sessionStr = sessionStorage.getItem('ntaTrainee') || sessionStorage.getItem('ntaAdmin') || sessionStorage.getItem('ntaUser') || '{}';
        const session = JSON.parse(sessionStr);
        myUserId = session.userId || session.id;
    } catch(e) {}

    // Modal Handlers
    document.getElementById('newTicketBtn').addEventListener('click', () => {
        modal.style.display = 'flex';
        loadAllowedRoles();
    });
    
    document.getElementById('closeModalBtn').addEventListener('click', () => {
        modal.style.display = 'none';
    });

    const getSessionToken = () => {
        try {
            const sessionStr = sessionStorage.getItem('ntaTrainee') || sessionStorage.getItem('ntaAdmin') || sessionStorage.getItem('ntaUser') || '{}';
            return JSON.parse(sessionStr).token || JSON.parse(sessionStr).access_token || '';
        } catch(e) { return ''; }
    };

    const apiCall = (endpoint, options = {}) => {
        const token = getSessionToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? {'Authorization': `Bearer ${token}`} : {})
        };
        
        return fetch('/api/tickets' + endpoint, {
            ...options,
            headers
        }).then(async r => {
            if(!r.ok) throw new Error(await r.text());
            return r.json();
        });
    };

    let searchTimeout = null;

    const loadAllowedRoles = async () => {
        try {
            const roles = await apiCall('/allowed-roles');
            if (targetRoleSelect) {
                targetRoleSelect.innerHTML = '<option value="" disabled selected>اختر نوع المرسل إليه...</option>';
                roles.forEach(r => {
                    targetRoleSelect.innerHTML += `<option value="${r.role}">${r.label}</option>`;
                });
            }
            if (targetUserSelectContainer) targetUserSelectContainer.style.display = 'none';
            if (targetSearchContainer) targetSearchContainer.style.display = 'none';
            if (targetUserSelect) targetUserSelect.innerHTML = '<option value="">اختر المستخدم...</option>';
            if (targetUserSearch) targetUserSearch.value = '';
        } catch (err) {
            console.error('Error loading roles:', err);
        }
    };

    const loadUsersForRole = async (role, query = '') => {
        try {
            if (targetUserSelect) targetUserSelect.innerHTML = '<option value="">جاري التحميل...</option>';
            const queryParam = query ? `&query=${encodeURIComponent(query)}` : '';
            const targets = await apiCall(`/lookup-users?target_role=${role}${queryParam}`);
            if (targetUserSelect) {
                targetUserSelect.innerHTML = '<option value="">اختر المستخدم...</option>';
                targets.forEach(u => {
                    const name = u.full_name_ar || u.email;
                    targetUserSelect.innerHTML += `<option value="${u.id}|${u.role}">${name}</option>`;
                });
            }
        } catch (err) {
            console.error('Error loading users:', err);
            if (targetUserSelect) targetUserSelect.innerHTML = '<option value="">خطأ في التحميل</option>';
        }
    };

    if (targetRoleSelect) {
        targetRoleSelect.addEventListener('change', (e) => {
            const role = e.target.value;
            if (targetUserSelectContainer) targetUserSelectContainer.style.display = 'block';
            
            if (role === 'trainee') {
                if (targetSearchContainer) targetSearchContainer.style.display = 'block';
            } else {
                if (targetSearchContainer) targetSearchContainer.style.display = 'none';
            }
            
            if (targetUserSearch) targetUserSearch.value = '';
            loadUsersForRole(role);
        });
    }

    if (targetUserSearch) {
        targetUserSearch.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value;
            const role = targetRoleSelect.value;
            searchTimeout = setTimeout(() => {
                if (role) loadUsersForRole(role, query);
            }, 400);
        });
    }

    const loadTickets = async () => {
        try {
            const tickets = await apiCall('/');
            ticketsList.innerHTML = '';
            if (!tickets || tickets.length === 0) {
                ticketsList.innerHTML = '<div class="empty-state">لا توجد تذاكر حالية.</div>';
                return;
            }
            
            tickets.forEach(t => {
                // If I am the initiator, the other person is the receiver.
                const otherName = (t.initiator_name && !t.receiver_name) ? t.initiator_name : (t.receiver_name || t.initiator_name);
                const date = new Date(t.updated_at).toLocaleDateString('ar-EG');
                
                const div = document.createElement('div');
                div.className = `ticket-item ${currentTicketId === t.id ? 'active' : ''}`;
                div.innerHTML = `
                    <div class="ticket-item-subject">${t.subject}</div>
                    <div class="ticket-item-meta">
                        <span>مع: ${otherName}</span>
                        <span>${date}</span>
                    </div>
                `;
                div.onclick = () => openTicket(t.id, t.subject, t.status);
                ticketsList.appendChild(div);
            });
        } catch (err) {
            ticketsList.innerHTML = '<div class="empty-state">فشل تحميل التذاكر.</div>';
        }
    };

    const openTicket = async (id, subject, status) => {
        currentTicketId = id;
        document.getElementById('chatSubject').textContent = subject;
        const statusEl = document.getElementById('chatStatus');
        statusEl.textContent = status === 'Open' ? 'مفتوحة' : (status === 'Closed' ? 'مغلقة' : 'قيد المعالجة');
        statusEl.className = `status-badge ${status === 'Closed' ? 'closed' : ''}`;
        
        chatHeader.style.display = 'flex';
        chatInputArea.style.display = status === 'Closed' ? 'none' : 'flex';
        
        document.querySelectorAll('.ticket-item').forEach(el => el.classList.remove('active'));
        
        try {
            const messages = await apiCall(`/${id}`);
            chatMessages.innerHTML = '';
            messages.forEach(m => {
                const date = new Date(m.created_at).toLocaleString('ar-EG', {hour: '2-digit', minute:'2-digit'});
                const isSent = myUserId ? m.sender_id == myUserId : m.sender_name.includes("أنا"); 
                
                const div = document.createElement('div');
                div.className = `message-bubble ${isSent ? 'message-sent' : 'message-received'}`;
                div.innerHTML = `
                    <div>${m.message_text.replace(/\n/g, '<br>')}</div>
                    <span class="message-meta">${m.sender_name} - ${date}</span>
                `;
                chatMessages.appendChild(div);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (err) {
            chatMessages.innerHTML = '<div class="empty-state">فشل تحميل الرسائل.</div>';
        }
    };

    document.getElementById('submitTicketBtn').addEventListener('click', async () => {
        const targetVal = targetUserSelect.value;
        const subject = document.getElementById('ticketSubject').value.trim();
        const msg = document.getElementById('ticketMessage').value.trim();
        
        if(!targetVal || !subject || !msg) {
            alert('يرجى ملء كافة الحقول');
            return;
        }
        
        const [receiver_id, receiver_role] = targetVal.split('|');
        try {
            await apiCall('/', {
                method: 'POST',
                body: JSON.stringify({
                    subject,
                    receiver_id: parseInt(receiver_id),
                    receiver_role,
                    initial_message: msg
                })
            });
            modal.style.display = 'none';
            document.getElementById('ticketSubject').value = '';
            document.getElementById('ticketMessage').value = '';
            loadTickets();
        } catch(e) {
            alert('حدث خطأ أثناء الإنشاء');
        }
    });

    document.getElementById('sendReplyBtn').addEventListener('click', async () => {
        if(!currentTicketId) return;
        const msgInput = document.getElementById('replyMessage');
        const msg = msgInput.value.trim();
        if(!msg) return;
        
        try {
            await apiCall(`/${currentTicketId}/messages`, {
                method: 'POST',
                body: JSON.stringify({ message_text: msg })
            });
            msgInput.value = '';
            openTicket(currentTicketId, document.getElementById('chatSubject').textContent, 'Open');
        } catch(e) {
            alert('حدث خطأ أثناء الإرسال');
        }
    });

    loadTickets();
});
