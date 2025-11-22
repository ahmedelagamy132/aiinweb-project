// Application shell responsible for wiring feature modules into the page.
//
// Each lab encourages keeping this component small so students can focus on the
// feature folders under `src/features`. New demos should follow the same
// pattern: create a hook for stateful logic and pass it into a presentational
// component.
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

function App() {
  const echoForm = useEchoForm();
  const lessonOutlineForm = useLessonOutlineForm();
  const resourceBoard = useResourceBoard();
  const planner = usePlanner();
  const chatbot = useChatbot();

  return (
    <main style={{ padding: 24, display: 'grid', gap: 32 }}>
      <header style={{ display: 'grid', gap: 8 }}>
        <h1>AI in Web Programming Demos</h1>
        <p>
          FastAPI and React layers
          evolve together. Each section mirrors the workflow documented in the
          instructor guide.
        </p>
      </header>

      <section style={{ display: 'grid', gap: 16 }}>
        <h2>Retrying echo service</h2>
        <EchoForm {...echoForm} />
      </section>

      <section style={{ display: 'grid', gap: 16 }}>
        <ResourceBoard {...resourceBoard} />
      </section>

      <section style={{ display: 'grid', gap: 16 }}>
        <PlannerPanel {...planner} />
      </section>

      <section style={{ display: 'grid', gap: 16 }}>
        <h2>Gemini lesson outline builder</h2>
        <LessonOutlineForm {...lessonOutlineForm} />
      </section>

      <section style={{ display: 'grid', gap: 16 }}>
        <ChatPanel {...chatbot} onSend={chatbot.send} />
      </section>
    </main>
  );
}

export default App;
