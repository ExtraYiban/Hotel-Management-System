/* Room Service chatbot client: quick-reply buttons + Gemini API call. */
(function () {
  const body = document.getElementById('chat-body');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const history = [];

  function csrfToken() {
    const el = document.querySelector('#chat-form input[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
  }

  function scrollDown() {
    body.scrollTop = body.scrollHeight;
    window.scrollTo(0, document.body.scrollHeight);
  }

  function addBubble(text, from) {
    const div = document.createElement('div');
    div.className = 'bubble ' + from;
    const p = document.createElement('p');
    p.textContent = text;
    div.appendChild(p);
    if (from === 'bot') {
      const note = document.createElement('small');
      note.className = 'auto-note';
      note.textContent = 'Pesan Otomatis Asisten Chat';
      div.appendChild(note);
    }
    body.appendChild(div);
    scrollDown();
    return div;
  }

  function addOptions(options) {
    if (!options || !options.length) return;
    const lastBot = [...body.querySelectorAll('.bubble.bot')].pop();
    if (!lastBot) return;
    const wrap = document.createElement('div');
    wrap.className = 'quick-options';
    options.forEach((opt) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'link-option';
      btn.textContent = opt;
      btn.addEventListener('click', () => send(opt));
      wrap.appendChild(btn);
    });
    lastBot.insertBefore(wrap, lastBot.querySelector('.auto-note'));
  }

  function addCards(target, cards) {
    if (!cards || !cards.length || !target) return;
    const wrap = document.createElement('div');
    wrap.className = 'menu-cards';
    cards.forEach((card) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'menu-card';
      const img = document.createElement('img');
      img.src = card.image;
      img.alt = card.label;
      img.loading = 'lazy';
      const label = document.createElement('span');
      label.textContent = card.label;
      btn.appendChild(img);
      btn.appendChild(label);
      btn.addEventListener('click', () => send(card.label));
      wrap.appendChild(btn);
    });
    target.insertBefore(wrap, target.querySelector('.auto-note'));
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'bubble bot';
    div.id = 'typing-bubble';
    div.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
    body.appendChild(div);
    scrollDown();
  }

  function hideTyping() {
    document.getElementById('typing-bubble')?.remove();
  }

  async function send(text) {
    text = (text || '').trim();
    if (!text) return;
    addBubble(text, 'user');
    history.push({ from: 'user', text });
    input.value = '';
    showTyping();
    try {
      const resp = await fetch('api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        body: JSON.stringify({ message: text, history: history.slice(-8) }),
      });
      const data = await resp.json();
      hideTyping();
      const reply = data.reply || 'Maaf, terjadi gangguan. Silakan coba lagi.';
      const botDiv = addBubble(reply, 'bot');
      history.push({ from: 'bot', text: reply });
      if (data.follow_up) {
        const f = document.createElement('div');
        f.className = 'bubble bot';
        f.innerHTML = '';
        const p = document.createElement('p');
        p.textContent = data.follow_up;
        f.appendChild(p);
        const note = document.createElement('small');
        note.className = 'auto-note';
        note.textContent = 'Pesan Otomatis Asisten Chat';
        f.appendChild(note);
        body.appendChild(f);
      }
      // Attach follow-up option buttons to the newest bot bubble.
      const target = [...body.querySelectorAll('.bubble.bot')].pop();
      if (data.options && data.options.length && target) {        const wrap = document.createElement('div');
        wrap.className = 'quick-options';
        data.options.forEach((opt) => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'link-option';
          btn.textContent = opt;
          btn.addEventListener('click', () => send(opt));
          wrap.appendChild(btn);
        });
        target.insertBefore(wrap, target.querySelector('.auto-note'));
        scrollDown();
      }
      addCards(target, data.cards);
      if (data.show_reception && target) {
        void botDiv;
      }
    } catch (err) {
      hideTyping();
      addBubble('Maaf, koneksi terputus. Periksa internet Anda lalu coba lagi.', 'bot');
    }
  }

  document.querySelectorAll('[data-send]').forEach((btn) => {
    btn.addEventListener('click', () => send(btn.getAttribute('data-send')));
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    send(input.value);
  });
})();
