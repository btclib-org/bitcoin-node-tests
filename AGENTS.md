# Repository instructions

Follow [CONTRIBUTING.md](./CONTRIBUTING.md) for issues, pull requests,
local gates, and worktree commands. Use [REVIEWING.md](./REVIEWING.md)
for reviews, [README.md](./README.md) for the repository standard, and
[REPOSITORY.md](./REPOSITORY.md) before changing workflows or settings.
See the [organization security policy](https://github.com/btclib-org/.github/blob/main/SECURITY.md)
for vulnerability reporting.

Keep the primary checkout clean and on `main`; use a separate worktree
for each task, following the setup and cleanup commands in
`CONTRIBUTING.md`.

Choose the least capable model that can reliably complete the task: use
a fast model for straightforward execution, a reasoning-focused model
for multi-step work, and the most capable available model for difficult
or ambiguous problems. Increase capability if progress stalls.

Use [TF2.md](./TF2.md) for the ledger of Bitcoin Core test-framework
coverage and source revisions. Cite a framework file by path and
function; its revision belongs in the ledger. Do not state how many
items a file contains in `TF2.md`.
