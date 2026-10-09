import PaperCard from "../components/PaperCard";
import type { Paper, RunStatus, Settings } from "../types";
import type { Translation } from "../i18n";

type PapersViewProps = {
  t: Translation;
  settings: Settings;
  status: RunStatus;
  groups: [string, Paper[]][];
  resultCount: number;
  minimumScore: number;
  favoritesOnly: boolean;
  searching: boolean;
  loading: boolean;
  demo: boolean;
  notice: string;
  progressText: string;
  onMinimumScoreChange: (score: number) => void;
  onFavoritesOnlyChange: (onlyFavorites: boolean) => void;
  onSearch: () => void;
  onOpenSettings: () => void;
  onToggleFavorite: (paper: Paper) => void;
  onDelete: (paper: Paper) => void;
};

export default function PapersView({
  t,
  settings,
  status,
  groups,
  resultCount,
  minimumScore,
  favoritesOnly,
  searching,
  loading,
  demo,
  notice,
  progressText,
  onMinimumScoreChange,
  onFavoritesOnlyChange,
  onSearch,
  onOpenSettings,
  onToggleFavorite,
  onDelete,
}: PapersViewProps) {
  const visibleGroups = groups
    .map(([cluster, groupPapers]) => [
      cluster,
      groupPapers.filter((paper) => paper.id !== status.current_paper_data?.id),
    ] as [string, Paper[]])
    .filter(([, groupPapers]) => groupPapers.length > 0);

  return (
    <section className="results-section">
      <div className="toolbar panel">
        <button className="button button-primary search-button" onClick={onSearch} disabled={demo || searching}>
          {searching ? <span className="spinner" /> : <span aria-hidden="true">↗</span>}
          {searching ? t.running : t.run}
        </button>
        <label className="score-control">
          <span>{t.scoreFilter}</span>
          <select value={minimumScore} onChange={(event) => onMinimumScoreChange(Number(event.target.value))}>
            {[0, 4, 7].map((score) => (
              <option key={score} value={score}>{score === 0 ? t.allScores : `${score}+`}</option>
            ))}
          </select>
        </label>
        <div className="paper-filter" role="group" aria-label={t.paperActions}>
          <button
            className={!favoritesOnly ? "active" : ""}
            onClick={() => onFavoritesOnlyChange(false)}
            type="button"
          >
            {t.showAll}
          </button>
          <button
            className={favoritesOnly ? "active" : ""}
            onClick={() => onFavoritesOnlyChange(true)}
            type="button"
          >
            <span aria-hidden="true">★</span> {t.favorites}
          </button>
        </div>
        <span className="result-count">{resultCount} {t.results}</span>
      </div>

      {searching && (
        <div className="search-progress" role="status" aria-live="polite">
          <span className="spinner" />
          <span className="progress-copy">
            <strong>{progressText}</strong>
            {status.current_paper && <span className="progress-paper">{status.current_paper}</span>}
          </span>
        </div>
      )}

      {status.running && status.current_paper_data && (
        <section className="active-analysis" aria-live="polite">
          <div className="group-heading">
            <h2>{t.analyzingPaper}</h2>
            <span className="spinner" />
          </div>
          <PaperCard
            paper={status.current_paper_data}
            t={t}
            analyzing
            onToggleFavorite={() => undefined}
            onDelete={() => undefined}
          />
        </section>
      )}

      {(notice || (status.warnings.length > 0 && !searching)) && (
        <div className="notice notice-info">
          <strong>{t.errors}</strong>
          <span>{notice || status.warnings.join(" · ")}</span>
        </div>
      )}

      {settings.topics.length === 0 && settings.keywords.length === 0 && !demo && (
        <div className="notice notice-warning">
          <span>{t.noKeywords}</span>
          <button className="text-button" onClick={onOpenSettings}>{t.settings} →</button>
        </div>
      )}

      {loading ? (
        <div className="empty-state panel"><span className="spinner" /><p>{t.running}</p></div>
      ) : visibleGroups.length === 0 && !(status.running && status.current_paper_data) ? (
        <div className="empty-state panel">
          <span className="empty-icon" aria-hidden="true">⌕</span>
          <h2>{favoritesOnly ? t.noFavorites : t.empty}</h2>
          <p>{t.emptyResultsHint}</p>
          {!demo && favoritesOnly
            ? <button className="button button-secondary" onClick={() => onFavoritesOnlyChange(false)}>{t.showAll}</button>
            : !demo && <button className="button button-secondary" onClick={onOpenSettings}>{t.settings}</button>}
        </div>
      ) : (
        <div className="paper-groups">
          {visibleGroups.map(([cluster, visiblePapers]) => (
            <section className="paper-group" key={cluster}>
              <div className="group-heading">
                <h2>{cluster}</h2>
                <span>{visiblePapers.length}</span>
              </div>
              <div className="paper-list">
                {[...visiblePapers]
                  .sort((a, b) => (b.analysis.relevance_score ?? 0) - (a.analysis.relevance_score ?? 0))
                  .map((paper) => (
                    <PaperCard
                      key={paper.id}
                      paper={paper}
                      t={t}
                      onToggleFavorite={() => onToggleFavorite(paper)}
                      onDelete={() => onDelete(paper)}
                    />
                  ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </section>
  );
}
