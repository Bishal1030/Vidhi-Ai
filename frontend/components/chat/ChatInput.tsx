import React from "react";
import { Send, Search } from "lucide-react";
import { Button } from "@/components/retroui/Button";

interface ChatInputProps {
  input: string;
  setInput: (text: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
}

export function ChatInput({ input, setInput, onSubmit, loading }: ChatInputProps) {
  return (
    <footer className="border-t-2 border-black bg-white p-5 sticky bottom-0 shadow-[0_-2px_0_0_#000] z-10">
      <form onSubmit={onSubmit} className="max-w-4xl mx-auto flex items-center gap-3">
        <div className="flex-1 relative">
          <input
            id="query-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about Nepalese law..."
            disabled={loading}
            className="w-full bg-white border-2 border-black p-4 pr-12 text-sm text-black rounded shadow-[3px_3px_0_0_#000] focus:outline-none focus:ring-2 focus:ring-black focus:shadow-none transition-all disabled:opacity-60 font-sans"
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400">
            <Search className="w-5 h-5" />
          </div>
        </div>
        <Button
          type="submit"
          disabled={loading || !input.trim()}
          variant="default"
          size="lg"
          className="border-2 border-black shadow-[3px_3px_0_0_#000] bg-[#ffea79] text-black hover:bg-[#ffe554] active:bg-[#ebd038] py-4 cursor-pointer"
        >
          <Send className="w-4 h-4 mr-2" />
          <span className="font-bold text-sm">Search</span>
        </Button>
      </form>
    </footer>
  );
}
