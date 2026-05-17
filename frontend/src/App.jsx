import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import MemoryPanel from "./components/MemoryPanel";
import HumanApproval from "./components/HumanApproval";
import AppHeader from "./components/AppHeader";
import { apiPost } from "./lib/api";

function App() {
  const [pendingAction, setPendingAction] = useState(null);
  const [refreshTasks, setRefreshTasks] = useState(0);

  const handleRequireApproval = (actionData) => {
    setPendingAction(actionData);
  };

  const handleApprove = async (callId) => {
    try {
      await apiPost("/approve", { call_id: callId });
      setPendingAction(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async (callId) => {
    try {
      await apiPost("/reject", { call_id: callId });
      setPendingAction(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleTaskComplete = () => {
    setRefreshTasks((prev) => prev + 1);
  };

  return (
    <div className="relative flex h-screen w-full overflow-hidden bg-surface-950 text-surface-100">
      <div className="pointer-events-none absolute inset-0 ambient-glow" aria-hidden />

      <MemoryPanel refreshTrigger={refreshTasks} />

      <main className="relative flex flex-1 flex-col min-w-0">
        <AppHeader />
        <ChatWindow
          onRequireApproval={handleRequireApproval}
          onTaskComplete={handleTaskComplete}
        />
      </main>

      {pendingAction && (
        <HumanApproval
          callId={pendingAction.callId}
          tool={pendingAction.tool}
          input={pendingAction.input}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
    </div>
  );
}

export default App;
