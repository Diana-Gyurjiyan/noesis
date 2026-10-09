import { useState } from "react";
import { removePaper, updatePaperFavorite } from "../backend/api";
import type { Paper } from "../../types";

export function usePaperActions(
  baseUrl: string,
  setPapers: (update: (current: Paper[]) => Paper[]) => void,
  favoriteError: string,
  deleteError: string,
) {
  const [paperToDelete, setPaperToDelete] = useState<Paper | null>(null);
  const [deletingPaper, setDeletingPaper] = useState(false);
  const [notice, setNotice] = useState("");

  async function toggleFavorite(paper: Paper) {
    const favorite = !paper.favorite;
    try {
      await updatePaperFavorite(baseUrl, paper, favorite);
      setPapers((current) =>
        current.map((entry) => entry.id === paper.id ? { ...entry, favorite } : entry),
      );
    } catch {
      setNotice(favoriteError);
    }
  }

  async function deletePaper() {
    if (!paperToDelete) return;
    setDeletingPaper(true);
    try {
      await removePaper(baseUrl, paperToDelete);
      setPapers((current) => current.filter((entry) => entry.id !== paperToDelete.id));
      setPaperToDelete(null);
      setNotice("");
    } catch {
      setNotice(deleteError);
    } finally {
      setDeletingPaper(false);
    }
  }

  return {
    paperToDelete,
    setPaperToDelete,
    deletingPaper,
    deletePaper,
    toggleFavorite,
    notice,
    setNotice,
  };
}
