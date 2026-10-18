# Reproduce README media

The screenshots are actual Playwright captures from a new synthetic fixture workspace. The video is a 30-second captioned Hyperframes montage of those screens and the original architecture SVG, without narration or music. It demonstrates local workflow behavior, not live-model quality or an unfamiliar engineer's acceptance.

Use the repository's Python/Node versions and locked environments. Install root/UI dependencies and Playwright Chromium as documented in the [root README](../../README.md). Use free ports8000/5173, or set `SPECBRIDGE_E2E_API_PORT=18000 SPECBRIDGE_E2E_WEB_PORT=15173` on the capture command to keep the owner app untouched. The extracted documentation uses a fresh ephemeral preview port with Astro daemon reuse disabled. From the repository root:

```sh
PLAYWRIGHT_BROWSERS_PATH=.cache/playwright npm exec playwright test -- --config scripts/readme-media.config.ts
npm --prefix docs/media ci --ignore-scripts
npm --prefix docs/media run check
npm --prefix docs/media run render
ffmpeg -y -i docs/media/specbridge-demo.mp4 -vf 'fps=8,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3' -loop 0 docs/media/specbridge-demo.gif
```

The capture authenticates privately before taking screenshots, disables traces/video, uses a temporary SQLite workspace, approves only its synthetic package and installs/builds the extracted fixed Starlight template. It shuts down its servers. It never loads `.env` or the owner's `.data`. Captured digests/IDs are synthetic and will change on recapture; review regenerated assets together. Template install/build errors fail capture. Temporary extracted websites are retained under the system temp directory for diagnosis.

`docs/media/index.html` and `compositions/` are the editable Hyperframes source. Screenshots, the original SVG, package manifest and lockfile are colocated so the renderer never needs parent-directory assets. `.hyperframes` state and `node_modules` are ignored. Hyperframes 0.8.171 and GSAP 3.15.0 are media-only tools, not application dependencies. Upstream licenses: [Hyperframes Apache-2.0](https://github.com/heygen-com/hyperframes/blob/dc0e80e73af185cc892ea90d5a9f1412a055e9a1/LICENSE), [GSAP standard license](https://gsap.com/standard-license/). No third-party images, fonts, music or logos were copied into the assets. The original project's distribution-license status remains unchanged.

To preview/edit locally:

```sh
HYPERFRAMES_NO_TELEMETRY=1 docs/media/node_modules/.bin/hyperframes preview docs/media --background --no-open
HYPERFRAMES_NO_TELEMETRY=1 docs/media/node_modules/.bin/hyperframes preview docs/media --stop
```

Open the URL printed by the first command. The preview can edit composition files; inspect the diff afterward. Local rendering requires FFmpeg and Chrome. Hyperframes also fetched and cached its default Inter font during compilation; first-time compilation can require network access. No font files are vendored in this repository. Hyperframes can use an existing browser via `HYPERFRAMES_BROWSER_PATH`. No hosted render, paid model call or publishing command is part of this procedure. Tool usage/quota lookup was unknown; the delivered render uses local Chrome/FFmpeg, not a hosted allowance.

MP4 is linked rather than embedded as a raw HTML video because README renderers differ. The GIF provides a broadly supported inline preview; static screenshots and SVG remain accessible when animation/video playback is unavailable. For reduced motion, use those static sections instead of the demo.
