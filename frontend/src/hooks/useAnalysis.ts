/** TanStack Query hooks */

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export function useAnalyze() {
  return useMutation({
    mutationFn: (keyword: string) => api.analyze(keyword),
  });
}

export function useHistory() {
  return useQuery({
    queryKey: ["history"],
    queryFn: () => api.getHistory(),
  });
}

export function useHistoryDetail(id: string | null) {
  return useQuery({
    queryKey: ["history", id],
    queryFn: () => api.getHistoryDetail(id ?? ""),
    enabled: !!id,
  });
}
