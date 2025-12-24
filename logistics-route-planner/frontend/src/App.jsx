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

function App() {
    const agent = useAgent();
    const echoForm = useEchoForm();
    const planner = usePlanner();

    return (
        <div className="app-container">
            <header className="app-header animate-in">
                <h1>🚚 Logistics Route Planner Launch Assistant</h1>
                <p>
                    AI-powered route planning with Gemini and RAG. Analyze routes, get recommendations,
                    and track delivery readiness with intelligent insights.
                </p>
            </header>

            <div className="grid">
                {/* Featured: Route Readiness Agent with Gemini + RAG */}
                <section className="card card-featured animate-in">
                    <AgentPanel {...agent} />
                </section>

                <section className="card animate-in">
                    <div className="card-header">
                        <h2>📦 Retrying Echo Service</h2>
                        <p>Test the retry mechanism with a flaky echo service.</p>
                    </div>
                    <EchoForm {...echoForm} />
                </section>

                <section className="card animate-in">
                    <PlannerPanel {...planner} />
                </section>
            </div>
        </div>
    );
}

export default App;
