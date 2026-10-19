import { useEffect, useState, type ReactNode } from 'react';
import type { components } from './api/schema';
import { request } from './api/client';
type S = components['schemas'];
const plain = (text: string) => text.replace(/\\([\\`*{}\[\]()#+\-.!|_>~])/g, '$1').replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&amp;', '&');
function Inline({ text, onNavigate }: {
  text: string;
  onNavigate: (path: string) => void;
}) {
  const nodes: ReactNode[] = [];
  const pattern = /(?<!\\)\[([^\]]+)\]\(\.\.\/(requirements|stories|provenance)\/#([a-z0-9-]+)\)/g;
  let start = 0;
  for (const match of text.matchAll(pattern)) {
    nodes.push(plain(text.slice(start, match.index)));
    nodes.push(<button type="button" key={match.index} className="text-link" onClick={() => onNavigate(`src/content/docs/${match[2]}.md`)}>{plain(match[1])}</button>);
    start = match.index + match[0].length;
  }
  nodes.push(plain(text.slice(start)));
  return <>{nodes}</>;
}
function ReadableDocument({ content, onNavigate }: {
  content: string;
  onNavigate: (path: string) => void;
}) {
  const front = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(content);
  let title = 'Documentation';
  try {
    title = JSON.parse(front?.[1].split('\n').find(line => line.startsWith('title: '))?.slice(7) || '"Documentation"');
  }
  catch { /* Treat unsupported frontmatter as source, never code. */ }
  const lines = content.slice(front?.[0].length || 0).split('\n');
  const blocks: ReactNode[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim())
      continue;
    if (/^#{1,6} /.test(line)) {
      blocks.push(<h4 key={i}>{plain(line.replace(/^#{1,6} /, ''))}</h4>);
      continue;
    }
    if (line.startsWith('> ')) { blocks.push(<blockquote key={i}>{plain(line.slice(2))}</blockquote>); continue; }
    if (line.startsWith('- ')) {
      const items = [];
      const key = i;
      while (i < lines.length && lines[i].startsWith('- ')) {
        items.push(<li key={i}><Inline text={lines[i].slice(2)} onNavigate={onNavigate} /></li>);
        i++;
      }
      i--;
      blocks.push(<ul key={key}>{items}</ul>);
      continue;
    }
    blocks.push(<p key={i}><Inline text={line} onNavigate={onNavigate} /></p>);
  }
  return <article aria-label="Packaged documentation" className="packaged-document"><h3>{typeof title === 'string' ? title : 'Documentation'}</h3>
    {blocks}</article>;
}
export function PackagePreview({ token, project, candidate }: {
  token: string;
  project: string;
  candidate: S['Candidate'];
}) {
  const [preview, setPreview] = useState<S['PackagePreview']>();
  const [path, setPath] = useState('src/content/docs/index.md');
  const [error, setError] = useState('');
  const [copyNotice, setCopyNotice] = useState('');
  const [loading, setLoading] = useState(true);
  const url = `/projects/${project}/candidates/${candidate.id}/preview`;
  useEffect(() => {
    let active = true; setLoading(true); setError(''); request<S['PackagePreview']>(token, url + `?path=${encodeURIComponent(path)}`).then(value => {
      if (value.digest !== candidate.digest)
        throw new Error('Package changed. Prepare and inspect it again.'); if (active)
        setPreview(value);
    }).catch(e => {
      if (active)
        setError(e.message);
    }).finally(() => {
      if (active)
        setLoading(false);
    }); return () => { active = false; };
  }, [token, url, path, candidate.digest]);
  return <section className="manifest" aria-label="Exact package content"><h3>Exact package preview</h3>
    <p>Read the content stored in this package. It is separate from your working draft; this view does not reproduce the website styling.</p>
    {error && <p role="alert" className="error">{error}</p>}
    <p role="status">{loading ? 'Verifying package and loading content…' : preview && !error ? 'Package integrity checked. This does not verify factual accuracy.' : ''}</p>
    {preview && !error && <><label>Documentation file<select aria-label="Documentation file" value={path} onChange={e => setPath(e.target.value)}>{preview.files.map(file => <option key={file.path} value={file.path}>{file.path.split('/').at(-1)?.replace('.md', '').replaceAll('-', ' ')}</option>)}</select></label>
      {!loading && preview.content !== null && preview.content !== undefined && <ReadableDocument content={preview.content} onNavigate={setPath} />}
      <details><summary>Document source</summary>
        <pre>{preview.content}</pre></details></>}
    <details><summary>Technical manifest</summary>
      <p>Package digest: <code>{candidate.digest}</code></p>
      <button type="button" className="secondary" onClick={() => void navigator.clipboard.writeText(candidate.digest).then(() => setCopyNotice('Package digest copied.'), () => setCopyNotice('Copy unavailable. Select the digest text to copy it.'))}>Copy package digest</button>
      <p role="status">{copyNotice}</p>
      <p>Template digest: <code>{candidate.template_digest}</code></p>
      <ul aria-label="File manifest">{Object.entries(candidate.manifest).map(([name, hash]) => <li key={name}><strong>{name}</strong>
        <code>{hash}</code></li>)}</ul></details>
  </section>;
}
