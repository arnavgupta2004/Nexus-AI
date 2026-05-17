import { Calendar, FileText, Github, Mail, ArrowUpRight } from "lucide-react";
import { STARTER_PROMPTS } from "../lib/constants";

const ICONS = {
  mail: Mail,
  calendar: Calendar,
  github: Github,
  notion: FileText,
};

export default function StarterPrompts({ onSelect, disabled }) {
  return (
    <div className="animate-fade-up max-w-2xl mx-auto w-full">
      <p className="text-sm text-surface-400 mb-3 text-center">
        Try something — I&apos;ll handle the rest
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {STARTER_PROMPTS.map(({ label, prompt, icon }) => {
          const Icon = ICONS[icon] || Mail;
          return (
            <button
              key={label}
              type="button"
              disabled={disabled}
              onClick={() => onSelect(prompt)}
              className="group text-left flex items-start gap-3 p-4 rounded-2xl border border-surface-700/50 bg-surface-900/50 hover:bg-surface-800/60 hover:border-accent/30 hover:shadow-glow transition-all duration-200 disabled:opacity-40 disabled:pointer-events-none"
            >
              <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-accent/15 text-accent-soft shrink-0 group-hover:bg-accent/25 transition-colors">
                <Icon className="w-4 h-4" />
              </span>
              <span className="flex-1 min-w-0">
                <span className="flex items-center gap-1 font-medium text-surface-100 text-sm">
                  {label}
                  <ArrowUpRight className="w-3.5 h-3.5 text-surface-500 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                </span>
                <span className="block text-xs text-surface-500 mt-0.5 line-clamp-2 leading-relaxed">
                  {prompt}
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
