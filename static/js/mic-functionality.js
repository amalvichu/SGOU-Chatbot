document.addEventListener('DOMContentLoaded', () => {
  const micButton = document.getElementById('mic-button');
  const micIcon = document.getElementById('mic-icon');
  const messageInput = document.getElementById('message-input');

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    if (micButton) micButton.style.display = 'none';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-IN';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  let isListening = false;
  let finalTranscript = '';

  micButton.addEventListener('click', () => {
    if (isListening) {
      recognition.stop();
    } else {
      finalTranscript = '';
      recognition.start();
    }
  });

  recognition.addEventListener('start', () => {
    isListening = true;
    micIcon.textContent = 'mic_off';
    messageInput.placeholder = 'Listening...';

    micButton.classList.add('mic-listening');
    micIcon.classList.add('mic-bounce');

    setTimeout(() => {
      micIcon.classList.remove('mic-bounce');
    }, 500);
  });

  recognition.addEventListener('result', (event) => {
    finalTranscript = event.results[0][0].transcript;
    messageInput.value = finalTranscript;
    console.log('Transcript:', finalTranscript);
  });

  recognition.addEventListener('end', () => {
    isListening = false;
    micIcon.textContent = 'mic';
    messageInput.placeholder = 'Type your message here...';

    micButton.classList.remove('mic-listening');

    console.log('Recognition ended, trying to send message...');
    if (finalTranscript.trim() !== '') {
      if (typeof sendMessage === 'function') {
        console.log('Calling sendMessage() now');
        window.sendMessage();

      } else {
        console.warn('sendMessage() function not found!');
      }
    } else {
      console.log('No transcript to send');
    }
  });

  recognition.addEventListener('error', (event) => {
    console.error('Speech recognition error:', event.error);
    alert(`Mic error: ${event.error}`);
    isListening = false;
    micIcon.textContent = 'mic';
    messageInput.placeholder = 'Type your message here...';
  });
});

recognition.addEventListener('result', (event) => {
  console.log('Speech recognition result:', event);
  const transcript = event.results[0][0].transcript;
  console.log('Transcript:', transcript);
  messageInput.value = transcript;
});
recognition.addEventListener('soundstart', () => {
  console.log('Sound detected');
});
recognition.addEventListener('speechstart', () => {
  console.log('Speech started');
});
recognition.addEventListener('speechend', () => {
  console.log('Speech ended');
});
