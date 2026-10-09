import type { Paper } from "../types";
import type { Translation } from "../i18n";

type PaperCardProps = {
  paper: Paper;
  t: Translation;
  analyzing?: boolean;
  onToggleFavorite: () => void;
  onDelete: () => void;
};

export default function PaperCard({
  paper,
  t,
  analyzing = false,
  onToggleFavorite,
  onDelete,
}: PaperCardProps) {
  const analysis = paper.analysis;
  const verdictLabels = {
    relevant: t.relevant,
    partly: t.partlyRelevant,
    not_relevant: t.notRelevant,
  };

  return (
    <article className="paper-card">
      {!analyzing && (
        <div className="paper-actions">
          <button
            className={`icon-button favorite-button${paper.favorite ? " is-favorite" : ""}`}
            type="button"
            onClick={onToggleFavorite}
            aria-label={paper.favorite ? t.unfavorite : t.favorite}
            title={paper.favorite ? t.unfavorite : t.favorite}
          >
            {paper.favorite ? "★" : "☆"}
          </button>
          <button
            className="icon-button delete-button"
            type="button"
            onClick={onDelete}
            aria-label={t.delete}
            title={t.delete}
          >
            ×
          </button>
        </div>
      )}
      {analyzing ? (
        <>
          <div className="paper-meta">
            <span>{paper.journal || t.unknownJournal}</span>
            {paper.published && <><span className="meta-divider">·</span><span>{paper.published}</span></>}
            {paper.authors && <><span className="meta-divider">·</span><span>{paper.authors}</span></>}
          </div>
          <div className="paper-title-row analyzing-title">
            <h3>{paper.title}</h3>
            <span className="analysis-progress-label">
              <span className="spinner" />
              {t.analyzingPaper}
            </span>
          </div>
        </>
      ) : analysis.error ? (
        <>
          <h3>{paper.title}</h3>
          <p className="paper-error">{analysis.error}</p>
        </>
      ) : (
        <>
          <div className="paper-meta">
            <span>{paper.journal || t.unknownJournal}</span>
            {paper.published && <><span className="meta-divider">·</span><span>{paper.published}</span></>}
            {paper.authors && <><span className="meta-divider">·</span><span>{paper.authors}</span></>}
          </div>
          <div className="paper-title-row">
            <h3>{paper.title}</h3>
            <span className={`score-badge ${analysis.verdict ?? "partly"}`}>
              <span className="score-value">{analysis.relevance_score ?? "?"}</span>
              <span>/ 10</span>
            </span>
          </div>
          <div className="paper-labels">
            {analysis.verdict && <span className={`verdict ${analysis.verdict}`}>{verdictLabels[analysis.verdict]}</span>}
            {analysis.info === "snippet" && <span className="snippet-label">{t.snippet}</span>}
          </div>
          {analysis.summary && <p className="paper-summary">{analysis.summary}</p>}
          {!!analysis.key_points?.length && <PaperList title={t.keyPoints} items={analysis.key_points} />}
          {!!analysis.why_fits?.length && <PaperList title={t.fits} items={analysis.why_fits} accent />}
          {!!analysis.why_not?.length && <PaperList title={t.notFits} items={analysis.why_not} />}
          <div className="future-work">
            <strong>{t.future}</strong>
            <p>{analysis.future_work || t.noFuture}</p>
          </div>
          {paper.url && paper.url !== "#" && (
            <a className="paper-link" href={paper.url} target="_blank" rel="noreferrer">
              {t.openPaper} <span aria-hidden="true">↗</span>
            </a>
          )}
        </>
      )}
    </article>
  );
}

function PaperList({ title, items, accent = false }: { title: string; items: string[]; accent?: boolean }) {
  return (
    <div className={`paper-detail-list${accent ? " accent" : ""}`}>
      <h4>{title}</h4>
      <ul>{items.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
    </div>
  );
}
