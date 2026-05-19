"use client";

import React, { useState, useRef, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import { ChatMessages } from "@/components/chat/ChatMessages";
import { ChatInput } from "@/components/chat/ChatInput";
import { queryLegalRAG } from "@/lib/api";
import type { ChatMessage } from "@/types/chat";

export default function DashboardPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [highlightedAnchor, setHighlightedAnchor] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const highlightTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSuggestClick = (text: string) => {
    setInput(text);
  };

  const getTimestamp = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleCitationClick = (anchor: string) => {
    setHighlightedAnchor(anchor);
    
    const element = document.getElementById(anchor.substring(1));
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
      
      if (highlightTimeoutRef.current) clearTimeout(highlightTimeoutRef.current);
      
      highlightTimeoutRef.current = setTimeout(() => {
        setHighlightedAnchor(null);
      }, 3000);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      sources: [],
      timestamp: getTimestamp()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const data = await queryLegalRAG(userMessage.content);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer || "No response received.",
        sources: data.sources || [],
        timestamp: getTimestamp()
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error("RAG Query failed:", err);
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `Error: Could not reach the legal RAG service. Please check that the backend server is running. (Details: ${err.message})`,
        sources: [],
        timestamp: getTimestamp()
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setInput("");
    setLoading(false);
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-transparent">
      {/* Workspace Header */}
      <Header onClearChat={clearChat} showReset={messages.length > 0} />

      {/* Main Chat Scroll Viewport */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestClick={handleSuggestClick} />
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            <ChatMessages 
              messages={messages} 
              highlightedAnchor={highlightedAnchor} 
              onCitationClick={handleCitationClick} 
            />
            
            {loading && (
              <div className="flex justify-start">
                <div className="max-w-[70%] border-2 border-black p-5 bg-white shadow-[4px_4px_0_0_#000] rounded-xl flex items-center gap-3">
                  <RefreshCw className="w-5 h-5 animate-spin text-zinc-500" />
                  <span className="text-sm font-semibold text-zinc-600">
                    Retrieving legal documents and generating citation maps...
                  </span>
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Message Input Bar */}
      <ChatInput 
        input={input} 
        setInput={setInput} 
        onSubmit={handleSubmit} 
        loading={loading} 
      />
    </div>
  );
}
