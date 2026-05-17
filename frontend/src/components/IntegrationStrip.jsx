import { useEffect, useState } from "react";
import { Calendar, Github, Mail, FileText } from "lucide-react";
import { apiGet } from "../lib/api";
import { INTEGRATIONS } from "../lib/constants";

const ICONS = {
  gmail: Mail,
  calendar: Calendar,
  github: Github,
  notion: FileText,
};

export default function IntegrationStrip() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiGet("/integrations/status")
      .then((data) => {
        if (!cancelled) setStatus(data);
      })
      .catch(() => {
        if (!cancelled) setStatus(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-[11px] font-medium uppercase tracking-wider text-surface-500 mr-1">
        Connections
      </span>
      {INTEGRATIONS.map(({ key, label, statusKey }) => {
        const Icon = ICONS[key] || FileText;
        const connected = status?.[statusKey];
        const isLoading = loading;

        return (
          <div
            key={key}
            title={
              connected
                ? `${label} is ready`
                : `${label} needs configuration in backend/.env`
            }
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors
              ${isLoading ? "border-surface-800/80 bg-surface-900/50 text-surface-500" : ""}
              ${
                !isLoading && connected
                  ? "border-mint/30 bg-mint/10 text-mint-soft"
                  : ""
              }
              ${
                !isLoading && !connected
                  ? "border-surface-700/50 bg-surface-900/40 text-surface-500"
                  : ""
              }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full shrink-0
                ${isLoading ? "bg-surface-600 animate-pulse" : ""}
                ${!isLoading && connected ? "bg-mint shadow-[0_0_6px_rgba(52,211,153,0.8)]" : ""}
                ${!isLoading && !connected ? "bg-surface-600" : ""}`}
            />
            <Icon className="w-3 h-3 opacity-80" />
            {label}
          </div>
        );
      })}
    </div>
  );
}
