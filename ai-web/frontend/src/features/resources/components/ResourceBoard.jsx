import PropTypes from 'prop-types';

export function ResourceBoard({ form, updateForm, submit, resources, loading, error }) {
  return (
    <section style={{ display: 'grid', gap: 16 }}>
      <header>
        <h2>Course resources (DB-backed)</h2>
        <p>Use the form to add a helpful link. Entries persist through Postgres + Alembic.</p>
      </header>

      <form onSubmit={submit} style={{ display: 'grid', gap: 8, maxWidth: 520 }}>
        <label htmlFor="title">Title</label>
        <input id="title" value={form.title} onChange={(e) => updateForm('title', e.target.value)} required />

        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={form.description}
          onChange={(e) => updateForm('description', e.target.value)}
          rows={3}
          required
        />

        <label htmlFor="url">URL</label>
        <input id="url" value={form.url} onChange={(e) => updateForm('url', e.target.value)} required />

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

        <button type="submit" disabled={loading}>{loading ? 'Saving…' : 'Save resource'}</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>

      <div style={{ display: 'grid', gap: 8 }}>
        <h3>Shared links</h3>
        <ul style={{ display: 'grid', gap: 8, paddingInlineStart: 16 }}>
          {resources.map((resource) => (
            <li key={resource.id}>
              <div style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
                <strong>{resource.title}</strong>
                <span>{resource.description}</span>
                <span>Difficulty: {resource.difficulty}</span>
                <a href={resource.url} target="_blank" rel="noreferrer">{resource.url}</a>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
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

