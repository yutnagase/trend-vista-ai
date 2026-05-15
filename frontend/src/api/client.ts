/** APIクライアント */

import type { AnalysisResponse, HistorySummary } from "../types";

const BASE_URL = "/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  analyze(keyword: string): Promise<AnalysisResponse> {
    return fetchJson("/analyze", {
      method: "POST",
      body: JSON.stringify({ keyword }),
    });
  },

  generateReport(id: string): Promise<{ ai_report: string }> {
    return fetchJson(`/report/${id}`, { method: "POST" });
  },

  getHistory(): Promise<HistorySummary[]> {
    return fetchJson("/history");
  },

  getHistoryDetail(id: string): Promise<AnalysisResponse> {
    return fetchJson(`/history/${id}`);
  },
};
