import React from "react";
import { Scale, Database, FileText, CheckCircle } from "lucide-react";

export function Sidebar() {
  return (
    <aside className="w-full md:w-80 lg:w-96 flex-shrink-0 border-b-2 md:border-b-0 md:border-r-3 border-black bg-white p-6 flex flex-col justify-between shadow-[2px_0_0_0_#000] z-10">
      <div className="flex flex-col gap-6">
        {/* Brand Header */}
        <div className="flex items-center gap-3 border-2 border-black p-3 bg-[#e8f6ff] shadow-[3px_3px_0_0_#000]">
          <div className="p-2 border-2 border-black bg-[#ffea79] rounded">
            <Scale className="w-6 h-6 text-black" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Vidhi-AI</h1>
            <p className="text-xs text-zinc-600 font-medium font-sans">Legal RAG Navigator</p>
          </div>
        </div>

        {/* Engine Status */}
        <div className="border-2 border-black p-4 bg-white shadow-[3px_3px_0_0_#000] flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-zinc-600 font-sans">RAG Engine:</span>
            <span className="flex items-center gap-1 text-green-700 bg-green-100 border border-green-500 px-2 py-0.5 rounded-full font-sans">
              <CheckCircle className="w-3 h-3" /> Online
            </span>
          </div>
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-zinc-600 font-sans">Knowledge Base:</span>
            <span className="text-black bg-zinc-100 border border-black px-2 py-0.5 rounded font-sans">
              300+ Acts
            </span>
          </div>
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-zinc-600 font-sans">Vector Database:</span>
            <span className="flex items-center gap-1 text-[#aa3bff] bg-purple-50 border border-purple-300 px-2 py-0.5 rounded font-sans">
              <Database className="w-3.5 h-3.5" /> Qdrant Cloud
            </span>
          </div>
        </div>

        {/* Loaded Indexes */}
        <div className="flex flex-col gap-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-1">
            <FileText className="w-3.5 h-3.5" /> Active Indexes
          </h2>
          <div className="border-2 border-black p-3 bg-[#fdfdfb] shadow-[2px_2px_0_0_#000]">
            <div className="flex justify-between items-start">
              <span className="font-semibold text-sm">Constitution of Nepal</span>
              <span className="text-[10px] bg-black text-white px-1.5 py-0.5 font-bold uppercase rounded font-sans">Active</span>
            </div>
            <p className="text-xs text-zinc-600 mt-1">Full hierarchical document indexed including all Articles, clauses, and schedules.</p>
          </div>
          <div className="border-2 border-dashed border-zinc-400 p-3 bg-zinc-50 text-zinc-500">
            <span className="text-xs font-medium">Additional acts queued for indexing.</span>
          </div>
        </div>
      </div>

      {/* Footer Disclaimer */}
      <div className="mt-8 pt-4 border-t border-zinc-200 text-xs text-zinc-500 flex flex-col gap-3 font-sans">
        <p className="leading-relaxed">
          <strong>Disclaimer:</strong> This AI system is developed for research and educational purposes. It does not constitute official legal advice or counsel.
        </p>
      </div>
    </aside>
  );
}
