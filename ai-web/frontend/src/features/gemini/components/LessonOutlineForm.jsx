// Presentational component that renders the Gemini lesson outline form.
// Keeps UI concerns separate from data fetching so the hook can focus on state.
import PropTypes from 'prop-types';

/**
 * Render the lesson outline form and its derived UI states.
 *
 * @param {object} props - Values provided by `useLessonOutlineForm`.
 * @param {string} props.topic - Current topic text, kept controlled via state.
 * @param {Function} props.setTopic - Setter that updates the topic field.
 * @param {string[]} props.outline - Outline bullets returned by the backend.
 * @param {boolean} props.loading - Flag that disables inputs while waiting on the API.
 * @param {string|null} props.error - Error message to show when the request fails.
 * @param {Function} props.handleSubmit - Form submit handler injected from the hook.
 */
export function LessonOutlineForm({ topic, setTopic, outline, loading, error, handleSubmit }) {
  return (
    <div>
      <p className="text-secondary mb-lg">
        Generate a quick lesson outline powered by Gemini. Provide a topic, submit
        the form, and discuss the generated talking points with your class.
      </p>

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="topic">Lesson topic</label>
          <input
            type="text"
            id="topic"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="e.g. Building resilient web APIs"
            disabled={loading}
            required
          />
        </div>

        <button type="submit" disabled={loading || !topic.trim()}>
          {loading ? 'Generating outline…' : 'Generate outline'}
        </button>

        {error && (
          <div className="alert alert-error">
            {error}. Confirm the backend has access to <code>GEMINI_API_KEY</code>.
          </div>
        )}

        {outline.length > 0 && (
          <div className="content-box">
            <h3>Generated Outline</h3>
            <ol style={{ paddingInlineStart: '1.5rem', display: 'grid', gap: '0.5rem' }}>
              {outline.map((item, index) => (
                <li key={`${item}-${index}`} style={{ paddingLeft: '0.5rem' }}>
                  {item}
                </li>
              ))}
            </ol>
          </div>
        )}
      </form>
    </div>
  );
}

LessonOutlineForm.propTypes = {
  topic: PropTypes.string.isRequired,
  setTopic: PropTypes.func.isRequired,
  outline: PropTypes.arrayOf(PropTypes.string).isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string,
  handleSubmit: PropTypes.func.isRequired
};

LessonOutlineForm.defaultProps = {
  error: null
};
