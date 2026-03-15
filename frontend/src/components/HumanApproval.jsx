import { AlertCircle, Check, X } from "lucide-react";

export default function HumanApproval({ callId, tool, input, onApprove, onReject }) {
  if (!callId) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
        <div className="flex items-center gap-3 text-amber-500 mb-4">
          <AlertCircle className="w-6 h-6" />
          <h2 className="text-xl font-semibold">Action Required</h2>
        </div>
        
        <p className="text-zinc-300 mb-2">
          The agent wants to execute <span className="font-mono text-emerald-400 bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800">{tool}</span>.
        </p>
        
        <div className="bg-zinc-950 rounded-lg p-3 mb-6 font-mono text-xs text-zinc-400 overflow-x-auto border border-zinc-800 max-h-48 overflow-y-auto">
          <pre>{JSON.stringify(input, null, 2)}</pre>
        </div>

        <div className="flex gap-3 mt-4">
          <button 
            onClick={() => onReject(callId)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-red-900/40 hover:text-red-400 text-zinc-300 transition-colors font-medium border border-transparent hover:border-red-900/50"
          >
            <X className="w-4 h-4" /> Reject
          </button>
          <button 
            onClick={() => onApprove(callId)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-lg shadow-emerald-900/20 font-medium"
          >
            <Check className="w-4 h-4" /> Approve
          </button>
        </div>
      </div>
    </div>
  );
}
