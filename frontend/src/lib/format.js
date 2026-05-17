export function formatToolName(tool) {
  if (!tool) return "Tool";
  const [service, ...rest] = tool.split("__");
  const action = rest.join(" ").replace(/_/g, " ");
  const serviceLabel =
    service === "memory"
      ? "Memory"
      : service.charAt(0).toUpperCase() + service.slice(1);
  return action ? `${serviceLabel} · ${action}` : serviceLabel;
}

export function formatRelativeDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
