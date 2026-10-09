import type { Settings, SourceId } from "../../types";

export const DEFAULT_SETTINGS: Settings = {
  thesis: "",
  topics: [],
  keywords: [],
  journals: [],
  frequency_days: 3,
  max_found_per_run: 20,
  max_papers_per_run: 5,
  lang: "nl",
  sources: ["arxiv", "openalex", "semanticscholar", "pubmed"],
  fulltext: true,
  llm: { provider: "ollama", model: "qwen3:8b" },
};

export const SOURCES: { id: SourceId; label: string; needsKey?: string }[] = [
  { id: "arxiv", label: "arXiv" },
  { id: "openalex", label: "OpenAlex" },
  { id: "semanticscholar", label: "Semantic Scholar" },
  { id: "pubmed", label: "PubMed" },
  { id: "crossref", label: "Crossref" },
  { id: "scholar", label: "Google Scholar", needsKey: "SERPAPI_KEY" },
  { id: "web", label: "Web search", needsKey: "TAVILY_API_KEY" },
];

export function parseCommaList(value: string): string[] {
  return value.split(",").map((entry) => entry.trim()).filter(Boolean);
}
