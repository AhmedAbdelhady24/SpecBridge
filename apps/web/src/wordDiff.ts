export type WordChange = { text: string; kind: 'same' | 'added' | 'removed' };
export function wordDiff(before: string, after: string): WordChange[] {
  const a = before.match(/\s+|\S+/gu) || [], b = after.match(/\s+|\S+/gu) || [];
  // Bound quadratic work for long clauses; fallback still reconstructs both texts exactly.
  if (a.length * b.length > 500_000) {
    let start = 0, end = 0;
    while (start < a.length && start < b.length && a[start] === b[start]) start++;
    while (end < a.length - start && end < b.length - start && a[a.length - end - 1] === b[b.length - end - 1]) end++;
    return [
      { text: a.slice(0, start).join(''), kind: 'same' },
      { text: a.slice(start, a.length - end).join(''), kind: 'removed' },
      { text: b.slice(start, b.length - end).join(''), kind: 'added' },
      { text: a.slice(a.length - end).join(''), kind: 'same' },
    ].filter(part => part.text) as WordChange[];
  }
  const lengths = Array.from({ length: a.length + 1 }, () => new Uint32Array(b.length + 1));
  for (let i = a.length - 1; i >= 0; i--)
    for (let j = b.length - 1; j >= 0; j--)
      lengths[i][j] = a[i] === b[j] ? 1 + lengths[i + 1][j + 1] : Math.max(lengths[i + 1][j], lengths[i][j + 1]);
  const parts: WordChange[] = [];
  function push(text: string, kind: WordChange['kind']) {
    const previous = parts.at(-1);
    if (previous?.kind === kind) previous.text += text;
    else parts.push({ text, kind });
  }
  let i = 0, j = 0;
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) { push(a[i++], 'same'); j++; }
    else if (j < b.length && (i === a.length || lengths[i][j + 1] > lengths[i + 1][j])) push(b[j++], 'added');
    else push(a[i++], 'removed');
  }
  return parts;
}
