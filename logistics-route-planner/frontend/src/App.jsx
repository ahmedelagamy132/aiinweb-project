// Application shell for the Logistics Route Planner.
//
// Each feature is organized in its own folder under `src/features`.
// New features follow the same pattern: create a hook for stateful logic
// and pass it into a presentational component.


import './App.css';
import { AgentPanel } from './features/agent/components/AgentPanel';
import { useAgent } from './features/agent/hooks/useAgent';
import { EchoForm } from './features/echo/components/EchoForm';
import { useEchoForm } from './features/echo/hooks/useEchoForm';
import { PlannerPanel } from './features/planner/components/PlannerPanel';
import { usePlanner } from './features/planner/hooks/usePlanner';
import { SearchPanel } from './features/search/components/SearchPanel';
import { ChatbotPanel } from './features/chatbot/components/ChatbotPanel';
import NavBar from './components/NavBar';
import React, { useState } from 'react';
import { Package, History, Truck } from 'lucide-react';


function App() {
    const agent = useAgent();
    const echoForm = useEchoForm();
    const planner = usePlanner();
    const [activeTab, setActiveTab] = useState('agent');

    let content;
    if (activeTab === 'agent') {
        content = (
            <section className="card card-featured animate-in">
                <AgentPanel {...agent} />
            </section>
        );
    } else if (activeTab === 'echo') {
        content = (
            <section className="card animate-in">
                <div className="card-header">
                    <h2><Package size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Retrying Echo Service</h2>
                    <p>Test the retry mechanism with a flaky echo service.</p>
                </div>
                <EchoForm {...echoForm} />
            </section>
        );
    } else if (activeTab === 'planner') {
        content = (
            <section className="card animate-in">
                <PlannerPanel {...planner} />
            </section>
        );
    } else if (activeTab === 'search') {
        content = (
            <section className="card card-featured animate-in">
                <SearchPanel />
            </section>
        );
    } else if (activeTab === 'chatbot') {
        content = (
            <section className="card card-featured animate-in">
                <ChatbotPanel />
            </section>
        );
    } else if (activeTab === 'history') {
        content = (
            <section className="card animate-in">
                <div className="card-header">
                    <h2><History size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Recent Runs History</h2>
                    <p>View past agent runs and planner executions.</p>
                </div>
                <HistoryPanel />
            </section>
        );
    }

    return (
        <div className="app-layout">
            <NavBar activeTab={activeTab} onTabChange={setActiveTab} />
            <div className="main-content">
                <header className="app-header animate-in">
                    <h1><Truck size={32} style={{ display: 'inline-block', marginRight: '12px', verticalAlign: 'middle' }} />Logistics Route Planner</h1>
                    <p>
                        AI-powered route planning with Gemini/Groq and RAG. Analyze routes, get recommendations,
                        and track delivery readiness with intelligent insights.
                    </p>
                </header>
                <div className="content-area">
                    {content}
                </div>
            </div>
        </div>
    );
}

// Simple History Panel component
function HistoryPanel() {
    const [agentHistory, setAgentHistory] = React.useState([]);
    const [plannerHistory, setPlannerHistory] = React.useState([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        async function loadHistory() {
            try {
                const [agentRes, plannerRes] = await Promise.all([
                    fetch('/api/ai/history?limit=10'),
                    fetch('/api/planner/route/history')
                ]);
                
                if (agentRes.ok) {
                    const agentData = await agentRes.json();
                    setAgentHistory(agentData.runs || []);
                }
                
                if (plannerRes.ok) {
                    const plannerData = await plannerRes.json();
                    setPlannerHistory(plannerData || []);
                }
            } catch (err) {
                console.error('Failed to load history:', err);
            } finally {
                setLoading(false);
            }
        }
        loadHistory();
    }, []);

    if (loading) {
        return <div className="text-secondary">Loading history...</div>;
    }

    return (
        <div>
            <div style={{ marginBottom: '2rem' }}>
                <h3>🤖 Agent Runs ({agentHistory.length})</h3>
                {agentHistory.length === 0 ? (
                    <p className="text-secondary">No agent runs yet</p>
                ) : (
                    <div className="history-list">
                        {agentHistory.map((run) => (
                            <div key={run.id} className="history-item">
                                <div className="history-header">
                                    <strong>{run.route_slug}</strong>
                                    <span className="text-secondary">
                                        {new Date(run.created_at).toLocaleString()}
                                    </span>
                                </div>
                                <p className="text-secondary">
                                    {run.audience_role} • {run.summary}
                                </p>
                                {run.gemini_insight && (
                                    <div className="insight-badge">
                                        💡 AI Insight: {run.gemini_insight.substring(0, 100)}...
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div>
                <h3>📍 Planner Runs ({plannerHistory.length})</h3>
                {plannerHistory.length === 0 ? (
                    <p className="text-secondary">No planner runs yet</p>
                ) : (
                    <div className="history-list">
                        {plannerHistory.map((run) => (
                            <div key={run.id} className="history-item">
                                <div className="history-header">
                                    <strong>{run.goal}</strong>
                                    <span className="text-secondary">
                                        {new Date(run.created_at).toLocaleString()}
                                    </span>
                                </div>
                                <p className="text-secondary">
                                    {run.audience_role} ({run.audience_experience}) • {run.summary}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
