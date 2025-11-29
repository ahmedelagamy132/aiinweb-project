// Application shell responsible for wiring feature modules into the page.
//
// Each lab encourages keeping this component small so students can focus on the
// feature folders under `src/features`. New demos should follow the same
// pattern: create a hook for stateful logic and pass it into a presentational
// component.
import './App.css';
import { EchoForm } from './features/echo/components/EchoForm';
import { useEchoForm } from './features/echo/hooks/useEchoForm';
import { LessonOutlineForm } from './features/gemini/components/LessonOutlineForm';
import { useLessonOutlineForm } from './features/gemini/hooks/useLessonOutlineForm';
import { ResourceBoard } from './features/resources/components/ResourceBoard';
import { useResourceBoard } from './features/resources/hooks/useResourceBoard';
import { PlannerPanel } from './features/planner/components/PlannerPanel';
import { usePlanner } from './features/planner/hooks/usePlanner';
import { ChatPanel } from './features/chat/components/ChatPanel';
import { useChatbot } from './features/chat/hooks/useChatbot';
import { AgentPanel } from './features/agent/components/AgentPanel';
import { useAgent } from './features/agent/hooks/useAgent';

function App() {
  const echoForm = useEchoForm();
  const lessonOutlineForm = useLessonOutlineForm();
  const resourceBoard = useResourceBoard();
  const planner = usePlanner();
  const chatbot = useChatbot();
  const agent = useAgent();

  return (
    <div className="app-container">
      <header className="app-header animate-in">
        <h1>AI in Web Programming Demos</h1>
        <p>
          FastAPI and React layers evolve together. Each section mirrors the workflow documented in the
          instructor guide. Build modern, intelligent web applications with best practices.
        </p>
      </header>

      <div className="grid">
        {/* Featured: Release Readiness Agent with Gemini + RAG */}
        <section className="card card-featured animate-in">
          <AgentPanel {...agent} />
        </section>

        <section className="card animate-in">
          <div className="card-header">
            <h2>Retrying Echo Service</h2>
          </div>
          <EchoForm {...echoForm} />
        </section>

        <section className="card animate-in">
          <ResourceBoard {...resourceBoard} />
        </section>

        <section className="card animate-in">
          <PlannerPanel {...planner} />
        </section>

        <section className="card animate-in">
          <div className="card-header">
            <h2>Gemini Lesson Outline Builder</h2>
          </div>
          <LessonOutlineForm {...lessonOutlineForm} />
        </section>

        <section className="card animate-in">
          <ChatPanel {...chatbot} onSend={chatbot.send} />
        </section>
      </div>
    </div>
  );
}

export default App;
