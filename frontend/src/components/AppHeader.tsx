import type { AppView, Language } from "../types";
import type { Translation } from "../i18n";

type AppHeaderProps = {
  view: AppView;
  language: Language;
  online: boolean;
  t: Translation;
  onViewChange: (view: AppView) => void;
  onLanguageChange: (language: Language) => void;
};

export default function AppHeader({
  view,
  language,
  online,
  t,
  onViewChange,
  onLanguageChange,
}: AppHeaderProps) {
  return (
    <>
      <header className="topbar">
        <a className="brand" href="#" onClick={(event) => event.preventDefault()}>
          <img className="brand-logo" src="/noesis-achtergrond.png" alt="Noesis" />
        </a>
        <div className="topbar-actions">
          <span className={`connection ${online ? "online" : "offline"}`}>
            <span className="connection-dot" />
            {online ? t.connected : t.disconnected}
          </span>
          <label className="language-picker">
            <span className="sr-only">{t.language}</span>
            <select
              value={language}
              onChange={(event) => onLanguageChange(event.target.value as Language)}
              aria-label={t.language}
            >
              <option value="nl">NL</option>
              <option value="en">EN</option>
            </select>
          </label>
        </div>
      </header>

      <section className="intro">
        <div>
          <p className="eyebrow">{t.researchDiscovery}</p>
          <h1>{view === "papers" ? t.papers : t.settings}</h1>
          <p className="subtitle">{t.subtitle}</p>
        </div>
        <nav className="view-switch" aria-label={t.openNavigation}>
          <button className={view === "papers" ? "active" : ""} onClick={() => onViewChange("papers")}>
            {t.papers}
          </button>
          <button className={view === "settings" ? "active" : ""} onClick={() => onViewChange("settings")}>
            {t.settings}
          </button>
        </nav>
      </section>
    </>
  );
}
