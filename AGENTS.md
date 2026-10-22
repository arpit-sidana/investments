# Investment workspace delivery rules

These instructions apply to this folder and every descendant. The user confirmed this standing preference on October 22, 2026.

- **Use Markdown as the default deliverable.** Write complete, dated investment reports as `.md` files that GitHub renders directly and that can be read on a phone. Keep tables reasonably narrow, retain sources, assumptions, qualifications, and essential numerical detail, and link supporting images with relative paths.
- **Save completed work to the established GitHub repository:** `https://github.com/arpit-sidana/investments`. Commit and push completed analyses, material revisions, and relevant reproducible research files as part of delivery. The user has authorized this ongoing workflow; do not ask again whether a GitHub reading copy is wanted. Exclude credentials, personal account records, caches, dependencies, and generated build output. Honor any later local-only or sharing restriction.
- **Do not start localhost previews or servers for investment analysis.** Do not make a web app the default report artifact. Do not create or deploy GitHub Pages or ChatGPT Sites unless the user explicitly requests that for the task. These user instructions take precedence over generic report/app workflows and nested scaffold defaults.
- **Use a document branch that does not deploy a site.** The repository currently publishes Pages from `main:/docs`. Use the established document branch `codex/investment-reading-copies` for this checkout; inspect current remote settings/workflows before changing destinations. Preserve existing history and unrelated files; never force-push as routine delivery.
- **Finish with a verified GitHub document link.** Confirm the saved file exists remotely and contains the completed report. A local file path, localhost URL, unpushed commit, deployment plan, or ZIP alone does not fulfill delivery. If publication is blocked, finish the local files and state the exact blocker without claiming that they were pushed.
- Maintain the repository's `README.md` report index so reports remain easy to find on a phone. Keep dated editions when creating a new report; update the same report path for revisions to that edition.

Read and apply [.agents/skills/investment-github-reading-copy/SKILL.md](.agents/skills/investment-github-reading-copy/SKILL.md) when creating or delivering investment research. This rule is scoped to this investment workspace, not unrelated projects. Another checkout named `Investments 2` uses the same GitHub repository; do not assume its local instructions automatically apply here or modify that checkout as a side effect.

## Private investment context

For personal portfolio and tax-lot analysis in this workspace, read `private-research/INVESTMENT_CONTEXT.md` when available. It is the central local context for user-confirmed account rules and dated reconciliations. Check its as-of dates before reuse. The entire `private-research/` directory is excluded from Git; do not publish its contents or referenced personal records.
