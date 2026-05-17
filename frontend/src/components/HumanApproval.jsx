import { ShieldAlert, Check, X } from "lucide-react";
import { formatToolName } from "../lib/format";

export default function HumanApproval({ callId, tool, input, onApprove, onReject }) {
  if (!callId) return null;

  const label = formatToolName(tool);
  const isWrite =
    /send|create|update|delete|post|schedule|write/i.test(tool) ||
    /send|create|update|delete|post|schedule|write/i.test(JSON.stringify(input));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay backdrop-blur-md animate-fade-up">
      <div
        className="glass-panel rounded-3xl max-w-md w-full p-7 shadow-glow-lg"
        role="dialog"
        aria-labelledby="approval-title"
      >
        <div className="flex items-start gap-4 mb-5">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-accent/15 border border-accent/25 shrink-0">
            <ShieldAlert className="w-6 h-6 text-accent-soft" />
          </div>
          <div>
            <h2
              id="approval-title"
              className="font-display text-xl font-semibold text-surface-100"
            >
              Your approval needed
            </h2>
            <p className="text-sm text-surface-400 mt-1 leading-relaxed">
              {isWrite
                ? "This action changes something outside NexusAI. Take a moment to review."
                : "The agent paused before continuing. You can approve or decline."}
            </p>
          </div>
        </div>

        <div className="rounded-2xl bg-surface-800/40 border border-surface-700/50 p-4 mb-5">
          <p className="text-xs font-medium uppercase tracking-wider text-surface-500 mb-2">
            Requested action
          </p>
          <p className="font-medium text-accent-soft">{label}</p>
          <div className="mt-3 rounded-xl bg-surface-900/80 border border-surface-800/60 p-3 font-mono text-[11px] text-surface-400 overflow-x-auto max-h-40 overflow-y-auto leading-relaxed">
            <pre className="whitespace-pre-wrap break-words">
              {JSON.stringify(input, null, 2)}
            </pre>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => onReject(callId)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-surface-800/80 hover:bg-red-950/50 text-surface-200 hover:text-red-200 border border-surface-700/50 hover:border-red-800/40 transition-all font-medium text-sm"
          >
            <X className="w-4 h-4" />
            Decline
          </button>
          <button
            type="button"
            onClick={() => onApprove(callId)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-gradient-to-r from-accent to-accent-muted hover:opacity-95 text-on-accent transition-all font-semibold text-sm shadow-glow"
          >
            <Check className="w-4 h-4" />
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
