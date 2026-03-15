import { useEffect, useState } from "react";
import { Database, CheckCircle, Clock } from "lucide-react";

export default function MemoryPanel({ refreshTrigger }) {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/memory")
      .then(r => r.json())
      .then(d => setTasks(d.tasks || []))
      .catch(console.error);
  }, [refreshTrigger]);

  return (
    <div className="w-72 border-r border-zinc-800 bg-zinc-950 flex flex-col h-screen shrink-0">
      <div className="p-4 border-b border-zinc-800 flex items-center gap-2">
        <div className="bg-emerald-500/10 p-2 rounded-lg">
          <Database className="w-5 h-5 text-emerald-500" />
        </div>
        <h2 className="font-semibold text-zinc-100 uppercase tracking-wider text-xs">Long-Term Memory</h2>
      </div>
      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {tasks.map(task => (
          <div key={task.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-sm hover:border-zinc-700 transition-colors">
            <div className="flex justify-between items-start mb-2">
              <span className="font-medium text-zinc-200 line-clamp-2 leading-relaxed">{task.description}</span>
            </div>
            {task.status === "completed" ? (
              <div className="flex items-center gap-1.5 text-xs text-emerald-500 mt-3 font-medium">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Completed</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-amber-500 mt-3 font-medium">
                <Clock className="w-3.5 h-3.5" />
                <span>Failed</span>
              </div>
            )}
          </div>
        ))}
        {tasks.length === 0 && (
          <div className="text-zinc-600 text-sm h-32 flex flex-col items-center justify-center border border-dashed border-zinc-800 rounded-xl mt-4">
            No memories yet.
          </div>
        )}
      </div>
      <div className="p-4 border-t border-zinc-800 text-xs text-zinc-600 font-mono text-center">
        Powered by SQLite & Claude
      </div>
    </div>
  );
}
