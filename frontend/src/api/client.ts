import axios from "axios";
import { useAuthStore } from "@/store/auth";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((cfg) => {
  const token = useAuthStore.getState().token;
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(err);
  }
);

export type Provider = "auto" | "groq" | "openrouter" | "hf" | "ollama" | "openai";

export type ChatStreamEvent =
  | { event: "meta"; data: { conversation_id: number } }
  | { event: "status"; data: { message: string } }
  | { event: "tool"; data: { name: string; args: Record<string, unknown> } }
  | { event: "token"; data: { text: string } }
  | { event: "done"; data: { answer: string; tools_used: string[]; tokens: number; latency_ms: number; provider: string; model: string } }
  | { event: "saved"; data: { message_id: number } }
  | { event: "error"; data: { message: string } };

export async function* streamChat(payload: {
  query: string;
  conversation_id?: number | null;
  provider?: Provider;
  use_rag?: boolean;
  document_ids?: number[];
}): AsyncGenerator<ChatStreamEvent> {
  const token = useAuthStore.getState().token;
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
    },
    body: JSON.stringify({ stream: true, ...payload }),
  });
  if (!res.ok || !res.body) {
    throw new Error(`Stream failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE messages are separated by \n\n
    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let eventName = "message";
      let dataLine = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLine += line.slice(5).trim();
      }
      if (!dataLine) continue;
      try {
        yield { event: eventName, data: JSON.parse(dataLine) } as ChatStreamEvent;
      } catch {
        // ignore malformed chunk
      }
    }
  }
}
