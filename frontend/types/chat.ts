export interface ChatSource {
  citation_index: number;
  citation_text: string;
  act_title: string;
  section_id: string;
  section_title: string;
  subsection_id: string;
  clause_id: string;
  raw_text: string;
  score: number;
  anchor: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[];
  timestamp: string;
}

export interface ChatApiResponse {
  query: string;
  answer: string;
  sources: ChatSource[];
  error?: string;
}
