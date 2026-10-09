import { useEffect, useState, type FormEvent } from "react";
import AppHeader from "./components/AppHeader";
import DeletePaperDialog from "./components/DeletePaperDialog";
import { saveSettings } from "./capabilities/backend/api";
import { useRadarData } from "./capabilities/backend/useRadarData";
import { usePaperActions } from "./capabilities/papers/usePaperActions";
import { usePaperLibrary } from "./capabilities/papers/usePaperLibrary";
import { usePaperSearch } from "./capabilities/search/usePaperSearch";
import SettingsView from "./views/SettingsView";
import PapersView from "./views/PapersView";
import { translations } from "./i18n";
import type { AppView, Language, Paper, Settings } from "./types";

export default function App() {
  const [view, setView] = useState<AppView>("papers");
  const [language, setLanguage] = useState<Language>("nl");
  const [backendUrl, setBackendUrl] = useState(
    () => localStorage.getItem("paper-radar-backend") || "http://localhost:8000",
  );
  const [activeBackendUrl, setActiveBackendUrl] = useState(backendUrl);
  const baseUrl = activeBackendUrl.replace(/\/+$/, "");
  const t = translations[language];
  const radar = useRadarData(baseUrl);
  const library = usePaperLibrary(radar.papers, language);
  const actions = usePaperActions(
    baseUrl,
    (update) => radar.setPapers(update),
    t.favoriteFailed,
    t.deleteFailed,
  );
  const search = usePaperSearch(
    baseUrl,
    radar.demo,
    radar.status,
    radar.setStatus,
    (update) => radar.setPapers(update),
    t,
  );
  const notice = actions.notice || search.notice;
  const progressText = radar.status.running
    ? `${t[`stage_${radar.status.stage}` as keyof typeof t] ?? t.running} · ${radar.status.papers_found} ${t.progress} · ${radar.status.papers_analyzed}/${radar.status.analysis_limit} ${t.analyzed}`
    : "";

  useEffect(() => {
    localStorage.setItem("paper-radar-backend", activeBackendUrl);
  }, [activeBackendUrl]);

  useEffect(() => {
    setLanguage(radar.settings.lang);
  }, [radar.settings.lang]);

  function changeLanguage(nextLanguage: Language) {
    setLanguage(nextLanguage);
    radar.setSettings((current) => ({ ...current, lang: nextLanguage }));
  }

  async function handleSaveSettings(
    event: FormEvent<HTMLFormElement>,
    submittedSettings: Settings,
  ) {
    event.preventDefault();
    search.setNotice("");
    actions.setNotice("");
    try {
      const saved = await saveSettings(baseUrl, submittedSettings);
      radar.setSettings(saved);
      setLanguage(saved.lang);
      search.setNotice(t.saved);
    } catch {
      search.setNotice(t.saveFailed);
    }
  }

  function updateSettings(settings: Settings) {
    radar.setSettings(settings);
  }

  function deletePaper(paper: Paper) {
    actions.setPaperToDelete(paper);
  }

  return (
    <main className="app-shell">
      <AppHeader
        view={view}
        language={language}
        online={!radar.demo}
        t={t}
        onViewChange={setView}
        onLanguageChange={changeLanguage}
      />

      {radar.demo && <div className="notice notice-warning">{t.demo}</div>}

      {view === "settings" ? (
        <SettingsView
          settings={radar.settings}
          backendUrl={backendUrl}
          notice={notice}
          t={t}
          onSettingsChange={updateSettings}
          onLanguageChange={changeLanguage}
          onBackendUrlChange={setBackendUrl}
          onBackendUrlCommit={setActiveBackendUrl}
          onSave={(event, settings) => void handleSaveSettings(event, settings)}
        />
      ) : (
        <PapersView
          t={t}
          settings={radar.settings}
          status={radar.status}
          groups={library.groups}
          resultCount={library.filteredPapers.length}
          minimumScore={library.minimumScore}
          favoritesOnly={library.favoritesOnly}
          searching={search.searching}
          loading={radar.loading}
          demo={radar.demo}
          notice={notice}
          progressText={progressText}
          onMinimumScoreChange={library.setMinimumScore}
          onFavoritesOnlyChange={library.setFavoritesOnly}
          onSearch={() => void search.runSearch()}
          onOpenSettings={() => setView("settings")}
          onToggleFavorite={(paper) => void actions.toggleFavorite(paper)}
          onDelete={deletePaper}
        />
      )}

      <footer className="footer">
        <span>Noesis</span>
        <span>
          {radar.status.last_run
            ? `${t.lastSearch}: ${new Date(radar.status.last_run).toLocaleString(language)}`
            : t.none}
        </span>
      </footer>

      {actions.paperToDelete && (
        <DeletePaperDialog
          paper={actions.paperToDelete}
          deleting={actions.deletingPaper}
          t={t}
          onCancel={() => actions.setPaperToDelete(null)}
          onConfirm={() => void actions.deletePaper()}
        />
      )}
    </main>
  );
}
