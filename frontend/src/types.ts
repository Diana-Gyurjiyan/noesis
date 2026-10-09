export type Language = "nl" | "en";
export type AppView = "papers" | "settings";
export type SourceId =
  | "arxiv"
  | "openalex"
  | "semanticscholar"
  | "pubmed"
  | "crossref"
  | "scholar"
  | "web";

export type LlmConfig = {
  provider: "ollama" | "anthropic" | "openai";
  model: string;
};

export type Settings = {
  thesis: string;
  topics: string[];
  keywords: string[];
  journals: string[];
  frequency_days: number;
  max_found_per_run: number;
  max_papers_per_run: number;
  lang: Language;
  sources: SourceId[];
  fulltext: boolean;
  llm: LlmConfig;
};

export type Analysis = {
  summary?: string;
  key_points?: string[];
  relevance_score?: number;
  verdict?: "relevant" | "partly" | "not_relevant";
  why_fits?: string[];
  why_not?: string[];
  future_work?: string | null;
  cluster?: string;
  info?: string;
  error?: string;
};

export type Paper = {
  id: string;
  title: string;
  authors: string;
  journal: string;
  published: string;
  url: string;
  favorite: boolean;
  analysis: Analysis;
};

export type RunStatus = {
  running: boolean;
  stage: string;
  papers_found: number;
  papers_analyzed: number;
  analysis_limit: number;
  current_paper: string | null;
  current_paper_data?: Paper | null;
  last_run: string | null;
  last_new: number;
  error: string | null;
  warnings: string[];
};

export type InitialRadarData = {
  settings: Settings;
  papers: Paper[];
  status: RunStatus;
};
