import type { Paper } from "../types";
import type { Translation } from "../i18n";

type DeletePaperDialogProps = {
  paper: Paper;
  deleting: boolean;
  t: Translation;
  onCancel: () => void;
  onConfirm: () => void;
};

export default function DeletePaperDialog({
  paper,
  deleting,
  t,
  onCancel,
  onConfirm,
}: DeletePaperDialogProps) {
  return (
    <div className="dialog-backdrop">
      <section
        className="delete-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <div className="dialog-heading">
          <span className="dialog-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" focusable="false">
              <path d="M4 7h16M10 11v6m4-6v6M6 7l1 14h10l1-14M9 7V4h6v3" />
            </svg>
          </span>
          <h2 id="delete-dialog-title">{t.deleteTitle}</h2>
        </div>
        <p id="delete-dialog-description">{t.confirmDelete}</p>
        <p className="dialog-paper-title">{paper.title}</p>
        <div className="dialog-actions">
          <button className="button button-secondary" type="button" onClick={onCancel} disabled={deleting}>
            {t.cancel}
          </button>
          <button className="button button-danger" type="button" onClick={onConfirm} disabled={deleting}>
            {deleting && <span className="spinner" />}
            {t.confirm}
          </button>
        </div>
      </section>
    </div>
  );
}
