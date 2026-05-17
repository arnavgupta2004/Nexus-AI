export const STARTER_PROMPTS = [
  {
    label: "Inbox summary",
    prompt: "Summarize my unread emails from this week.",
    icon: "mail",
  },
  {
    label: "Calendar peek",
    prompt: "What's on my calendar tomorrow?",
    icon: "calendar",
  },
  {
    label: "GitHub priorities",
    prompt: "What are my top GitHub issues to tackle right now?",
    icon: "github",
  },
  {
    label: "Notion capture",
    prompt: "Add my top 3 GitHub issues as tasks in Notion.",
    icon: "notion",
  },
];

export const INTEGRATIONS = [
  { key: "gmail", label: "Gmail", statusKey: "gmail" },
  { key: "calendar", label: "Calendar", statusKey: "calendar" },
  { key: "github", label: "GitHub", statusKey: "github" },
  { key: "notion", label: "Notion", statusKey: "notion" },
];
