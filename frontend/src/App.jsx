import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import MemoryPanel from "./components/MemoryPanel";
import HumanApproval from "./components/HumanApproval";

function App() {
  const [pendingAction, setPendingAction] = useState(null);
  const [refreshTasks, setRefreshTasks] = useState(0);

  const handleRequireApproval = (actionData) => {
    setPendingAction(actionData);
  };

  const handleApprove = async (callId) => {
    try {
      await fetch("http://localhost:8000/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ call_id: callId })
      });
      setPendingAction(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async (callId) => {
    try {
      await fetch("http://localhost:8000/reject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ call_id: callId })
      });
      setPendingAction(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleTaskComplete = () => {
    // trigger memory panel refresh
    setRefreshTasks(prev => prev + 1);
  };

  return (
    <div className="flex h-screen w-full bg-[#09090b] text-zinc-100 font-sans overflow-hidden selection:bg-emerald-500/30">
      <MemoryPanel refreshTrigger={refreshTasks} />
      
      <ChatWindow 
        onRequireApproval={handleRequireApproval} 
        onTaskComplete={handleTaskComplete} 
      />

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
