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
  const lang = langSelect.value;
  if (!message) return;
  appendMessage(message, 'user');
  msgInput.value = '';
  setTyping(true);

  // Send message to backend
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        encounter_id: 1, // Replace with actual encounter_id if available
        locale: lang,
        text: message
      })
    });
    const data = await response.json();

    // Hide typing indicator
    setTyping(false);

    // Show bot response
    appendMessage(data.disposition || "Sorry, I didn't understand.");

    // Show next questions if any
    if (data.questions_next && data.questions_next.length > 0) {
      data.questions_next.forEach(q => appendMessage(q));
    }

    // Show triage level
    if (data.triage_level) {
      appendMessage(`Triage Level: ${data.triage_level}`);
    }

    // Show telemedicine link
    if (data.telemedicine && data.telemedicine.url) {
      appendMessage(`<a href="${data.telemedicine.url}" target="_blank">${data.telemedicine.label}</a>`);
    }
  } catch (err) {
    console.error(err);
    showError("Server error. Try again.");
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
