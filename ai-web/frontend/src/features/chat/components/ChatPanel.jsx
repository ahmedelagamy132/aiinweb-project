import { useMemo, useState } from 'react';
import PropTypes from 'prop-types';

export function ChatPanel({ messages, contexts, steps, pending, error, onSend }) {
  const [draft, setDraft] = useState('How do I run migrations?');

  const contextList = useMemo(
    () => contexts?.map((ctx, index) => (
      <li key={index} className="list-item">
        <strong>{ctx.source}</strong>
        <p className="text-secondary">{ctx.content}</p>
      </li>
    )),
    [contexts],
  );

  return (
    <div>
      <div className="card-header">
        <h2>Chatbot + RAG</h2>
        <p>Retrieves repository context and calls Gemini when available.</p>
      </div>

      <div className="chat-container">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`chat-message ${message.role === 'assistant' ? 'chat-message-assistant' : 'chat-message-user'}`}
          >
            <strong>{message.role === 'assistant' ? 'Assistant' : 'You'}</strong>
            <p>{message.text}</p>
          </div>
        ))}
        {pending && (
          <div className="chat-message chat-message-assistant">
            <span className="loading">Thinking</span>
          </div>
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSend(draft);
          setDraft('');
        }}
        className="form"
      >
        <div className="form-group">
          <label htmlFor="chat">Ask a question</label>
          <textarea
            id="chat"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask about deployments, migrations, or any technical topic..."
            rows={2}
          />
        </div>
        <button type="submit" disabled={pending}>Send</button>
      </form>

      <div className="content-box">
        <h3>Retrieved context</h3>
        <ul className="list">
          {contextList}
        </ul>
      </div>

      <div className="content-box">
        <h3>Agent steps</h3>
        <ul className="list">
          {steps?.map((step, index) => (
            <li key={index} className="list-item">
              <strong>{step.name}</strong>
              <div className="text-secondary">{step.detail}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
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

