# Documentation checks

The reader guides have an offline link and diagram check, separate from the
engine suite. From this repository's root, with Node.js satisfying
[`tooling/docs/package.json`](../tooling/docs/package.json):

```sh
npm --prefix tooling/docs ci --ignore-scripts
npm --prefix tooling/docs exec -- playwright install chromium
npm --prefix tooling/docs run verify
make test
```

On a Linux host without browser libraries, install Playwright's system dependencies
as appropriate for that host; the CI job uses `playwright install --with-deps chromium`.
Node and Chromium are maintainer documentation dependencies, not engine or adopter
runtime requirements. The lockfile pins the parser and renderer dependencies;
update it deliberately with the package manifest.

## What is checked

The `check` script in the package manifest lists the source pages: README,
developer guide, getting started, architecture, parallel development and recipes,
troubleshooting, ownership, and this page. Add a new reader guide there when linking
it from the navigation. A missing requested source fails the command.

For those sources, the check parses Markdown rather than searching fenced examples
for link-like text. It checks local Markdown links, reference links, HTML links and
images, including percent-encoded paths. Markdown heading fragments use GitHub-style
slugs, including duplicate headings; explicit HTML ids and named anchors are accepted.
Target files must exist inside the repository. Directory links are allowed without a
fragment. Fragments on non-Markdown files are rejected as unsupported. Responsive
image markup (`source[srcset]` and `img[srcset]`) is also rejected, including when
an ordinary fallback image exists. Use Markdown images or HTML `img` elements with
`src`; the checker does not parse responsive image candidate lists.

Linked Markdown targets outside the source list are read to resolve their anchors;
their outgoing links and diagrams are not recursively checked. Historical records,
workflow contracts and templates therefore do not become a new migration backlog.
Remote URLs are not fetched. This check does not establish external availability,
semantic correctness, workflow compliance or complete GitHub rendering parity.

Each Mermaid fence is parsed and rendered in Chromium using the locked Mermaid
package. Browser requests are limited to its local module assets. The check retains
PNG previews, SVGs, Mermaid source, source locations and its result under
`tooling/docs/previews/`. Open a run's `index.md` and inspect labels, clipping and
legibility; a successful render alone does not establish visual quality.

## CI and failure recovery

The `documentation` job in the [test workflow](../.github/workflows/test.yml)
runs the same `verify` command. It uploads the preview directory as the
`documentation-previews` artifact even when a later diagram fails. GitHub's artifact
retention is temporary; retain any evidence needed for a session's cleanup through
the [evidence lifecycle](agentic-dev-kit/session-cleanup.md).

A failed link names its source and destination. Fix the link or restore its intended
target; do not remove a page from the check list to hide a failure. A Mermaid failure
names the source and fence line. Use the retained `.mmd` file to reproduce it, then
run `verify` again and inspect the new preview. Dependency or browser startup failures
also fail the job; they do not count as successful diagram validation.

The check's regression tests exercise broken destinations and anchors, ignored code
examples, duplicate heading slugs, refusal of responsive image markup, and valid and
invalid browser renders. They do not
replace this repository's required `make test` verification.
