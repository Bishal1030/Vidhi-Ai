import React, { useState } from "react";
import { Copy, Check, BookOpen, FileText } from "lucide-react";
import { SourceCard } from "./SourceCard";
import type { ChatMessage } from "@/types/chat";

// Local helper to copy text
function useClipboard() {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const copyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };
  return { copiedId, copyText };
}

interface ChatMessagesProps {
  messages: ChatMessage[];
  highlightedAnchor: string | null;
  onCitationClick: (anchor: string) => void;
}

export function ChatMessages({ messages, highlightedAnchor, onCitationClick }: ChatMessagesProps) {
  const { copiedId, copyText } = useClipboard();

  const handleAnswerClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.tagName === "A" && target.getAttribute("href")?.startsWith("#")) {
      const anchor = target.getAttribute("href");
      if (anchor) {
        e.preventDefault();
        onCitationClick(anchor);
      }
    }
  };

  const renderMessageContent = (content: string) => {
    const parts = content.split(/(\*\*\[.*?\]\(#.*?\)\*\*|\*\*.*?\*\*)/g);

    return parts.map((part, idx) => {
      // 1. Citation Link Check: **[Citation](#anchor)**
      const linkMatch = part.match(/\*\*\[(.*?)\]\((#.*?)\)\*\*/);
      if (linkMatch) {
        const text = linkMatch[1];
        const href = linkMatch[2];
        return (
          <a
            key={idx}
            href={href}
            className="inline-flex items-center gap-0.5 px-1.5 py-0.5 mx-0.5 rounded text-xs font-semibold border border-black bg-[#ffea79] text-black shadow-[1px_1px_0_0_#000] hover:translate-y-px hover:shadow-none transition-all cursor-pointer font-sans no-underline"
          >
            <BookOpen className="w-3 h-3" />
            {text}
          </a>
        );
      }

      // 2. Pure Bold Check: **bold text**
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={idx} className="font-semibold text-black">{part.slice(2, -2)}</strong>;
      }

      // 3. Plain Text
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <div key={message.id} className="space-y-4">
          <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
            <div 
              className={`max-w-[85%] border-2 border-black p-5 shadow-[4px_4px_0_0_#000] rounded-xl ${
                message.role === "user" 
                  ? "bg-[#e8f6ff]" 
                  : "bg-white"
              }`}
            >
              <div className="flex justify-between items-center gap-4 mb-2 pb-1.5 border-b border-black/10">
                <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 font-sans">
                  {message.role === "user" ? "User" : "Vidhi-Ai"}
                </span>
                <span className="text-[10px] text-zinc-400 font-bold font-sans">{message.timestamp}</span>
              </div>

              <div 
                onClick={handleAnswerClick}
                className="text-sm leading-relaxed text-zinc-800 space-y-2 whitespace-pre-line"
              >
                {renderMessageContent(message.content)}
              </div>

              <div className="mt-4 pt-2 border-t border-black/5 flex justify-end">
                <button
                  onClick={() => copyText(message.id, message.content)}
                  className="flex items-center gap-1 text-[11px] font-bold text-zinc-500 hover:text-black transition-colors cursor-pointer"
                >
                  {copiedId === message.id ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-green-600" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Copy response
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {message.role === "assistant" && message.sources && message.sources.length > 0 && (
            <div className="pl-6 border-l-3 border-[#ffea79] space-y-3">
              <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5 font-sans">
                <FileText className="w-3.5 h-3.5" /> Source Citations:
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {message.sources.map((src, srcIdx) => (
                  <SourceCard 
                    key={srcIdx} 
                    source={src} 
                    isHighlighted={highlightedAnchor === src.anchor} 
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
