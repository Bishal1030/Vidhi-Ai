import React from "react";
import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-[#faf9f5] text-black font-sans selection:bg-[#ffea79]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen bg-transparent relative">
        {children}
      </div>
    </div>
  );
}
