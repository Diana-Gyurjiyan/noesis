import { useEffect, useState } from "react";
import { parseCommaList } from "./defaults";

type CommaSeparatedInputProps = {
  value: string[];
  placeholder: string;
  onDraftChange: (value: string) => void;
  onChange: (values: string[]) => void;
};

export default function CommaSeparatedInput({
  value,
  placeholder,
  onDraftChange,
  onChange,
}: CommaSeparatedInputProps) {
  const [draft, setDraft] = useState(value.join(", "));
  const committedValue = value.join(", ");

  useEffect(() => {
    setDraft(committedValue);
  }, [committedValue]);

  function commit() {
    const parsed = parseCommaList(draft);
    const normalized = parsed.join(", ");
    setDraft(normalized);
    onDraftChange(normalized);
    onChange(parsed);
  }

  return (
    <input
      value={draft}
      onChange={(event) => {
        setDraft(event.target.value);
        onDraftChange(event.target.value);
      }}
      onBlur={commit}
      placeholder={placeholder}
    />
  );
}
