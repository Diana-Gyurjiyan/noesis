import type { InitialRadarData, Paper, RunStatus, Settings } from "../../types";

async function request<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, init);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function loadRadarData(baseUrl: string): Promise<InitialRadarData> {
  const [settings, papers, status] = await Promise.all([
    request<Settings>(baseUrl, "/api/settings"),
    request<Paper[]>(baseUrl, "/api/papers"),
    request<RunStatus>(baseUrl, "/api/status"),
  ]);
  return { settings, papers, status };
}

export function saveSettings(baseUrl: string, settings: Settings): Promise<Settings> {
  return request<Settings>(baseUrl, "/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}

export function startSearch(baseUrl: string): Promise<{ started: boolean }> {
  return request(baseUrl, "/api/run", { method: "POST" });
}

export function getStatus(baseUrl: string): Promise<RunStatus> {
  return request(baseUrl, "/api/status");
}

export function getPapers(baseUrl: string): Promise<Paper[]> {
  return request(baseUrl, "/api/papers");
}

export function updatePaperFavorite(
  baseUrl: string,
  paper: Paper,
  favorite: boolean,
): Promise<{ favorite: boolean }> {
  return request(baseUrl, `/api/papers/${encodeURIComponent(paper.id)}/favorite`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ favorite }),
  });
}

export function removePaper(baseUrl: string, paper: Paper): Promise<void> {
  return request(baseUrl, `/api/papers/${encodeURIComponent(paper.id)}`, {
    method: "DELETE",
  });
}
