import PropTypes from 'prop-types';

/**
 * PlannerPanel - Route planning form and results display.
 */
export function PlannerPanel({
    goal,
    setGoal,
    audienceRole,
    setAudienceRole,
    audienceExperience,
    setAudienceExperience,
    primaryRisk,
    setPrimaryRisk,
    plan,
    pending,
    error,
    submit,
}) {
    return (
        <div>
            <div className="card-header">
                <h2>📍 Route Planner</h2>
                <p>Generate structured route plans for your logistics operations.</p>
            </div>

            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    submit();
                }}
                className="form"
            >
                <div className="form-group">
                    <label htmlFor="plannerGoal">Goal</label>
                    <input
                        type="text"
                        id="plannerGoal"
                        value={goal}
                        onChange={(e) => setGoal(e.target.value)}
                        placeholder="e.g., Optimize express delivery route"
                    />
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="plannerRole">Audience Role</label>
                        <input
                            type="text"
                            id="plannerRole"
                            value={audienceRole}
                            onChange={(e) => setAudienceRole(e.target.value)}
                            placeholder="e.g., Driver"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="plannerExperience">Experience Level</label>
                        <select
                            id="plannerExperience"
                            value={audienceExperience}
                            onChange={(e) => setAudienceExperience(e.target.value)}
                        >
                            <option value="beginner">Beginner</option>
                            <option value="intermediate">Intermediate</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                </div>

                <div className="form-group">
                    <label htmlFor="plannerRisk">Primary Risk (optional)</label>
                    <input
                        type="text"
                        id="plannerRisk"
                        value={primaryRisk}
                        onChange={(e) => setPrimaryRisk(e.target.value)}
                        placeholder="e.g., Traffic congestion during peak hours"
                    />
                </div>

                <button type="submit" disabled={pending}>
                    {pending ? 'Generating Plan...' : 'Generate Route Plan'}
                </button>
            </form>

            {error && <div className="alert alert-error">{error}</div>}

            {plan && (
                <div className="content-box">
                    <h3>📋 Generated Plan: {plan.goal}</h3>
                    <p className="text-secondary">
                        For {plan.audience.role} ({plan.audience.experience_level}) •
                        Version {plan.version}
                    </p>

                    <div style={{ marginTop: '1rem' }}>
                        <h4>Steps ({plan.steps.length})</h4>
                        <ul className="list">
                            {plan.steps.map((step, index) => (
                                <li key={index} className="list-item">
                                    <div className="recommendation-header">
                                        <strong>{step.title}</strong>
                                        <span className="badge badge-secondary">
                                            {step.duration_minutes} min
                                        </span>
                                    </div>
                                    <p className="text-secondary">{step.description}</p>
                                    <small>Owner: {step.owner}</small>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {plan.risks?.length > 0 && (
                        <div style={{ marginTop: '1rem' }}>
                            <h4>⚠️ Risks</h4>
                            <ul className="list">
                                {plan.risks.map((risk, index) => (
                                    <li key={index} className="list-item text-secondary">
                                        {risk}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

PlannerPanel.propTypes = {
    goal: PropTypes.string.isRequired,
    setGoal: PropTypes.func.isRequired,
    audienceRole: PropTypes.string.isRequired,
    setAudienceRole: PropTypes.func.isRequired,
    audienceExperience: PropTypes.string.isRequired,
    setAudienceExperience: PropTypes.func.isRequired,
    primaryRisk: PropTypes.string.isRequired,
    setPrimaryRisk: PropTypes.func.isRequired,
    plan: PropTypes.object,
    pending: PropTypes.bool.isRequired,
    error: PropTypes.string.isRequired,
    submit: PropTypes.func.isRequired,
};
