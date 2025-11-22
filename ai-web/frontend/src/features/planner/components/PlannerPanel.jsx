import PropTypes from 'prop-types';

export function PlannerPanel({ payload, plan, history, loading, error, updateField, submit }) {
  return (
    <div>
      <div className="card-header">
        <h2>Launch Plan Generator</h2>
        <p>Calls the FastAPI planner endpoint and stores results in Postgres.</p>
      </div>

      <form onSubmit={submit} className="form">
        <div className="form-group">
          <label htmlFor="goal">Goal</label>
          <input 
            type="text"
            id="goal" 
            value={payload.goal} 
            onChange={(e) => updateField('goal', e.target.value)} 
            placeholder="e.g., Launch the upgraded stack"
          />
        </div>

        <div className="form-group">
          <label htmlFor="role">Audience role</label>
          <input 
            type="text"
            id="role" 
            value={payload.audience_role} 
            onChange={(e) => updateField('audience_role', e.target.value)} 
            placeholder="e.g., Instructor"
          />
        </div>

        <div className="form-group">
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
        </div>

        <div className="form-group">
          <label htmlFor="risk">Primary risk</label>
          <input 
            type="text"
            id="risk" 
            value={payload.primary_risk} 
            onChange={(e) => updateField('primary_risk', e.target.value)} 
            placeholder="e.g., Student laptops differ from container setup"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Generating…' : 'Generate plan'}
        </button>
        {error && <div className="alert alert-error">{error}</div>}
      </form>

      {plan && (
        <div className="content-box">
          <h3>Latest plan</h3>
          <pre>{JSON.stringify(plan, null, 2)}</pre>
        </div>
      )}

      <div className="content-box">
        <h3>Recent plans</h3>
        <ul className="list">
          {history.map((item) => (
            <li key={item.id} className="list-item">
              <strong>{item.goal}</strong>
              <div className="text-secondary">
                {item.audience_role} • <span className={`badge badge-${item.audience_experience}`}>
                  {item.audience_experience}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
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

