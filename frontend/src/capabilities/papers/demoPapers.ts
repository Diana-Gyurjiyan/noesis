import type { Paper } from "../../types";

export const DEMO_PAPERS: Paper[] = [
  {
    id: "sample-1",
    title: "Sample: Valuation multiples in healthcare buyouts",
    authors: "A. Example",
    journal: "Journal of Finance (sample)",
    published: "2026-10-07",
    url: "#",
    favorite: false,
    analysis: {
      summary: "Sample summary. Real papers will appear after the backend finds and analyzes them.",
      key_points: ["Illustrative finding one", "Illustrative finding two"],
      relevance_score: 8,
      verdict: "relevant",
      why_fits: ["Example connection to a research question"],
      why_not: ["Sample data only"],
      future_work: "Example future-work statement.",
      cluster: "Valuation",
    },
  },
];
