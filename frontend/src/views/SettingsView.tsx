import type { FormEvent } from "react";
import { useState } from "react";
import CommaSeparatedInput from "../capabilities/settings/CommaSeparatedInput";
import { parseCommaList, SOURCES } from "../capabilities/settings/defaults";
import type { Language, LlmConfig, Settings, SourceId } from "../types";
import type { Translation } from "../i18n";

type SettingsViewProps = {
  settings: Settings;
  backendUrl: string;
  notice: string;
  t: Translation;
  onSettingsChange: (settings: Settings) => void;
  onLanguageChange: (language: Language) => void;
  onBackendUrlChange: (url: string) => void;
  onBackendUrlCommit: (url: string) => void;
  onSave: (event: FormEvent<HTMLFormElement>, settings: Settings) => void;
};

export default function SettingsView({
  settings,
  backendUrl,
  notice,
  t,
  onSettingsChange,
  onLanguageChange,
  onBackendUrlChange,
  onBackendUrlCommit,
  onSave,
}: SettingsViewProps) {
  const [topicDraft, setTopicDraft] = useState(settings.topics.join(", "));
  const [keywordDraft, setKeywordDraft] = useState(settings.keywords.join(", "));
  const [journalDraft, setJournalDraft] = useState(settings.journals.join(", "));

  function update<K extends keyof Settings>(key: K, value: Settings[K]) {
    onSettingsChange({ ...settings, [key]: value });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    const submittedSettings = {
      ...settings,
      topics: parseCommaList(topicDraft),
      keywords: parseCommaList(keywordDraft),
      journals: parseCommaList(journalDraft),
    };
    onSave(event, submittedSettings);
  }

  function toggleSource(source: SourceId) {
    const selected = settings.sources.includes(source);
    update(
      "sources",
      selected
        ? settings.sources.filter((entry) => entry !== source)
        : [...settings.sources, source],
    );
  }

  return (
    <form className="settings-card panel" onSubmit={handleSubmit}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t.personalize}</p>
          <h2>{t.settings}</h2>
        </div>
        <span className="section-number">01</span>
      </div>

      <label className="field">
        <span>{t.thesis}</span>
        <textarea
          rows={3}
          value={settings.thesis}
          onChange={(event) => update("thesis", event.target.value)}
          placeholder={t.titlePlaceholder}
        />
      </label>

      <div className="form-grid">
        <label className="field">
          <span>{t.topics}</span>
          <CommaSeparatedInput
            value={settings.topics}
            placeholder={t.commaHint}
            onDraftChange={setTopicDraft}
            onChange={(values) => {
              update("topics", values);
            }}
          />
        </label>
        <label className="field">
          <span>{t.keywords}</span>
          <CommaSeparatedInput
            value={settings.keywords}
            placeholder={t.commaHint}
            onDraftChange={setKeywordDraft}
            onChange={(values) => {
              update("keywords", values);
            }}
          />
        </label>
      </div>

      <label className="field">
        <span>{t.journals}</span>
        <CommaSeparatedInput
          value={settings.journals}
          placeholder={t.journalsHint}
          onDraftChange={setJournalDraft}
          onChange={(values) => {
            update("journals", values);
          }}
        />
      </label>

      <div className="form-grid">
        <label className="field">
          <span>{t.frequency}</span>
          <select
            value={settings.frequency_days}
            onChange={(event) => update("frequency_days", Number(event.target.value))}
          >
            {[2, 3, 7].map((days) => <option key={days} value={days}>{days} {t.days}</option>)}
          </select>
        </label>
        <label className="field">
          <span>{t.foundLimit}</span>
          <input
            type="number"
            min={1}
            max={100}
            value={settings.max_found_per_run}
            onChange={(event) => update("max_found_per_run", Math.min(100, Math.max(1, Number(event.target.value) || 1)))}
          />
        </label>
      </div>

      <div className="form-grid">
        <label className="field">
          <span>{t.paperLimit}</span>
          <input
            type="number"
            min={1}
            max={50}
            value={settings.max_papers_per_run}
            onChange={(event) => update("max_papers_per_run", Math.min(50, Math.max(1, Number(event.target.value) || 1)))}
          />
        </label>
        <label className="field">
          <span>{t.language}</span>
          <select
            value={settings.lang}
            onChange={(event) => onLanguageChange(event.target.value as Language)}
          >
            <option value="nl">Nederlands</option>
            <option value="en">English</option>
          </select>
        </label>
      </div>

      <fieldset className="field source-field">
        <legend>{t.sources}</legend>
        <div className="source-grid">
          {SOURCES.map((source) => (
            <label className="source-option" key={source.id}>
              <input
                type="checkbox"
                checked={settings.sources.includes(source.id)}
                onChange={() => toggleSource(source.id)}
              />
              <span>{source.label}</span>
              {source.needsKey && <small title={source.needsKey}>{t.apiKey}</small>}
            </label>
          ))}
        </div>
      </fieldset>

      <label className="toggle-option">
        <input
          type="checkbox"
          checked={settings.fulltext}
          onChange={(event) => update("fulltext", event.target.checked)}
        />
        <span>{t.fulltext}</span>
      </label>

      <div className="form-grid llm-grid">
        <label className="field">
          <span>{t.llmProvider}</span>
          <select
            value={settings.llm.provider}
            onChange={(event) => update("llm", {
              ...settings.llm,
              provider: event.target.value as LlmConfig["provider"],
            })}
          >
            <option value="ollama">Ollama (local, no API key)</option>
            <option value="anthropic">Anthropic (API key required)</option>
            <option value="openai">OpenAI-compatible (API key required)</option>
          </select>
        </label>
        <label className="field">
          <span>{t.llmModel}</span>
          <input
            value={settings.llm.model}
            onChange={(event) => update("llm", { ...settings.llm, model: event.target.value })}
            placeholder={settings.llm.provider === "ollama" ? "qwen3:8b" : "model name"}
            required
          />
        </label>
      </div>
      <p className="field-hint">
        {settings.llm.provider === "ollama" ? t.localLlmHint : t.hostedLlmHint}
      </p>

      <label className="field backend-field">
        <span>{t.backend}</span>
        <input
          type="url"
          value={backendUrl}
          onChange={(event) => onBackendUrlChange(event.target.value)}
          onBlur={(event) => onBackendUrlCommit(event.target.value.trim())}
          placeholder="http://localhost:8000"
        />
      </label>

      <div className="form-footer">
        {notice && <span className="form-notice" role="status">{notice}</span>}
        <button className="button button-primary" type="submit">{t.save}</button>
      </div>
    </form>
  );
}
