export default function AgentOrb({ size = "md", className = "" }) {
  const sizes = {
    sm: "w-2 h-2",
    md: "w-2.5 h-2.5",
    lg: "w-3 h-3",
  };

  return (
    <span className={`relative inline-flex ${className}`}>
      <span
        className={`${sizes[size]} rounded-full bg-accent animate-soft-pulse`}
      />
      <span
        className={`absolute inset-0 ${sizes[size]} rounded-full bg-accent/50 blur-sm animate-orb-glow`}
      />
    </span>
  );
}
