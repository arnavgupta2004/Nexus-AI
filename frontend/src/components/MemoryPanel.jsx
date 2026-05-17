import { useEffect, useState } from "react";
import { Brain, CheckCircle2, Heart, ListTodo, Sparkles } from "lucide-react";
import { apiGet } from "../lib/api";
import { formatRelativeDate } from "../lib/format";

const TABS = [
  { id: "tasks", label: "Tasks", icon: ListTodo },
  { id: "prefs", label: "Preferences", icon: Heart },
];

export default function MemoryPanel({ refreshTrigger }) {
  const [tasks, setTasks] = useState([]);
  const [preferences, setPreferences] = useState({});
  const [tab, setTab] = useState("tasks");

  useEffect(() => {
    apiGet("/memory")
      .then((d) => {
        setTasks(d.tasks || []);
        setPreferences(d.preferences || {});
      })
      .catch(console.error);
  }, [refreshTrigger]);

  const preferenceEntries = Object.entries(preferences);
  const hasTasks = tasks.length > 0;
  const hasPrefs = preferenceEntries.length > 0;
  return (
    <aside className="relative z-10 flex w-80 shrink-0 flex-col border-r border-surface-800/60 bg-surface-950/90 backdrop-blur-xl h-screen">
      <div className="p-5 border-b border-surface-800/60">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-mint/15 border border-mint/25">
            <Brain className="w-5 h-5 text-mint-soft" />
          </div>
          <div>
            <h2 className="font-display text-base font-semibold text-surface-100">
              Memory
            </h2>
            <p className="text-xs text-surface-500">What I remember for you</p>
          </div>
        </div>
      </div>

      <div className="flex gap-1 p-3 mx-3 mt-3 rounded-2xl bg-surface-900/60 border border-surface-800/50">
        {TABS.map((item) => {
          const TabIcon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-medium transition-all
                ${
                  tab === item.id
                    ? "bg-surface-800/80 text-surface-100 shadow-sm"
                    : "text-surface-500 hover:text-surface-300"
                }`}
            >
              <TabIcon className="w-3.5 h-3.5" />
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {tab === "tasks" && (
          <>
            {hasTasks ? (
              tasks.map((task, i) => (
                <article
                  key={task.id}
                  className="animate-fade-up rounded-2xl border border-surface-700/40 bg-surface-900/50 p-4 hover:border-surface-600/50 hover:bg-surface-900/70 transition-colors"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <p className="text-sm font-medium text-surface-100 line-clamp-2 leading-relaxed">
                    {task.description}
                  </p>
                  {task.result && (
                    <p className="text-xs text-surface-500 line-clamp-2 mt-2 leading-relaxed">
                      {task.result}
                    </p>
                  )}
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-surface-800/50">
                    {task.status === "completed" ? (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-mint-soft">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Done
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-accent-soft/90">
                        Incomplete
                      </span>
                    )}
                    {task.date && (
                      <span className="text-[10px] text-surface-600">
                        {formatRelativeDate(task.date)}
                      </span>
                    )}
                  </div>
                </article>
              ))
            ) : (
              <EmptyMemory
                icon={ListTodo}
                title="No tasks yet"
                hint="Ask me to do something — I'll save a summary here."
              />
            )}
          </>
        )}

        {tab === "prefs" && (
          <>
            {hasPrefs ? (
              preferenceEntries.map(([key, value], i) => (
                <article
                  key={key}
                  className="animate-fade-up rounded-2xl border border-surface-700/40 bg-surface-900/50 p-4"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <p className="text-[11px] font-mono text-surface-500 break-words">
                    {key}
                  </p>
                  <p className="text-sm text-surface-200 mt-1.5 break-words leading-relaxed">
                    {value}
                  </p>
                </article>
              ))
            ) : (
              <EmptyMemory
                icon={Heart}
                title="No preferences saved"
                hint={'Try: "Remember that I prefer morning focus blocks."'}
              />
            )}
          </>
        )}
      </div>

      <footer className="p-4 border-t border-surface-800/60 text-center">
        <p className="text-[11px] text-surface-600 flex items-center justify-center gap-1.5">
          <Sparkles className="w-3 h-3 text-accent/60" />
          SQLite · Gemini
        </p>
      </footer>
    </aside>
  );
}

function EmptyMemory({ icon, title, hint }) {
  const EmptyIcon = icon;
  return (
    <div className="flex flex-col items-center justify-center text-center px-4 py-10 rounded-2xl border border-dashed border-surface-700/40 bg-surface-900/30">
      <div className="w-12 h-12 rounded-2xl bg-surface-800/50 flex items-center justify-center mb-3">
        <EmptyIcon className="w-5 h-5 text-surface-500" />
      </div>
      <p className="text-sm font-medium text-surface-300">{title}</p>
      <p className="text-xs text-surface-500 mt-2 leading-relaxed max-w-[200px]">
        {hint}
      </p>
    </div>
  );
}
