const chatBody = document.getElementById('chatBody');
const msgInput = document.getElementById('msgInput');
const btnSend = document.getElementById('btnSend');
const btnRefer = document.getElementById('btnRefer');
const btnMic = document.getElementById('btnMic');
const typingEl = document.getElementById('typing');
const langSelect = document.getElementById('langSelect');

// Bootstrap toast
const toast = new bootstrap.Toast(document.getElementById('toast'));
function showError(msg) {
  document.getElementById('toastMsg').textContent = msg || 'Something went wrong.';
  toast.show();
}

// Text-to-Speech
function speakBotResponse(text) {
  const synth = window.speechSynthesis;
  if (!synth || typeof SpeechSynthesisUtterance === 'undefined') {
    showError('Text-to-speech is not supported in this browser.');
    return;
  }
  try {
    let utter = new SpeechSynthesisUtterance(text);
    const lang = langSelect.value === 'hi' ? 'hi-IN' : 'en-US';
    utter.lang = lang;
    synth.speak(utter);
  } catch (err) {
    showError('Failed to speak response.');
  }
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
  bubble.innerHTML = text;
  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  chatBody.appendChild(wrap);
  chatBody.scrollTop = chatBody.scrollHeight;
  // Always speak bot response
  if (who === 'bot') {
    console.log('Speaking bot response:', text);
    speakBotResponse(text);
  }
}

function setTyping(on) { typingEl.style.display = on ? 'block' : 'none'; }

// Send message
async function sendMessage() {
  let message = msgInput.value.trim();
  const lang = langSelect.value;
  if (!message) return;
  let displayMessage = message;
  // If Hindi, translate input to English for backend
  if (lang === 'hi') {
    try {
      setTyping(true);
      const res = await fetch('https://libretranslate.de/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          q: message,
          source: 'hi',
          target: 'en',
          format: 'text'
        })
      });
      const data = await res.json();
      message = data.translatedText || message;
    } catch (err) {
      showError('Input translation error. Processing original text.');
    }
  }
  appendMessage(displayMessage, 'user');
  msgInput.value = '';
  setTyping(true);

  // Send message to backend
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        encounter_id: encounterId,
        locale: lang,
        text: message
      })
    });
    let data = await response.json();

    // Hide typing indicator
    setTyping(false);

    // If Hindi, translate output to Hindi before displaying
    async function translateToHindi(text) {
      try {
        const res = await fetch('https://libretranslate.de/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            q: text,
            source: 'en',
            target: 'hi',
            format: 'text'
          })
        });
        const result = await res.json();
        return result.translatedText || text;
      } catch (err) {
        showError('Output translation error. Showing original text.');
        return text;
      }
    }

    if (lang === 'hi') {
      // Translate disposition
      if (data.disposition) {
        data.disposition = await translateToHindi(data.disposition);
      }
      // Translate questions_next
      if (data.questions_next && data.questions_next.length > 0) {
        for (let i = 0; i < data.questions_next.length; i++) {
          data.questions_next[i] = await translateToHindi(data.questions_next[i]);
        }
      }
      // Translate triage_level
      if (data.triage_level) {
        data.triage_level = await translateToHindi(`Triage Level: ${data.triage_level}`);
      }
      // Translate telemedicine label
      if (data.telemedicine && data.telemedicine.label) {
        data.telemedicine.label = await translateToHindi(data.telemedicine.label);
      }
    }

    // Show bot response
    appendMessage(data.disposition || "Sorry, I didn't understand.");

    // Show next questions if any
    if (data.questions_next && data.questions_next.length > 0) {
      data.questions_next.forEach(q => appendMessage(q));
    }

    // Show triage level
    if (data.triage_level) {
      appendMessage(data.triage_level);
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
function transcribeOnce() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    showError('Speech recognition not supported in this browser.');
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  recognition.lang = langSelect.value || 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  setTyping(true);
  recognition.onresult = async function (event) {
    let transcript = event.results[0][0].transcript;
    if (langSelect.value === 'hi') {
      // Translate to Hindi using LibreTranslate API
      try {
        setTyping(true);
        const res = await fetch('https://libretranslate.de/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            q: transcript,
            source: 'en',
            target: 'hi',
            format: 'text'
          })
        });
        const data = await res.json();
        transcript = data.translatedText || transcript;
      } catch (err) {
        showError('Translation error. Showing original text.');
      }
    }
    msgInput.value = transcript;
    msgInput.focus();
    setTyping(false);
    lastInputWasAudio = true;
    console.log('Audio input received:', transcript);
  };
  recognition.onerror = function (event) {
    showError('Mic/Transcription error: ' + event.error);
    setTyping(false);
  };
  recognition.onend = function () {
    setTyping(false);
  };
  recognition.start();
}

let encounterId = null;

window.onload = async function() {
  const res = await fetch('/api/start_encounter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ locale: langSelect.value })
  });
  const data = await res.json();
  encounterId = data.encounter_id;
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
