import type { ChatApiResponse } from "@/types/chat";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4001";

export async function queryLegalRAG(query: string): Promise<ChatApiResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    throw new Error(`Backend returned ${res.status}`);
  }

  return res.json();
}
