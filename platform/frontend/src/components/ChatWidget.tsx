import { useState, useRef, useEffect, useCallback } from "react";
import {
  MessageCircle,
  X,
  Send,
  Bot,
  User,
  Loader2,
  Wrench,
  RotateCw,
} from "lucide-react";
import { api } from "../api";
import type { ChatMessage } from "../types";

function extractDisplayContent(raw: unknown): string {
  if (raw == null) return "";
  const s = typeof raw === "string" ? raw : String(raw);
  const trimmed = s.trim();
  if (!trimmed) return "";
  if (trimmed.startsWith("[")) {
    try {
      const arr = JSON.parse(trimmed) as unknown[];
      if (!Array.isArray(arr)) return s;
      const parts: string[] = [];
      for (const block of arr) {
        if (!block || typeof block !== "object") continue;
        const obj = block as Record<string, unknown>;
        const text = (obj.text ?? obj.content) as string | undefined;
        if (text == null) continue;
        const t = String(text).trim();
        if (!t) continue;
        if (t.startsWith("{") || t.startsWith("[")) {
          try {
            const inner = JSON.parse(t) as Record<string, unknown>;
            if (typeof inner?.message === "string") parts.push(inner.message);
            else if (typeof inner?.content === "string") parts.push(inner.content);
          } catch {
            parts.push(t);
          }
        } else {
          parts.push(t);
        }
      }
      return parts.join("\n\n");
    } catch {
      return s;
    }
  }
  if (trimmed.startsWith("{") && (trimmed.includes("content") || trimmed.includes("message"))) {
    try {
      const obj = JSON.parse(trimmed) as Record<string, unknown>;
      if (typeof obj?.content === "string") return obj.content;
      if (typeof obj?.message === "string") return obj.message;
    } catch {
      /* fall through */
    }
  }
  return s;
}

interface ChatWidgetProps {
  userId: number | null;
}

export default function ChatWidget({ userId }: ChatWidgetProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [statusText, setStatusText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [messages, streamText, scrollToBottom]);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  // Start new chat when user changes
  useEffect(() => {
    setMessages([]);
    setStreamText("");
    setActiveTools([]);
    setStatusText("");
  }, [userId]);

  const sendMessage = async (overrideText?: string) => {
    const text = (overrideText || input).trim();
    if (!text || streaming || userId === null) return;
    setInput("");

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setStreaming(true);
    setStreamText("");
    setActiveTools([]);
    setStatusText("Thinking...");

    let fullContent = "";
    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      for await (const event of api.chat(text, history, userId)) {
        if (event.type === "token") {
          fullContent += extractDisplayContent(event.content ?? "");
          setStreamText(extractDisplayContent(fullContent) || fullContent);
          setStatusText("");
        } else if (event.type === "tool_call") {
          setActiveTools((prev) => [...prev, event.name ?? "tool"]);
          setStatusText(`Using ${event.name}...`);
        } else if (event.type === "status") {
          const intentMap: Record<string, string> = {
            ORDER_MANAGEMENT: "Looking up your orders...",
            PRODUCT_DISCOVERY: "Searching products...",
            GENERAL: "Thinking...",
          };
          setStatusText(intentMap[event.intent ?? ""] || "Thinking...");
        } else if (event.type === "done") {
          if (fullContent === "" && event.content != null)
            fullContent = extractDisplayContent(event.content);
        } else if (event.type === "error") {
          fullContent = `Sorry, something went wrong: ${event.content}`;
        }
      }
    } catch {
      fullContent =
        fullContent || "Sorry, I encountered an error. Please try again.";
    }

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: extractDisplayContent(fullContent) || fullContent },
    ]);
    setStreaming(false);
    setStreamText("");
    setActiveTools([]);
    setStatusText("");
  };

  const startNewChat = () => {
    if (streaming) return;
    setMessages([]);
    setStreamText("");
    setActiveTools([]);
    setStatusText("");
  };

  const suggestions = [
    "Where is my order?",
    "Show me trending products",
    "I want to return an item",
  ];

  return (
    <>
      {open && (
        <div className="fixed bottom-22 right-4 z-50 w-[380px] h-[540px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden animate-slide-up">
          <div className="bg-gradient-to-r from-violet-600 to-purple-700 px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm">
                  KV Kart Assistant
                </h3>
                <p className="text-white/60 text-xs">
                  Ask about orders, products & more
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={startNewChat}
                disabled={streaming}
                title="Start new chat"
                className="text-white/70 hover:text-white p-1 rounded transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RotateCw className="w-5 h-5" />
              </button>
              <button
                onClick={() => setOpen(false)}
                className="text-white/70 hover:text-white p-1 rounded transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 chat-scroll bg-gray-50/80">
            {messages.length === 0 && !streaming && (
              <div className="text-center py-6">
                <div className="w-14 h-14 bg-violet-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Bot className="w-8 h-8 text-violet-500" />
                </div>
                <p className="text-sm text-gray-700 font-medium">
                  {userId === null
                    ? "Select a user in the header to chat."
                    : "Hi! I'm your KV Kart assistant."}
                </p>
                <p className="text-xs text-gray-400 mt-1 mb-4">
                  {userId === null
                    ? "Orders, cart, and chat are per user."
                    : "Ask me about orders, products, delivery, returns..."}
                </p>
                {userId !== null && (
                  <div className="space-y-2">
                    {suggestions.map((q) => (
                      <button
                        key={q}
                        onClick={() => sendMessage(q)}
                        className="block w-full text-left text-xs bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-gray-600 hover:border-violet-300 hover:text-violet-700 transition cursor-pointer"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 bg-violet-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-4 h-4 text-violet-600" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-violet-600 text-white rounded-br-sm"
                      : "bg-white text-gray-800 border border-gray-100 rounded-bl-sm shadow-sm"
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">
                    {msg.role === "assistant"
                      ? extractDisplayContent(msg.content)
                      : msg.content}
                  </div>
                </div>
                {msg.role === "user" && (
                  <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </div>
            ))}

            {streaming && (
              <div className="flex gap-2 justify-start">
                <div className="w-7 h-7 bg-violet-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-violet-600" />
                </div>
                <div className="max-w-[80%]">
                  {activeTools.length > 0 && (
                    <div className="mb-2 space-y-1">
                      {activeTools.map((tool, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-1.5 text-xs text-gray-500 bg-violet-50 border border-violet-100 rounded-lg px-2.5 py-1.5"
                        >
                          <Wrench className="w-3 h-3 text-violet-500" />
                          <span className="truncate">{tool}</span>
                          <Loader2 className="w-3 h-3 animate-spin ml-auto text-violet-400" />
                        </div>
                      ))}
                    </div>
                  )}
                  {streamText ? (
                    <div className="bg-white text-gray-800 border border-gray-100 rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-sm leading-relaxed shadow-sm">
                      <div className="whitespace-pre-wrap break-words">
                        {streamText}
                        <span className="inline-block w-1.5 h-4 bg-violet-500 ml-0.5 animate-pulse rounded-sm align-text-bottom" />
                      </div>
                    </div>
                  ) : (
                    <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-sm text-gray-500 shadow-sm flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-violet-500" />
                      <span>{statusText || "Thinking..."}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="px-3 py-3 border-t border-gray-100 bg-white shrink-0">
            {(messages.length > 0 || streaming) && (
              <div className="flex justify-end mb-2">
                <button
                  onClick={startNewChat}
                  disabled={streaming}
                  className="flex items-center gap-1.5 text-xs text-violet-600 hover:text-violet-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <RotateCw className="w-3.5 h-3.5" />
                  New chat
                </button>
              </div>
            )}
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Type a message..."
                disabled={streaming || userId === null}
                className="flex-1 text-sm px-4 py-2.5 bg-gray-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-300 disabled:opacity-50 placeholder-gray-400"
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || streaming || userId === null}
                className="p-2.5 bg-violet-600 hover:bg-violet-700 disabled:bg-gray-300 text-white rounded-xl transition cursor-pointer disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen(!open)}
        className={`fixed bottom-4 right-4 z-50 w-14 h-14 rounded-full shadow-lg hover:shadow-xl transition-all flex items-center justify-center cursor-pointer ${
          open
            ? "bg-gray-600 hover:bg-gray-700"
            : "bg-violet-600 hover:bg-violet-700"
        } text-white`}
      >
        {open ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageCircle className="w-6 h-6" />
        )}
      </button>
    </>
  );
}
