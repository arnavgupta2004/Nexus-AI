import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import ToolBadge from "./ToolBadge";

export default function ChatWindow({ onRequireApproval, onTaskComplete }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm NexusAI, your autonomous agent. What would you like me to do?", type: "text" }
  ]);
  const [input, setInput] = useState("");
  const [modelChoice, setModelChoice] = useState("gemini");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");
    
    // Add user message to UI
    setMessages(prev => [...prev, { role: "user", content: userMsg, type: "text" }]);
    setIsLoading(true);
    
    // Add an empty assistant message template for the stream
    setMessages(prev => [...prev, { role: "assistant", content: "", tools: [], type: "mixed", statusContext: "Thinking..." }]);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, model: modelChoice })
      });

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
            
            setMessages(prev => {
              const newMessages = [...prev];
              const msgIndex = newMessages.length - 1;
              const msg = newMessages[msgIndex];
              
              if (data.type === "text") {
                msg.content += (msg.content ? "\n" : "") + data.content;
                msg.statusContext = null;
              } else if (data.type === "tool_start") {
                msg.tools.push({ name: data.tool, status: "pending", input: data.input });
                msg.statusContext = `Using ${data.tool}...`;
              } else if (data.type === "tool_result" || data.type === "tool_error") {
                // Update latest matching pending tool
                let targetIdx = msg.tools.length - 1;
                while (targetIdx >= 0) {
                  if (msg.tools[targetIdx].name === data.tool && (msg.tools[targetIdx].status === "pending" || msg.tools[targetIdx].status === "paused")) {
                    break;
                  }
                  targetIdx--;
                }
                
                if (targetIdx >= 0) {
                  msg.tools[targetIdx].status = data.status || (data.type === "tool_result" ? "success" : "error");
                  msg.tools[targetIdx].result = data.result || data.error;
                }
                msg.statusContext = "Evaluating results...";
              } else if (data.type === "pause") {
                  let targetIdx = msg.tools.length - 1;
                  while (targetIdx >= 0) {
                    if (msg.tools[targetIdx].name === data.tool && msg.tools[targetIdx].status === "pending") break;
                    targetIdx--;
                  }
                  if (targetIdx >= 0) {
                      msg.tools[targetIdx].status = "paused";
                  }
                  msg.statusContext = "Waiting for your approval...";
                  onRequireApproval({ callId: data.call_id, tool: data.tool, input: data.input });
              } else if (data.type === "status") {
                  msg.statusContext = data.content;
              }
              
              return newMessages;
            });
          } catch (e) {
            console.error("Failed to parse SSE line", line, e);
          }
        }
      }
      
      setMessages(prev => {
          const newMessages = [...prev];
          const lastIndex = newMessages.length - 1;
          newMessages[lastIndex].statusContext = null;
          return newMessages;
      });
      
      onTaskComplete();
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, an error occurred communicating with the server.", type: "text" }]);
    } finally {
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
          <select 
            value={modelChoice} 
            onChange={(e) => setModelChoice(e.target.value)}
            disabled={isLoading}
            className="bg-zinc-800/80 border border-zinc-700 text-zinc-300 text-sm rounded-2xl px-4 py-4 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 cursor-pointer disabled:opacity-50"
          >
            <option value="gemini">Gemini 2.5 Flash</option>
            <option value="claude">Claude 3.5 Sonnet</option>
          </select>
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
          Agent capabilities powered by Claude 3.5 Sonnet + Model Context Protocol
        </p>
      </div>
    </div>
  );
}
