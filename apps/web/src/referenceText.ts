export type Passage = { start: number; end: number };
// Literal matching only: a source-ID citation contains no verified passage offsets.
export function exactPassage(source: string, claim: string): Passage | null {
  const wording = claim.trim();
  if (!wording) return null;
  const start = source.indexOf(wording);
  return start < 0 ? null : { start, end: start + wording.length };
}
export function sourceExcerpt(source: string, match: Passage | null): string {
  const start = match ? Math.max(0, match.start - 100) : 0;
  const end = match ? Math.min(source.length, match.end + 100) : Math.min(source.length, 420);
  return (start ? '…' : '') + source.slice(start, end) + (end < source.length ? '…' : '');
}
