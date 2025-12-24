import { useMemo } from 'react';
import PropTypes from 'prop-types';
import { Bot, Sparkles, Target, Wrench, BookOpen, FileText } from 'lucide-react';

/**
 * AgentPanel - A comprehensive UI for the route readiness agent.
 *
 * This component demonstrates:
 * - Route selection with dynamic form updates
 * - AI-powered recommendations with Gemini integration
 * - FAISS-based RAG context display
 * - Tool call transparency for debugging
 * - Historical agent runs for auditing
 */
export function AgentPanel({
    routes,
    selectedRoute,
    audienceRole,
    audienceExperience,
    includeRisks,
    launchDate,
    selectRoute,
    setAudienceRole,
    setAudienceExperience,
    setIncludeRisks,
    setLaunchDate,
    runAgent,
    result,
    history,
    pending,
    error,
}) {
    // Memoize the recommendations list for performance
    const recommendationsList = useMemo(
        () =>
            result?.recommended_actions?.map((rec, index) => (
                <li key={index} className="list-item">
                    <div className="recommendation-header">
                        <strong>{rec.title}</strong>
                        <span className={`priority-badge priority-${rec.priority}`}>
                            {rec.priority}
                        </span>
                    </div>
                    <p className="text-secondary">{rec.detail}</p>
                </li>
            )),
        [result?.recommended_actions]
    );

    // Memoize tool calls for transparency view
    const toolCallsList = useMemo(
        () =>
            result?.tool_calls?.map((call, index) => (
                <li key={index} className="list-item tool-call">
                    <code>{call.tool}</code>
                    <span className="text-secondary">{call.output_preview}</span>
                </li>
            )),
        [result?.tool_calls]
    );

    // Memoize RAG contexts
    const ragContextsList = useMemo(
        () =>
            result?.rag_contexts?.map((ctx, index) => (
                <li key={index} className="list-item">
                    <strong>{ctx.source}</strong>
                    <p className="text-secondary">{ctx.content}</p>
                    <small>Score: {ctx.score.toFixed(4)}</small>
                </li>
            )),
        [result?.rag_contexts]
    );

    return (
        <div>
            <div className="card-header">
                <h2><Bot size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Route Readiness Agent</h2>
                <p>
                    AI-powered route assessment using Gemini and RAG retrieval.
                    Select a route and run the agent to get intelligent recommendations.
                </p>
            </div>

            {/* Route Selection Form */}
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    runAgent();
                }}
                className="form"
            >
                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="route">Route</label>
                        <select
                            id="route"
                            value={selectedRoute}
                            onChange={(e) => selectRoute(e.target.value)}
                        >
                            {routes.map((r) => (
                                <option key={r.slug} value={r.slug}>
                                    {r.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="launchDate">Launch Date</label>
                        <input
                            type="date"
                            id="launchDate"
                            value={launchDate}
                            onChange={(e) => setLaunchDate(e.target.value)}
                        />
                    </div>
                </div>

                <div className="form-row">
                    <div className="form-group">
                        <label htmlFor="audienceRole">Audience Role</label>
                        <input
                            type="text"
                            id="audienceRole"
                            value={audienceRole}
                            onChange={(e) => setAudienceRole(e.target.value)}
                            placeholder="e.g., Driver, Fleet Manager"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="audienceExperience">Experience Level</label>
                        <select
                            id="audienceExperience"
                            value={audienceExperience}
                            onChange={(e) => setAudienceExperience(e.target.value)}
                        >
                            <option value="beginner">Beginner</option>
                            <option value="intermediate">Intermediate</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                </div>

                <div className="form-group checkbox-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={includeRisks}
                            onChange={(e) => setIncludeRisks(e.target.checked)}
                        />
                        Include Risk Analysis
                    </label>
                </div>

                <button type="submit" disabled={pending || !selectedRoute}>
                    {pending ? 'Running Agent...' : 'Run Route Readiness Agent'}
                </button>
            </form>

            {error && <div className="alert alert-error">{error}</div>}

            {/* Results Section */}
            {result && (
                <div className="agent-results">
                    {/* Summary */}
                    <div className="content-box">
                        <h3>📋 Summary</h3>
                        <p>{result.summary}</p>
                    </div>

                    {/* Gemini AI Insight */}
                    {result.gemini_insight && (
                        <div className="content-box gemini-insight">
                            <h3>
                                <Sparkles size={20} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />
                                AI Insight
                                {result.used_gemini ? (
                                    <span className="badge">Powered by Gemini</span>
                                ) : (
                                    <span className="badge badge-secondary">Offline</span>
                                )}
                            </h3>
                            <p>{result.gemini_insight}</p>
                        </div>
                    )}

                    {/* Recommendations */}
                    <div className="content-box">
                        <h3><Target size={20} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Recommendations ({result.recommended_actions?.length || 0})</h3>
                        <ul className="list recommendations-list">{recommendationsList}</ul>
                    </div>

                    {/* Tool Calls - Transparency */}
                    <div className="content-box">
                        <h3><Wrench size={20} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Tool Calls</h3>
                        <ul className="list tool-calls-list">{toolCallsList}</ul>
                    </div>

                    {/* RAG Contexts */}
                    {result.rag_contexts?.length > 0 && (
                        <div className="content-box">
                            <h3><BookOpen size={20} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Retrieved Context (RAG)</h3>
                            <ul className="list">{ragContextsList}</ul>
                        </div>
                    )}

                    {/* Plan Steps Preview */}
                    {result.plan?.steps?.length > 0 && (
                        <div className="content-box">
                            <h3><FileText size={20} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Generated Plan ({result.plan.steps.length} steps)</h3>
                            <ul className="list">
                                {result.plan.steps.slice(0, 3).map((step, index) => (
                                    <li key={index} className="list-item">
                                        <strong>{step.title}</strong>
                                        <p className="text-secondary">{step.description}</p>
                                    </li>
                                ))}
                                {result.plan.steps.length > 3 && (
                                    <li className="list-item text-secondary">
                                        ...and {result.plan.steps.length - 3} more steps
                                    </li>
                                )}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

AgentPanel.propTypes = {
    routes: PropTypes.arrayOf(PropTypes.object).isRequired,
    selectedRoute: PropTypes.string.isRequired,
    audienceRole: PropTypes.string.isRequired,
    audienceExperience: PropTypes.string.isRequired,
    includeRisks: PropTypes.bool.isRequired,
    launchDate: PropTypes.string.isRequired,
    selectRoute: PropTypes.func.isRequired,
    setAudienceRole: PropTypes.func.isRequired,
    setAudienceExperience: PropTypes.func.isRequired,
    setIncludeRisks: PropTypes.func.isRequired,
    setLaunchDate: PropTypes.func.isRequired,
    runAgent: PropTypes.func.isRequired,
    result: PropTypes.object,
    history: PropTypes.arrayOf(PropTypes.object).isRequired,
    pending: PropTypes.bool.isRequired,
    error: PropTypes.string.isRequired,
};
