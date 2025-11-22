import PropTypes from 'prop-types';

export function PlannerPanel({ payload, plan, history, loading, error, updateField, submit }) {
  return (
    <section style={{ display: 'grid', gap: 12 }}>
      <header>
        <h2>Launch plan generator</h2>
        <p>Calls the FastAPI planner endpoint and stores results in Postgres.</p>
      </header>

      <form onSubmit={submit} style={{ display: 'grid', gap: 8, maxWidth: 520 }}>
        <label htmlFor="goal">Goal</label>
        <input id="goal" value={payload.goal} onChange={(e) => updateField('goal', e.target.value)} />

        <label htmlFor="role">Audience role</label>
        <input id="role" value={payload.audience_role} onChange={(e) => updateField('audience_role', e.target.value)} />

        <label htmlFor="experience">Experience</label>
        <select
          id="experience"
          value={payload.audience_experience}
          onChange={(e) => updateField('audience_experience', e.target.value)}
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>

        <label htmlFor="risk">Primary risk</label>
        <input id="risk" value={payload.primary_risk} onChange={(e) => updateField('primary_risk', e.target.value)} />

        <button type="submit" disabled={loading}>{loading ? 'Generating…' : 'Generate plan'}</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>

      {plan && (
        <article style={{ border: '1px solid #ddd', padding: 12, borderRadius: 8 }}>
          <h3>Latest plan</h3>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(plan, null, 2)}</pre>
        </article>
      )}

      <article>
        <h3>Recent plans</h3>
        <ul style={{ display: 'grid', gap: 8, paddingInlineStart: 16 }}>
          {history.map((item) => (
            <li key={item.id}>
              <strong>{item.goal}</strong> — {item.audience_role} ({item.audience_experience})
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}

PlannerPanel.propTypes = {
  payload: PropTypes.object.isRequired,
  plan: PropTypes.object,
  history: PropTypes.arrayOf(PropTypes.object).isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string.isRequired,
  updateField: PropTypes.func.isRequired,
  submit: PropTypes.func.isRequired,
};

PlannerPanel.defaultProps = {
  plan: null,
};

