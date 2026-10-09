import { useEffect, useState } from "react";
import { DEFAULT_SETTINGS } from "../settings/defaults";
import { DEMO_PAPERS } from "../papers/demoPapers";
import { DEFAULT_STATUS } from "../search/defaultStatus";
import { getPapers, getStatus, loadRadarData } from "./api";
import type { Paper, RunStatus, Settings } from "../../types";

export function useRadarData(baseUrl: string) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [status, setStatus] = useState<RunStatus>(DEFAULT_STATUS);
  const [demo, setDemo] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loadRadarData(baseUrl)
      .then((data) => {
        if (cancelled) return;
        setSettings(data.settings);
        setPapers(data.papers);
        setStatus(data.status);
        setDemo(false);
      })
      .catch(() => {
        if (cancelled) return;
        setDemo(true);
        setPapers(DEMO_PAPERS);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [baseUrl]);

  useEffect(() => {
    let cancelled = false;
    let polling = false;
    let wasRunning = false;
    const poll = async () => {
      if (cancelled || polling) return;
      polling = true;
      try {
        const nextStatus = await getStatus(baseUrl);
        if (cancelled) return;
        setStatus(nextStatus);
        if (nextStatus.running || wasRunning) {
          const latestPapers = await getPapers(baseUrl);
          if (!cancelled) setPapers(latestPapers);
        }
        wasRunning = nextStatus.running;
      } catch (error) {
        if (!cancelled) console.warn("Could not refresh Noesis search status", error);
      } finally {
        polling = false;
      }
    };
    const interval = window.setInterval(() => void poll(), 1500);
    void poll();
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [baseUrl]);

  return {
    settings,
    setSettings,
    papers,
    setPapers,
    status,
    setStatus,
    demo,
    loading,
  };
}
