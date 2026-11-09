# Maintaining this profile

`README.md` is the single source for two pages:

- the GitHub profile page at https://github.com/concrete-sangminlee
- the Pages site at https://concrete-sangminlee.github.io/concrete-sangminlee/

The main academic site at https://concrete-sangminlee.github.io/ is built from a different repository, `concrete-sangminlee.github.io`, and is not updated from here.

## Common edits

**Add a publication.** Add a row at the top of the matching table (Journal Articles or Selected Conference Papers), newest first:

```
| 2026 | **S.M. Lee**, T. Kang. "Title." *Venue*. [[DOI](https://doi.org/10.xxxx/xxxx)] |
```

- Write the advisor as `T. H.-K. Kang` in journal articles and `T. Kang` in conference proceedings, matching how he publishes in each.
- Link `https://doi.org/<doi>` when the DOI resolves there. If it does not resolve yet, link the publisher's own `/doi/` page instead. The weekly DOI check reports when the DOI starts resolving, so you can switch the link.

**Update News.** Keep about three items, each starting with the year in bold, and link the paper when there is one.

**Edit research areas.** Use `- **Area**: description`. The bold label becomes a tag on the site and a card in the Research section.

**Style.** Avoid em dashes in README text.

## Checks

| Command | What it does | When CI runs it |
|---------|--------------|-----------------|
| `make check` | Builds the site into `docs/` and runs the unit tests. | Every pull request and every push to `main` |
| `make check-dois` | Looks up every DOI linked from the README at doi.org. It needs network access. | Pull requests that touch `README.md`, and every Monday at 03:17 UTC |

`make check-dois` fails only when a `https://doi.org/` link is not registered, because that link shows "DOI Not Found" to visitors.

## Build and deploy

- `docs/` is generated and git-ignored. Do not commit it.
- On every push to `main`, the Deploy workflow runs `make check` and publishes `docs/` to GitHub Pages.
- The build stamp and the site's modified dates come from the last commit that changed `README.md`.
- The canonical URL follows the README's "Profile Site" badge. Image and other asset URLs use this repository's Pages path, where the files are actually served.
