import PropTypes from 'prop-types';

export function ResourceBoard({ form, updateForm, submit, resources, loading, error }) {
  return (
    <div>
      <div className="card-header">
        <h2>Course Resources</h2>
        <p>Use the form to add a helpful link. Entries persist through Postgres + Alembic.</p>
      </div>

      <form onSubmit={submit} className="form">
        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input 
            type="text"
            id="title" 
            value={form.title} 
            onChange={(e) => updateForm('title', e.target.value)} 
            placeholder="Enter resource title..."
            required 
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={form.description}
            onChange={(e) => updateForm('description', e.target.value)}
            placeholder="Describe the resource and why it's helpful..."
            rows={3}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="url">URL</label>
          <input 
            type="url"
            id="url" 
            value={form.url} 
            onChange={(e) => updateForm('url', e.target.value)} 
            placeholder="https://example.com"
            required 
          />
        </div>

        <div className="form-group">
          <label htmlFor="difficulty">Difficulty</label>
          <select
            id="difficulty"
            value={form.difficulty}
            onChange={(e) => updateForm('difficulty', e.target.value)}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Saving…' : 'Save resource'}
        </button>
        {error && <div className="alert alert-error">{error}</div>}
      </form>

      <div className="content-box">
        <h3>Shared links</h3>
        <ul className="list">
          {resources.map((resource) => (
            <li key={resource.id} className="list-item">
              <strong>{resource.title}</strong>
              <p className="text-secondary">{resource.description}</p>
              <div className="flex" style={{ alignItems: 'center', marginTop: '0.5rem' }}>
                <span className={`badge badge-${resource.difficulty}`}>
                  {resource.difficulty}
                </span>
                <a href={resource.url} target="_blank" rel="noreferrer">
                  View Resource →
                </a>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

ResourceBoard.propTypes = {
  form: PropTypes.object.isRequired,
  updateForm: PropTypes.func.isRequired,
  submit: PropTypes.func.isRequired,
  resources: PropTypes.arrayOf(PropTypes.object).isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string.isRequired,
};

