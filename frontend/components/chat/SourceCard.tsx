import React from "react";
import { ChevronRight } from "lucide-react";
import type { ChatSource } from "@/types/chat";

interface SourceCardProps {
  source: ChatSource;
  isHighlighted: boolean;
}

export function SourceCard({ source, isHighlighted }: SourceCardProps) {
  return (
    <div 
      id={source.anchor?.substring(1)}
      className={`border-2 border-black p-4 bg-white shadow-[2px_2px_0_0_#000] transition-all duration-500 relative overflow-hidden ${
        isHighlighted ? "bg-yellow-50 border-yellow-500 ring-2 ring-yellow-400 scale-[1.01]" : ""
      }`}
    >
      {isHighlighted && (
        <div className="absolute top-0 right-0 bg-yellow-400 text-black px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider border-b border-l border-black font-sans">
          Selected Citation
        </div>
      )}

      <div className="flex justify-between items-start gap-2 mb-2">
        <span className="bg-black text-white px-2 py-0.5 rounded text-[10px] font-bold font-sans">
          Citation {source.citation_index}
        </span>
        <span className="text-[10px] font-bold text-zinc-700 bg-zinc-100 px-2 py-0.5 border border-zinc-300 rounded font-sans">
          Match: {Math.round(source.score * 100)}%
        </span>
      </div>

      <div className="text-xs font-bold text-black mb-2 flex flex-wrap gap-1 items-center">
        <span className="underline">{source.act_title}</span>
        <ChevronRight className="w-3.5 h-3.5 text-zinc-400" />
        <span className="text-zinc-700 bg-zinc-100 px-1.5 py-0.5 border border-zinc-300 rounded">
          {source.citation_text}
        </span>
      </div>

      <div className="bg-zinc-50 border border-zinc-300 p-2.5 rounded text-[12px] text-zinc-700 font-mono leading-relaxed line-clamp-4 hover:line-clamp-none transition-all cursor-zoom-in">
        {source.raw_text}
      </div>
    </div>
  );
}
