import { useMemo, useState } from 'react';
import PropTypes from 'prop-types';

export function ChatPanel({ messages, contexts, steps, pending, error, onSend }) {
  const [draft, setDraft] = useState('How do I run migrations?');

  const contextList = useMemo(
    () => contexts?.map((ctx, index) => (
      <li key={index}>
        <strong>{ctx.source}</strong>
        <p>{ctx.content}</p>
      </li>
    )),
    [contexts],
  );

  return (
    <section style={{ display: 'grid', gap: 12 }}>
      <header>
        <h2>Chatbot + RAG</h2>
        <p>Retrieves repository context and calls Gemini when available.</p>
      </header>

      <div style={{ display: 'grid', gap: 8, border: '1px solid #ddd', padding: 12, borderRadius: 8 }}>
        {messages.map((message, index) => (
          <div key={index} style={{ textAlign: message.role === 'assistant' ? 'left' : 'right' }}>
            <strong>{message.role === 'assistant' ? 'Assistant' : 'You'}</strong>
            <p>{message.text}</p>
          </div>
        ))}
        {pending && <p>Thinking…</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSend(draft);
          setDraft('');
        }}
        style={{ display: 'grid', gap: 8 }}
      >
        <label htmlFor="chat">Ask a question</label>
        <textarea
          id="chat"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={2}
        />
        <button type="submit" disabled={pending}>Send</button>
      </form>

      <div>
        <h3>Retrieved context</h3>
        <ul style={{ display: 'grid', gap: 8, paddingInlineStart: 16 }}>
          {contextList}
        </ul>
      </div>

      <div>
        <h3>Agent steps</h3>
        <ul style={{ display: 'grid', gap: 8, paddingInlineStart: 16 }}>
          {steps?.map((step, index) => (
            <li key={index}>{step.name}: {step.detail}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

ChatPanel.propTypes = {
  messages: PropTypes.arrayOf(PropTypes.object).isRequired,
  contexts: PropTypes.arrayOf(PropTypes.object).isRequired,
  steps: PropTypes.arrayOf(PropTypes.object).isRequired,
  pending: PropTypes.bool.isRequired,
  error: PropTypes.string.isRequired,
  onSend: PropTypes.func.isRequired,
};

