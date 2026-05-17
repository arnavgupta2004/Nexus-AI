import { Sparkles } from "lucide-react";
import IntegrationStrip from "./IntegrationStrip";
import ThemeToggle from "./ThemeToggle";

export default function AppHeader() {
  return (
    <header className="shrink-0 border-b border-surface-800/60 bg-surface-950/80 backdrop-blur-md z-10">
      <div className="max-w-4xl mx-auto px-6 py-4 flex flex-col gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative shrink-0">
            <div className="absolute inset-0 rounded-2xl bg-accent/30 blur-md animate-orb-glow" />
            <div className="relative flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-br from-accent/90 to-accent-muted shadow-glow">
              <Sparkles className="w-5 h-5 text-on-accent" strokeWidth={2.25} />
            </div>
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-xl font-semibold tracking-tight text-gradient-brand">
              NexusAI
            </h1>
            <p className="text-sm text-surface-400 truncate">
              Your warm, capable personal assistant
            </p>
          </div>
          <ThemeToggle />
        </div>
        <IntegrationStrip />
      </div>
    </header>
  );
}
