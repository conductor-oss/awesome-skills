# awesome-skills site

Static landing site for [awesome-skills](https://github.com/conductor-oss/awesome-skills). No build step.

## Preview locally

Any static file server works. From the repo root:

```bash
# Python
python3 -m http.server 8000 -d site

# Or Node, if you have it
npx serve site
```

Then open <http://localhost:8000>.

## Deploy

Designed to drop onto GitHub Pages, Cloudflare Pages, Netlify, or any static host. Point the server at `site/` and you're done — no build, no env vars.

For GitHub Pages from this repo:

1. Settings → Pages → Source: **Deploy from a branch**
2. Branch: `main` / folder: `/site`
3. Save. URL appears at the top of the page within a minute.

## Structure

```
site/
├── index.html                  # landing page
├── skills/
│   └── gtm-mavericks.html      # featured skill detail
├── assets/
│   ├── styles.css              # design system + components
│   ├── app.js                  # copy buttons + scroll reveals
│   └── favicon.svg
└── README.md
```

## Adding a new skill page

1. Drop a new file under `site/skills/<name>.html`. Copy `gtm-mavericks.html` as the starting template — it already wires up nav, fonts, and shared styles.
2. Add a card to the **Featured skill** / showcase section in `index.html`.
3. If the new skill has its own npm package, add an install row to the install block in `index.html`.

The shared CSS in `assets/styles.css` defines the design system (`--ink`, `--paper`, `--amber`, etc.) and section primitives (`.panel`, `.excerpt`, `.cap`, `.persona`, `.install-block`). Stick to those tokens so new pages stay coherent.

## Design notes

- **Type pairing:** Fraunces (variable display serif, opsz + SOFT axes) for headlines, General Sans for body, JetBrains Mono for code and labels. Loaded from Google Fonts + Fontshare CDN.
- **Palette:** warm-dark editorial — `#0E0D0B` ink, `#F1E9D6` paper, `#E8A33D` saffron amber as the signature "Conductor" accent, with sage as the secondary signal color.
- **Texture:** subtle SVG-noise grain overlay at ~4.5% opacity, mixed via `overlay` blend mode.
- **Motion:** scroll-triggered reveals via `IntersectionObserver`; pure-CSS staggered animation for the hero workflow panel. Respects `prefers-reduced-motion`.
