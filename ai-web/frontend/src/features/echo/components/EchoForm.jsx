// Presentational component responsible for rendering the echo form and results.
//
// The component receives all state and handlers from the `useEchoForm` hook so it
// can focus on markup and teaching-friendly comments.
import PropTypes from 'prop-types';

export function EchoForm({
  msg,
  setMsg,
  handleSubmit,
  loading,
  error,
  response,
  history,
}) {
  return (
    <div>
      <div className="mb-lg">
        <p className="text-secondary">
          This form mirrors the curriculum&apos;s feature-folder layout. Submit a message to see
          how the frontend retries the flaky endpoint before succeeding.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="msg">Message to echo</label>
          <input
            type="text"
            id="msg"
            value={msg}
            onChange={(event) => setMsg(event.target.value)}
            disabled={loading}
            placeholder="Enter your message..."
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Sending…' : 'Send'}
        </button>
      </form>
      {error && <div className="alert alert-error">{error}</div>}
      {response && (
        <div className="content-box">
          <h3>Server response</h3>
          <pre>{response}</pre>
        </div>
      )}
      <div className="content-box">
        <h3>Recent echo attempts</h3>
        <p className="text-secondary mb-md">Persistence is handled by Postgres + Alembic migrations.</p>
        <ul className="list">
          {history.map((row) => (
            <li key={row.id} className="list-item">
              <strong>{row.msg}</strong>
              <div className="text-secondary">
                Failures: {row.failures} • Attempts: {row.attempts}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

EchoForm.propTypes = {
  msg: PropTypes.string.isRequired,
  setMsg: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string.isRequired,
  response: PropTypes.string.isRequired,
  history: PropTypes.arrayOf(PropTypes.object).isRequired,
};
