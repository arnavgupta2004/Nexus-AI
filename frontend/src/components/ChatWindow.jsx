import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Sparkles, User } from "lucide-react";
import ToolBadge from "./ToolBadge";
import StarterPrompts from "./StarterPrompts";
import AgentOrb from "./AgentOrb";
import { API_BASE_URL } from "../lib/api";

const WELCOME =
  "Good to see you. What should we tackle together today?";

export default function ChatWindow({ onRequireApproval, onTaskComplete }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: WELCOME, type: "text" },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const requestInFlightRef = useRef(false);

  const showStarters =
    messages.length === 1 &&
    messages[0].role === "assistant" &&
    !isLoading;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const updateLastMessage = (updater) => {
    setMessages((prev) => {
      const lastIndex = prev.length - 1;
      return prev.map((message, index) =>
        index === lastIndex ? updater(message) : message
      );
    });
  };

  const sendMessage = useCallback(
    async (userMsg) => {
      if (!userMsg.trim() || requestInFlightRef.current) return;

      requestInFlightRef.current = true;
      setIsLoading(true);

      setMessages((prev) => [
        ...prev,
        { role: "user", content: userMsg, type: "text" },
      ]);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "",
          tools: [],
          type: "mixed",
          statusContext: "Thinking...",
        },
      ]);

      try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: userMsg }),
        });

        if (!response.ok || !response.body) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n").filter((l) => l.trim() !== "");

          for (const line of lines) {
            try {
              const data = JSON.parse(line);

              updateLastMessage((msg) => {
                if (data.type === "text") {
                  return {
                    ...msg,
                    content: msg.content
                      ? `${msg.content}\n${data.content}`
                      : data.content,
                    statusContext: null,
                  };
                }
                if (data.type === "tool_start") {
                  return {
                    ...msg,
                    tools: [
                      ...(msg.tools || []),
                      {
                        name: data.tool,
                        status: "pending",
                        input: data.input,
                      },
                    ],
                    statusContext: `Working with ${data.tool.replace(/__/g, " ")}...`,
                  };
                }
                if (data.type === "tool_result" || data.type === "tool_error") {
                  const tools = [...(msg.tools || [])];
                  let targetIdx = tools.length - 1;
                  while (targetIdx >= 0) {
                    if (
                      tools[targetIdx].name === data.tool &&
                      (tools[targetIdx].status === "pending" ||
                        tools[targetIdx].status === "paused")
                    ) {
                      break;
                    }
                    targetIdx--;
                  }

                  if (targetIdx >= 0) {
                    tools[targetIdx] = {
                      ...tools[targetIdx],
                      status:
                        data.status ||
                        (data.type === "tool_result" ? "success" : "error"),
                      result: data.result || data.error,
                    };
                  }
                  return {
                    ...msg,
                    tools,
                    statusContext: "Putting it all together...",
                  };
                }
                if (data.type === "pause") {
                  const tools = [...(msg.tools || [])];
                  let targetIdx = tools.length - 1;
                  while (targetIdx >= 0) {
                    if (
                      tools[targetIdx].name === data.tool &&
                      tools[targetIdx].status === "pending"
                    ) {
                      break;
                    }
                    targetIdx--;
                  }
                  if (targetIdx >= 0) {
                    tools[targetIdx] = { ...tools[targetIdx], status: "paused" };
                  }
                  onRequireApproval({
                    callId: data.call_id,
                    tool: data.tool,
                    input: data.input,
                  });
                  return {
                    ...msg,
                    tools,
                    statusContext: "Waiting for your approval...",
                  };
                }
                if (data.type === "status") {
                  return { ...msg, statusContext: data.content };
                }
                return msg;
              });
            } catch (e) {
              console.error("Failed to parse SSE line", line, e);
            }
          }
        }

        updateLastMessage((msg) => ({ ...msg, statusContext: null }));
        onTaskComplete();
      } catch (err) {
        console.error(err);
        updateLastMessage((msg) => ({
          ...msg,
          content:
            "I couldn't reach the server. Make sure the backend is running on port 8000, then try again.",
          statusContext: null,
        }));
      } finally {
        requestInFlightRef.current = false;
        setIsLoading(false);
      }
    },
    [onRequireApproval, onTaskComplete]
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const userMsg = input.trim();
    setInput("");
    sendMessage(userMsg);
  };

  const handlePromptSelect = (prompt) => {
    sendMessage(prompt);
  };

  return (
    <div className="relative flex flex-1 flex-col min-h-0">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 animate-fade-up ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              style={{ animationDelay: `${Math.min(idx * 30, 120)}ms` }}
            >
              <Avatar role={msg.role} />

              <div
                className={`flex flex-col gap-2 max-w-[85%] min-w-0 ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                {msg.content && (
                  <div
                    className={`px-5 py-3.5 rounded-3xl whitespace-pre-wrap leading-relaxed text-[15px] shadow-sm
                      ${
                        msg.role === "user"
                          ? "bg-gradient-to-br from-surface-800 to-surface-900 text-surface-100 rounded-tr-lg border border-surface-700/50"
                          : "glass-panel text-surface-100 rounded-tl-lg"
                      }`}
                  >
                    {msg.content}
                  </div>
                )}

                {msg.tools && msg.tools.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {msg.tools.map((t, i) => (
                      <ToolBadge key={i} tool={t.name} status={t.status} />
                    ))}
                  </div>
                )}

                {msg.statusContext && (
                  <div className="flex items-center gap-2.5 text-xs font-medium text-accent-soft/90 px-1 py-0.5">
                    <AgentOrb size="sm" />
                    <span className="animate-soft-pulse">{msg.statusContext}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {showStarters && (
            <div className="pt-2 pb-4">
              <StarterPrompts onSelect={handlePromptSelect} disabled={isLoading} />
            </div>
          )}

          <div ref={messagesEndRef} className="h-2" />
        </div>
      </div>

      <div className="shrink-0 px-6 pb-6 pt-2 bg-gradient-to-t from-surface-950 via-surface-950/95 to-transparent">
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto relative group"
        >
          <div className="relative rounded-3xl border border-surface-700/50 bg-surface-900/80 shadow-glow-lg backdrop-blur-sm focus-within:border-accent/40 focus-within:shadow-[0_0_0_3px_rgba(244,114,182,0.14)] transition-all">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              placeholder={
                isLoading ? "Working on it..." : "Tell me what you need..."
              }
              className="w-full bg-transparent text-surface-100 rounded-3xl py-4 pl-6 pr-14 focus:outline-none placeholder:text-surface-500 disabled:opacity-50 text-[15px]"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 p-2.5 rounded-2xl bg-gradient-to-br from-accent to-accent-muted text-on-accent disabled:from-surface-800 disabled:to-surface-800 disabled:text-surface-500 transition-all hover:opacity-95 disabled:opacity-60 shadow-glow"
              aria-label="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-center text-[11px] text-surface-600 mt-3 tracking-wide">
            Thoughtful actions · Your approval on anything sensitive
          </p>
        </form>
      </div>
    </div>
  );
}

function Avatar({ role }) {
  if (role === "user") {
    return (
      <div className="mt-0.5 shrink-0 flex items-center justify-center w-10 h-10 rounded-2xl bg-surface-800 border border-surface-700/60 shadow-sm">
        <User className="w-5 h-5 text-surface-300" />
      </div>
    );
  }

  return (
    <div className="mt-0.5 shrink-0 relative">
      <div className="absolute inset-0 rounded-2xl bg-accent/25 blur-md" />
      <div className="relative flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br from-accent/90 to-accent-muted border border-accent/30 shadow-glow">
        <Sparkles className="w-5 h-5 text-on-accent" strokeWidth={2.25} />
      </div>
    </div>
  );
}
