# Project documentation

This is a standalone static Astro Starlight project. It needs no SpecBridge process, model credentials, or API. The empty template makes no product claims; an exported snapshot supplies its reviewed content and provenance.

Use Node 22.23.1 and npm 10 on macOS/Linux (or Windows through WSL). From this directory:

```sh
npm ci
npm run dev
```

Open the loopback URL printed by Astro. To build and inspect the static site:

```sh
npm run build
npm run preview
```

The build writes `dist/`; preview serves that build on loopback. Install needs npm registry access; an offline install is not promised. The fixed scripts disable Astro telemetry for each command. No analytics, remote fonts, remote images, LLM calls, or deployment integration are configured.

## Content and review

Author plain `.md` files under `src/content/docs/`, with a YAML `title` in frontmatter. The collection intentionally loads only `.md`; do not replace it with an MDX loader. Navigation discovers the pages automatically. Keep generated text escaped: Markdown can otherwise render HTML, links and images. The template loader is not an HTML sanitizer. Do not paste untrusted content into configuration, frontmatter, npm scripts, or executable files.

An exported snapshot uses fixed pages for overview, requirements, stories, edge cases, risks, questions, and provenance. Read the included revision manifest and source mappings alongside the pages. A cited source is provenance, not independent verification. Missing information must stay explicit.

## Local Git changes

For a new extracted package, initialize its own repository once:

```sh
git init
git add .
git commit -m "Add reviewed documentation snapshot"
```

For later edits, create a branch and review the diff before committing:

```sh
git switch -c docs/update
git diff --check
git diff
npm run build
git add src/content/docs
git diff --cached
git commit -m "Update project documentation"
```

Review any configuration or lockfile changes separately and stage their exact paths intentionally. No remote is assumed; publication needs a separate decision. Do not extract another snapshot over an authored repository without comparing files first. Keep `node_modules/`, `.astro/`, `dist/`, and credentials out of Git.

## Dependency baseline

Direct dependencies are pinned in `package.json`, with the full resolution in `package-lock.json`: Astro 7.4.0 and Starlight 0.42.6 (both MIT). Starlight requires Astro `^7.2.10`; Astro requires Node `>=22.22.0`. Starlight includes an internal MDX integration, but this project's content loader accepts only `.md` files. Dependencies retain their licenses in installed packages; do not remove upstream notices when redistributing their code.

Setup follows the official [Starlight manual](https://starlight.astro.build/manual-setup/) and [Astro content loader API](https://docs.astro.build/en/reference/content-loader-reference/). Configuration is maintained as trusted source, never generated from document text.

The template applies a narrowly scoped npm override: `postcss-nested@6.2.0` uses `postcss-selector-parser@7.1.6`, fixing [GHSA-rj75-hqrm-r3gf](https://github.com/advisories/GHSA-rj75-hqrm-r3gf). Expressive Code still requests the older nesting library, so upgrading Starlight alone does not remove the affected parser. The parser's [7.0 release change](https://github.com/postcss/postcss-selector-parser/blob/v7.0.0/CHANGELOG.md) affects safe insertion during iteration; representative nesting transformations and the independent website build/browser checks verify this consumer path. Keep this override until upstream accepts a patched range, and rerun those checks when updating it. The patched lockfile audited with zero known vulnerabilities on 2026-10-16; an audit is not a guarantee against undiscovered defects.

CSS and configuration remain trusted source. Transitive native tooling includes Sharp/libvips under LGPL and Lightning CSS under MPL; the source ZIP does not vendor those binaries. Retain their notices if redistributing installed tooling.
