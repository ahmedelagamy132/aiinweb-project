import { useCallback, useState } from 'react';

import { post } from '../../../lib/api';

export function useChatbot() {
  const [messages, setMessages] = useState([]);
  const [contexts, setContexts] = useState([]);
  const [steps, setSteps] = useState([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');

  const send = useCallback(async (text) => {
    if (!text?.trim()) return;
    const question = text.trim();
    setPending(true);
    setError('');
    setMessages((prev) => [...prev, { role: 'user', text: question }]);
    try {
      const result = await post('/chat/', { message: question });
      setMessages((prev) => [...prev, { role: 'assistant', text: result.answer }]);
      setContexts(result.contexts || []);
      setSteps(result.steps || []);
    } catch (err) {
      console.error('Chat request failed', err);
      setError(err.message || 'Unable to reach chatbot');
    } finally {
      setPending(false);
    }
  }, []);

  return { messages, contexts, steps, pending, error, send };
}

