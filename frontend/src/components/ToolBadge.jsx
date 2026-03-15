import { Activity, Check } from "lucide-react";

export default function ToolBadge({ tool, status }) {
  const isPending = status === "pending" || status === "paused";
  const isSuccess = status === "success";
  const isError = status === "error";

  return (
    <div className={`flex flex-row items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all duration-300
      ${isPending ? 'bg-amber-900/30 border-amber-700/50 text-amber-300' : ''}
      ${isSuccess ? 'bg-emerald-900/30 border-emerald-800/50 text-emerald-400' : ''}
      ${isError ? 'bg-red-900/30 border-red-800/50 text-red-400' : ''}
    `}>
      <Activity className={`w-3 h-3 ${isPending ? 'animate-spin' : ''}`} />
      <span>{tool}</span>
      {isSuccess && <Check className="w-3 h-3" />}
    </div>
  );
}
