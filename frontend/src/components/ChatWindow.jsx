import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import ToolBadge from "./ToolBadge";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function ChatWindow({ onRequireApproval, onTaskComplete }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm NexusAI, your autonomous agent. What would you like me to do?", type: "text" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const requestInFlightRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const updateLastMessage = (updater) => {
    setMessages(prev => {
      const lastIndex = prev.length - 1;
      return prev.map((message, index) => (
        index === lastIndex ? updater(message) : message
      ));
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || requestInFlightRef.current) return;

    const userMsg = input.trim();
    requestInFlightRef.current = true;
    setInput("");
    
    // Add user message to UI
    setMessages(prev => [...prev, { role: "user", content: userMsg, type: "text" }]);
    setIsLoading(true);
    
    // Add an empty assistant message template for the stream
    setMessages(prev => [...prev, { role: "assistant", content: "", tools: [], type: "mixed", statusContext: "Thinking..." }]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg })
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
        const lines = chunk.split("\n").filter(l => l.trim() !== "");
        
        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            
            updateLastMessage(msg => {
              if (data.type === "text") {
                return {
                  ...msg,
                  content: msg.content ? `${msg.content}\n${data.content}` : data.content,
                  statusContext: null
                };
              } else if (data.type === "tool_start") {
                return {
                  ...msg,
                  tools: [...(msg.tools || []), { name: data.tool, status: "pending", input: data.input }],
                  statusContext: `Using ${data.tool}...`
                };
              } else if (data.type === "tool_result" || data.type === "tool_error") {
                const tools = [...(msg.tools || [])];
                let targetIdx = tools.length - 1;
                while (targetIdx >= 0) {
                  if (tools[targetIdx].name === data.tool && (tools[targetIdx].status === "pending" || tools[targetIdx].status === "paused")) {
                    break;
                  }
                  targetIdx--;
                }
                
                if (targetIdx >= 0) {
                  tools[targetIdx] = {
                    ...tools[targetIdx],
                    status: data.status || (data.type === "tool_result" ? "success" : "error"),
                    result: data.result || data.error
                  };
                }
                return {
                  ...msg,
                  tools,
                  statusContext: "Evaluating results..."
                };
              } else if (data.type === "pause") {
                const tools = [...(msg.tools || [])];
                let targetIdx = tools.length - 1;
                while (targetIdx >= 0) {
                  if (tools[targetIdx].name === data.tool && tools[targetIdx].status === "pending") break;
                  targetIdx--;
                }
                if (targetIdx >= 0) {
                  tools[targetIdx] = { ...tools[targetIdx], status: "paused" };
                }
                onRequireApproval({ callId: data.call_id, tool: data.tool, input: data.input });
                return {
                  ...msg,
                  tools,
                  statusContext: "Waiting for your approval..."
                };
              } else if (data.type === "status") {
                return {
                  ...msg,
                  statusContext: data.content
                };
              }
              
              return msg;
            });
          } catch (e) {
            console.error("Failed to parse SSE line", line, e);
          }
        }
      }
      
      updateLastMessage(msg => ({ ...msg, statusContext: null }));
      
      onTaskComplete();
    } catch (err) {
      console.error(err);
      updateLastMessage(msg => ({
          ...msg,
          content: "Backend is not reachable. Start the FastAPI server on port 8000, then try again.",
          statusContext: null
      }));
    } finally {
      requestInFlightRef.current = false;
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#09090b] relative">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 max-w-4xl mx-auto ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`mt-1 shrink-0 flex items-center justify-center w-10 h-10 rounded-full border shadow-sm ${msg.role === "user" ? 'bg-zinc-800 border-zinc-700' : 'bg-emerald-900 border-emerald-700/50 text-emerald-400'}`}>
              {msg.role === "user" ? <User className="w-5 h-5 text-zinc-300" /> : <Bot className="w-6 h-6" />}
            </div>
            
            <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
              {/* Text content block */}
              {msg.content && (
                <div className={`px-5 py-3.5 rounded-2xl whitespace-pre-wrap leading-relaxed shadow-sm text-[15px]
                  ${msg.role === "user" ? 'bg-zinc-800 text-zinc-100 rounded-tr-sm border border-zinc-700' : 'bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-tl-sm'}`}>
                  {msg.content}
                </div>
              )}
              
              {/* Tool Execution Badges Row */}
              {msg.tools && msg.tools.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {msg.tools.map((t, i) => (
                      <ToolBadge key={i} tool={t.name} status={t.status} />
                  ))}
                </div>
              )}
              
              {/* Status Context Helper */}
              {msg.statusContext && (
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-500 mt-1 animate-pulse px-1">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600" />
                  {msg.statusContext}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} className="h-4" />
      </div>

      <div className="p-6 bg-gradient-to-t from-[#09090b] via-[#09090b] to-transparent">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-3 relative group">
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              placeholder={isLoading ? "Please wait..." : "Ask NexusAI to do something..."}
              className="w-full bg-zinc-900 border border-zinc-700 text-zinc-100 rounded-2xl py-4 pl-6 pr-14 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all placeholder:text-zinc-500 shadow-lg disabled:opacity-50"
            />
            <button 
              type="submit" 
              disabled={isLoading || !input.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-800 text-white disabled:text-zinc-500 rounded-xl transition-all shadow-md group-focus-within:shadow-emerald-900/40"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </form>
        <p className="text-center text-xs text-zinc-500 mt-4 font-medium tracking-wide">
          Agent capabilities powered by Gemini + Model Context Protocol
        </p>
      </div>
    </div>
  );
}
