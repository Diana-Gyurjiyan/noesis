import type { RunStatus } from "../../types";

export const DEFAULT_STATUS: RunStatus = {
  running: false,
  stage: "idle",
  papers_found: 0,
  papers_analyzed: 0,
  analysis_limit: 5,
  current_paper: null,
  current_paper_data: null,
  last_run: null,
  last_new: 0,
  error: null,
  warnings: [],
};
