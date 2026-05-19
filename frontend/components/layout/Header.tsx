import React from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/retroui/Button";

interface HeaderProps {
  onClearChat: () => void;
  showReset: boolean;
}

export function Header({ onClearChat, showReset }: HeaderProps) {
  return (
    <header className="border-b-2 border-black bg-white px-6 py-4 flex items-center justify-between shadow-[0_2px_0_0_#000] z-0">
      <div className="flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full bg-green-500 border border-black animate-pulse"></span>
        <span className="font-bold text-sm tracking-wide">Semantic Citations Explorer</span>
      </div>
      {showReset && (
        <Button 
          onClick={onClearChat}
          variant="outline" 
          size="sm" 
          className="flex items-center gap-1.5 text-xs border-black shadow-[2px_2px_0_0_#000] hover:translate-y-px hover:shadow-none transition-all py-1 font-sans cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Clear Chat
        </Button>
      )}
    </header>
  );
}
