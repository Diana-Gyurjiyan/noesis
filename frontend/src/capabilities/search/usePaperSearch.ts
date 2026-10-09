import { useState } from "react";
import { getPapers, getStatus, startSearch } from "../backend/api";
import type { Paper, RunStatus } from "../../types";
import type { Translation } from "../../i18n";

const POLL_INTERVAL_MS = 1500;
const SEARCH_TIMEOUT_MS = 10 * 60 * 1000;

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function usePaperSearch(
  baseUrl: string,
  demo: boolean,
  status: RunStatus,
  setStatus: (status: RunStatus) => void,
  setPapers: (update: (current: Paper[]) => Paper[]) => void,
  t: Translation,
) {
  const [searching, setSearching] = useState(false);
  const [notice, setNotice] = useState("");

  async function runSearch() {
    if (demo || searching) return;
    setSearching(true);
    setNotice("");
    const previousRun = status.last_run;
    try {
      await startSearch(baseUrl);
      const deadline = Date.now() + SEARCH_TIMEOUT_MS;
      let nextStatus = status;
      do {
        await delay(POLL_INTERVAL_MS);
        nextStatus = await getStatus(baseUrl);
        setStatus(nextStatus);
        const papers = await getPapers(baseUrl);
        setPapers(() => papers);
      } while (
        Date.now() < deadline &&
        (nextStatus.running || nextStatus.last_run === previousRun)
      );
      if (nextStatus.running || nextStatus.last_run === previousRun) {
        throw new Error("Search timed out");
      }
      if (nextStatus.error) setNotice(`${t.runFailed}: ${nextStatus.error}`);
      else if (nextStatus.warnings.length) setNotice(nextStatus.warnings.join(" · "));
    } catch {
      setNotice(t.runFailed);
    } finally {
      setSearching(false);
    }
  }

  return { searching, runSearch, notice, setNotice };
}
