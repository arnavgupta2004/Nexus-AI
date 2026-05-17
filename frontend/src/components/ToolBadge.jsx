import { Activity, Check, Pause, X } from "lucide-react";
import { formatToolName } from "../lib/format";

export default function ToolBadge({ tool, status }) {
  const isPending = status === "pending";
  const isPaused = status === "paused";
  const isSuccess = status === "success" || status === "rejected";
  const isError = status === "error";

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-300
        ${isPending ? "bg-accent/10 border-accent/25 text-accent-soft" : ""}
        ${isPaused ? "bg-amber-950/40 border-amber-700/40 text-amber-200/90" : ""}
        ${isSuccess && status === "success" ? "bg-mint/15 border-mint/30 text-mint-soft" : ""}
        ${isSuccess && status === "rejected" ? "bg-surface-800/60 border-surface-600/40 text-surface-400" : ""}
        ${isError ? "bg-red-950/30 border-red-800/40 text-red-300/90" : ""}`}
    >
      {isPending && <Activity className="w-3 h-3 animate-spin" />}
      {isPaused && <Pause className="w-3 h-3" />}
      {isSuccess && status === "success" && <Check className="w-3 h-3" />}
      {isSuccess && status === "rejected" && <X className="w-3 h-3" />}
      {isError && <X className="w-3 h-3" />}
      <span>{formatToolName(tool)}</span>
    </div>
  );
}
