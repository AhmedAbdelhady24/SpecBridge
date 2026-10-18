import { useEffect, useState } from "react";
import type { components } from "./api/schema";
import { request } from "./api/client";
type Source = components["schemas"]["Source"];
type Summary = components["schemas"]["SourceSummary"];

export function EvidencePicker({
  token,
  project,
  ids,
  disabled,
  onChange,
}: {
  token: string;
  project: string;
  ids: string[];
  disabled: boolean;
  onChange: (ids: string[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [results, setResults] = useState<Summary[]>([]);
  const [known, setKnown] = useState<Record<string, string>>({});
  const [more, setMore] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const base = `/projects/${project}/sources`;
  useEffect(() => {
    let active = true;
    const missing = ids.filter((id) => !known[id]);
    if (missing.length)
      Promise.all(
        missing.map(async (id) => {
          const item = await request<Source>(
            token,
            `/projects/${project}/sources/${id}`,
          );
          return [
            id,
            item.kind === "user_provided" && !item.knowledge_ref
              ? item.text.slice(0, 320)
              : "Not original evidence — remove this reference",
          ] as const;
        }),
      )
        .then((items) => {
          if (active)
            setKnown((current) => ({
              ...current,
              ...Object.fromEntries(items),
            }));
        })
        .catch(() => {
          if (active)
            setError(
              "Some selected evidence could not be loaded. Remove unavailable references before verifying.",
            );
        });
    return () => {
      active = false;
    };
  }, [ids, known, token, project]);
  async function load(after?: string) {
    setWorking(true);
    setError("");
    const search = after ? activeQuery : query;
    try {
      const items = await request<Summary[]>(
        token,
        `${base}?query=${encodeURIComponent(search)}${after ? `&after=${encodeURIComponent(after)}` : ""}`,
      );
      setResults((current) => (after ? [...current, ...items] : items));
      setKnown((current) => ({
        ...current,
        ...Object.fromEntries(items.map((item) => [item.id, item.preview])),
      }));
      setMore(items.length === 20);
      setActiveQuery(search);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Evidence could not be loaded.",
      );
    } finally {
      setWorking(false);
    }
  }
  return (
    <fieldset className="evidence-picker" disabled={disabled || working}>
      <legend>Evidence sources</legend>
      <p>
        Choose original source evidence from this project. Selection does not
        verify a claim.
      </p>
      {!!ids.length && (
        <ul className="selected-evidence" aria-label="Selected evidence">
          {ids.map((id) => (
            <li key={id}>
              <span>{known[id] || "Loading selected source…"}</span>
              <button
                type="button"
                className="secondary"
                aria-label={`Remove evidence: ${known[id] || "unavailable source"}`}
                onClick={() => onChange(ids.filter((value) => value !== id))}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      <details
        onToggle={(event) => {
          if (event.currentTarget.open && !results.length && !working)
            void load();
        }}
      >
        <summary>Choose evidence ({ids.length} selected)</summary>
        <label>
          Search evidence
          <input
            maxLength={200}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void load();
              }
            }}
          />
        </label>
        <button type="button" className="secondary" onClick={() => void load()}>
          Find evidence
        </button>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <p role="status">
          {working
            ? "Loading evidence…"
            : `${results.length} sources shown. Select up to 20.`}
        </p>
        {!working && !results.length && (
          <p>
            No matching original sources. Add feature evidence or refine the
            search.
          </p>
        )}
        {results.map((item) => (
          <label className="check evidence-option" key={item.id}>
            <input
              type="checkbox"
              aria-label={`Use evidence: ${item.preview}`}
              checked={ids.includes(item.id)}
              disabled={!ids.includes(item.id) && ids.length >= 20}
              onChange={(event) =>
                onChange(
                  event.target.checked
                    ? [...ids, item.id]
                    : ids.filter((id) => id !== item.id),
                )
              }
            />
            <span>
              Use evidence: {item.preview}
              <small>{item.kind.replaceAll("_", " ")}</small>
            </span>
          </label>
        ))}
        {more && (
          <button
            type="button"
            className="secondary"
            onClick={() => void load(results.at(-1)!.id)}
          >
            Load more evidence
          </button>
        )}
      </details>
    </fieldset>
  );
}
