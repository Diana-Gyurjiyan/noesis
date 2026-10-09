import { useMemo, useState } from "react";
import type { Language, Paper } from "../../types";

export function usePaperLibrary(papers: Paper[], language: Language) {
  const [minimumScore, setMinimumScore] = useState(0);
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const filteredPapers = useMemo(
    () => papers.filter(
      (paper) =>
        (paper.analysis.relevance_score ?? 0) >= minimumScore &&
        (!favoritesOnly || paper.favorite),
    ),
    [papers, minimumScore, favoritesOnly],
  );
  const groups = useMemo(() => {
    const grouped = new Map<string, Paper[]>();
    for (const paper of filteredPapers) {
      const cluster = paper.analysis.cluster || (language === "nl" ? "Overig" : "Other");
      grouped.set(cluster, [...(grouped.get(cluster) ?? []), paper]);
    }
    return [...grouped.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [filteredPapers, language]);

  return {
    minimumScore,
    setMinimumScore,
    favoritesOnly,
    setFavoritesOnly,
    filteredPapers,
    groups,
  };
}
