const chatBody   = document.getElementById('chatBody');
const msgInput   = document.getElementById('msgInput');
const btnSend    = document.getElementById('btnSend');
const btnRefer   = document.getElementById('btnRefer');
const btnMic     = document.getElementById('btnMic');
const typingEl   = document.getElementById('typing');
const langSelect = document.getElementById('langSelect');

// Bootstrap toast
const toast = new bootstrap.Toast(document.getElementById('toast'));
function showError(msg) {
  document.getElementById('toastMsg').textContent = msg || 'Something went wrong.';
  toast.show();
}

// Append chat message
function appendMessage(text, who = 'bot') {
  const wrap = document.createElement('div');
  wrap.className = 'message ' + (who === 'user' ? 'from-user' : 'from-bot');
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.innerHTML = who === 'user' ? '<i class="bi bi-person"></i>' : '<i class="bi bi-robot"></i>';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  chatBody.appendChild(wrap);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function setTyping(on) { typingEl.style.display = on ? 'block' : 'none'; }

// Send message
async function sendMessage() {
  const message = msgInput.value.trim();
  if (!message) return;
  appendMessage(message, 'user');
  msgInput.value = '';
  setTyping(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, lang: langSelect.value })
    });
    if (!res.ok) throw new Error('API error: ' + res.status);
    const data = await res.json();
    appendMessage(data.response || '…');
  } catch (err) {
    console.error(err);
    showError('Failed to send message. Check server.');
  } finally {
    setTyping(false);
  }
}

// Telemedicine referral
async function referToDoctor() {
  try {
    const res = await fetch('/api/telemedicine/referral', { method: 'GET' });
    if (!res.ok) throw new Error('Referral API error');
    const data = await res.json();
    const url = data.link || 'https://esanjeevani.mohfw.gov.in/';
    window.location.href = url;
  } catch (err) {
    console.error(err);
    window.location.href = 'https://esanjeevani.mohfw.gov.in/';
  }
}

// Mic → /api/transcribe
async function transcribeOnce() {
  try {
    const res = await fetch('/api/transcribe', { method: 'POST' });
    if (!res.ok) throw new Error('Transcription failed');
    const data = await res.json();
    if (data.text) {
      msgInput.value = data.text;
      msgInput.focus();
    } else {
      showError('No speech recognized.');
    }
  } catch (e) {
    console.error(e);
    showError('Mic/Transcription error.');
  }
}

// Events
btnSend.addEventListener('click', sendMessage);
msgInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
btnRefer.addEventListener('click', referToDoctor);
btnMic.addEventListener('click', transcribeOnce);
langSelect.addEventListener('change', () => {
  appendMessage(
    langSelect.value === 'hi' ? 'भाषा हिंदी पर सेट की गई है।' :
    langSelect.value === 'ta' ? 'மொழி தமிழ் ஆக மாற்றப்பட்டது.' :
    'Language set to English.'
  );
});
