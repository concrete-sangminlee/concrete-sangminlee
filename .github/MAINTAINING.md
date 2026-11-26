# Maintaining this profile

`README.md` is the single source for two pages:

- the GitHub profile page at https://github.com/concrete-sangminlee
- the Pages site at https://concrete-sangminlee.github.io/concrete-sangminlee/

The main academic site at https://concrete-sangminlee.github.io/ is built from a different repository, `concrete-sangminlee.github.io`, and is not updated from here.

## Common edits

**Add a publication.** Add a row at the top of the matching table (Journal Articles or Selected Conference Papers), newest first:

```
| 2026 | **S.M. Lee**, T. Kang. "Title." *Venue*. [[DOI](https://doi.org/10.xxxx/xxxx)] |
| 2025 | **S.M. Lee**, T. H.-K. Kang. "Title." *Journal* 44(4). [[DOI](https://doi.org/10.xxxx/xxxx)] |
```

- Keep this exact shape: authors, the title in straight double quotes ending with a period, the venue in `*italics*`, then volume(issue) for journals. `make check` fails on a row in another shape, because the site would leave it out of its structured data.
- Keep rows newest first; `make check` fails otherwise.
- Write titles as they were published, in sentence case.
- Write the advisor as `T. H.-K. Kang` in journal articles and `T. Kang` in conference proceedings, matching how he publishes in each.
- Link `https://doi.org/<doi>` when the DOI resolves there. If it does not resolve yet, link the publisher's own `/doi/` page instead. The DOI check reports when the DOI starts resolving, so you can switch the link.

**Update News.** Keep about three items, each starting with the year in bold, and link the paper when there is one.

**Edit research areas.** Use `- **Area**: description`. The bold label becomes a tag on the site and a card in the Research section.

**Background.** One row per degree: `| **Ph.D.**, Field | Institution | Period |`. Three columns keep the table readable on phones.

**Keep the "Profile Site" badge.** The site uses it as its canonical URL. If it is renamed or removed, the canonical URL silently falls back to the first other link.

**Style.** No em dashes or en dashes anywhere in the README.

## Checks

`make lint` fails, with the line number, when README.md drifts from the shapes the site relies on: a missing title or "Profile Site" link, an em or en dash, an image without alt text, News items without a bold year or out of order, Research items not written as `**Area**: description`, publication rows that do not parse, Background rows without a bold degree, an institution and a period, Projects items not written as `**Name** (period): funder`, or patents without a bold name, a granted-year badge and a link.

| Command | What it does | When CI runs it |
|---------|--------------|-----------------|
| `make check` | Lints `README.md` (`make lint`), builds the site into `docs/`, and runs the unit tests. | Every pull request and every push to `main` |
| `make preview-image` | Builds the site, then rasterizes `docs/og-preview.svg` to `docs/og-preview.png` with a local Chrome or Chromium. Without a browser it prints a notice and skips the image. | CI runs `scripts/render_og_png.py --require` on every pull request and before every deploy, and fails if the image cannot be made |
| `make check-dois` | Looks up every DOI linked from the README at doi.org. It needs network access. | Pull requests that touch `README.md` or `scripts/check_dois.py`, every Monday at 03:17 UTC, and on demand from the Actions tab |

`make check-dois` fails when a `https://doi.org/` link is not registered, because that link shows "DOI Not Found" to visitors, and when the title registered for a DOI is clearly a different paper from the README row's title, which catches typos that land on another registered DOI. A smaller title difference is only a warning. If doi.org cannot be reached, it warns instead of failing.

The weekly scheduled run also fails when a publisher link's DOI starts resolving at doi.org, so GitHub emails you that the link can be switched.

Scheduled runs can start hours after 03:17 UTC when GitHub is busy. GitHub also disables scheduled workflows in a public repository after 60 days without activity; re-enable "Check publication DOIs" from the Actions tab if that happens.

The scripts need Python 3.11 or newer. CI uses 3.13.

## Build and deploy

- `docs/` is generated and git-ignored. Do not commit it.
- On every push to `main`, the Deploy workflow runs `make check`, renders the PNG link preview, and publishes `docs/` to GitHub Pages.
- The build stamp and the site's modified dates come from the last commit that changed `README.md`.
- The canonical URL follows the README's "Profile Site" badge. The preview image URL uses this repository's Pages path, where the file is actually served.
- The site publishes no `sitemap.xml` or `robots.txt`. It is served under a project path and names the main site as canonical, so crawlers should follow the main site's files.
