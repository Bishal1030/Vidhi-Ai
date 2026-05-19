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
            <p className="text-xs text-zinc-600 font-medium font-sans">Legal RAG Chatbot</p>
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
