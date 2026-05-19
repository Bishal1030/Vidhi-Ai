import React from "react";
import { Sparkles, HelpCircle, CheckCircle } from "lucide-react";

interface WelcomeScreenProps {
  onSuggestClick: (text: string) => void;
}

export function WelcomeScreen({ onSuggestClick }: WelcomeScreenProps) {
  const suggestions = [
    {
      label: "Citizenship Requirements",
      text: "What are the rules for obtaining Nepalese citizenship?"
    },
    {
      label: "Fundamental Rights",
      text: "What fundamental rights are guaranteed in the constitution of Nepal?"
    },
    {
      label: "Duties of Citizens",
      text: "What duties are specified for Nepalese citizens in the constitution?"
    },
    {
      label: "Sovereignty",
      text: "Who holds the sovereignty and state power under the constitution?"
    }
  ];

  return (
    <div className="max-w-3xl mx-auto py-10 space-y-8">
      <div className="border-3 border-black p-6 bg-white shadow-[4px_4px_0_0_#000] space-y-4">
        <div className="flex items-center gap-2 text-zinc-500">
          <Sparkles className="w-5 h-5" />
          <span className="font-bold text-xs uppercase tracking-widest font-sans">Legal Assistant</span>
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight">
          Nepalese Law Explorer
        </h2>
        <p className="text-zinc-700 leading-relaxed text-sm">
          Ask questions about the Constitution of Nepal and other indexed Acts. This system provides direct, clause-level legal references and source citations.
        </p>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-zinc-200">
          <div className="flex gap-2">
            <CheckCircle className="w-4 h-4 text-zinc-700 flex-shrink-0 mt-0.5" />
            <span className="text-xs font-semibold text-zinc-600">Bilingual support (English & Nepali queries).</span>
          </div>
          <div className="flex gap-2">
            <CheckCircle className="w-4 h-4 text-zinc-700 flex-shrink-0 mt-0.5" />
            <span className="text-xs font-semibold text-zinc-600">Precise section & clause citations.</span>
          </div>
        </div>
      </div>

    </div>
  );
}
