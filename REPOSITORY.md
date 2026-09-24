# Repository configuration

Read this before changing a workflow, a branch rule or a repository
setting; writing code does not need it. `CLAUDE.md` points here rather than
carrying it, so that a session fixing a bug in the package does not hold it
in context.

The branch rules and the repository settings live *outside* the
repository. What is recorded is the settings the organization standard
asks about — the ones section 16's checklist sets on a new repository,
the ones a section of the standard states a rule for, and the ones a
behaviour it describes rests on — together with whatever a call quoted
for one of those answers alongside it. That is this file's scope, and
*What this file passes over* at the foot says what falls outside it.

The topics have a second form in the tree — `pyproject.toml`'s
`keywords` — so it is read back here for comparison rather than as the
only place the answer lives, which is what *Topics* says of it. This
tree publishes nothing yet (issue btclib-org/btclib#2220, step 2 of 5),
so it has no `homepage` and no Read the Docs subscription: *Publishing*
and *Read the Docs* below say what is deferred and to what.

**No answer is recorded here yet.** Each section carries the command that
sets its setting and the command that reads it back, and the answer is
written in under the read-back once `btclib-org/bitcoin-node-tests` exists
on GitHub and the commands have run — section 16's last step. Until then
a read-back answers `Not Found (HTTP 404)`.

## Creating the repository

The name and the calls that follow stand in blocks of their own. The
repository is public, and that is a prerequisite rather than a
preference: branch protection is a paid feature for a private repository
on the free plan.

```shell
gh repo create btclib-org/bitcoin-node-tests --public \
  --description "Bitcoin Core's functional test suite, rewritten on btclib, \
run against any node that speaks bitcoin's RPC and p2p" \
  --disable-wiki
```

`main` is pushed next, being the branch every rule below names, and the
read-back below is what says it is the default:

```shell
git push git@github.com:btclib-org/bitcoin-node-tests.git main
```

Then the switches section 11 turns off or on at the repository level, in
one call — the projects board and the wiki off, the tracker on, squash as
the only merge method with auto-merge, the head branch deleted on merge,
and the squash commit's title and body. No `homepage`: this tree ships no
documentation site yet.

```shell
gh api -X PATCH repos/btclib-org/bitcoin-node-tests \
  -F has_issues=true -F has_wiki=false -F has_projects=false \
  -F allow_squash_merge=true -F allow_merge_commit=false \
  -F allow_rebase_merge=false -F allow_auto_merge=true \
  -F delete_branch_on_merge=true \
  -f squash_merge_commit_title=COMMIT_OR_PR_TITLE \
  -f squash_merge_commit_message=COMMIT_MESSAGES
```

Read back:

```shell
gh api repos/btclib-org/bitcoin-node-tests \
  --jq '{visibility, default_branch, has_issues, wiki: .has_wiki,
         projects: .has_projects}'
gh api repos/btclib-org/bitcoin-node-tests/pages
```

`has_issues` is what `CONTRIBUTING.md`'s *The issue tracker* rests on,
and so does `.github/ISSUE_TEMPLATE/`. The Pages call is expected to
answer `404`: this tree serves no GitHub Pages site, and a recorded `404`
is what makes a later flip visible.

## Required checks on main

**Never name matrix contexts in the branch rule.** The rule lives outside
the repository, so a context that stops being produced blocks every merge
with nothing in the tree to explain why. `test: every job passed` is an
aggregate job at the end of `test.yml` that `needs` every other job there;
a new job in `test.yml` belongs in that job's `needs`, or it gates
nothing.

`main` requires these checks and nothing else:

| Check | Produced by |
| --- | --- |
| `test: every job passed` | `test.yml`, aggregate over its jobs |
| `docs / Build the documentation` | `docs.yml`, calling `reusable-docs.yml` |
| `lint / Lint and type-check` | `lint.yml`, calling `reusable-lint.yml` |

A job whose whole body is a call to a reusable workflow contributes no
name of its own: the context joins the calling job's id to the called
job's own name, so `docs.yml`'s `docs` job calling a job named `Build the
documentation` produces `docs / Build the documentation`. A context is
matched by name, not by the workflow that reported it, so moving a job is
free and renaming one is not.

No sentinel appears in the rule, and none of them may: `links.yml` and
`vendored-vectors.yml` can each go red for reasons no pull request
introduced, and a red check nobody can act on from a branch is noise.

Every required check is an Actions check, bound to the app that produces
it — `checks` with an `app_id` rather than the bare `contexts` list, 15368
for Actions — so nothing else can satisfy one.

## Branch protection

Classic protection carries the required checks with `strict`, one
approving review, `dismiss_stale_reviews`, linear history, no force
pushes, no deletions, `required_conversation_resolution`, and
`enforce_admins` **off**. The whole object is `PUT` once, here, on a
branch that has none; every later change `PATCH`es the sub-endpoint it is
about, a partial `PUT` dropping the rest:

```shell
gh api -X PUT repos/btclib-org/bitcoin-node-tests/branches/main/protection \
  --input - <<'JSON'
{"required_status_checks": {"strict": true, "checks": [
   {"context": "test: every job passed", "app_id": 15368},
   {"context": "docs / Build the documentation", "app_id": 15368},
   {"context": "lint / Lint and type-check", "app_id": 15368}]},
 "enforce_admins": false,
 "required_pull_request_reviews": {"dismiss_stale_reviews": true,
   "require_code_owner_reviews": false,
   "required_approving_review_count": 1},
 "restrictions": null,
 "required_linear_history": true,
 "allow_force_pushes": false,
 "allow_deletions": false,
 "required_conversation_resolution": true}
JSON
```

The body arrives on stdin because `-f` sends every value as a string,
where the endpoint types `app_id` as an integer.

Read back:

```shell
gh api repos/btclib-org/bitcoin-node-tests/branches/main/protection \
  --jq '{checks: [.required_status_checks.checks[] | [.context, .app_id]],
         strict: .required_status_checks.strict,
         reviews: .required_pull_request_reviews
                  | {required_approving_review_count, dismiss_stale_reviews},
         enforce_admins: .enforce_admins.enabled,
         linear: .required_linear_history.enabled,
         conversation: .required_conversation_resolution.enabled}'
```

Three rulesets sit beside it, additive — rules aggregate across rulesets
and classic protection, taking the most restrictive combination.
`main-integrity` has no bypass actor, for anyone:

```shell
gh api -X POST repos/btclib-org/bitcoin-node-tests/rulesets --input - <<'JSON'
{"name": "main-integrity", "target": "branch", "enforcement": "active",
 "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
 "bypass_actors": [],
 "rules": [{"type": "required_signatures"},
           {"type": "required_linear_history"},
           {"type": "non_fast_forward"},
           {"type": "deletion"}]}
JSON
```

`main-self-merge` requires a pull request, with the maintainer as the
only bypass actor and in **`pull_request` mode**, which excuses the
approving review a solo-maintainer repository cannot produce and nothing
else: a direct push to `main` is refused for everyone.

```shell
gh api -X POST repos/btclib-org/bitcoin-node-tests/rulesets --input - <<'JSON'
{"name": "main-self-merge", "target": "branch", "enforcement": "active",
 "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
 "bypass_actors": [{"actor_id": 3296421, "actor_type": "User",
                    "bypass_mode": "pull_request"}],
 "rules": [{"type": "pull_request", "parameters": {
   "allowed_merge_methods": ["squash"],
   "dismiss_stale_reviews_on_push": true,
   "require_code_owner_review": false,
   "require_last_push_approval": false,
   "required_approving_review_count": 1,
   "required_review_thread_resolution": true}}]}
JSON
```

`3296421` is `fametrano`'s account id,
`gh api users/fametrano --jq .id`.

## Tag protection

`tag-integrity`, `target: tag`, `refs/tags/v*`: required signatures, and
nothing else, matching every other repository of the organization even
though nothing has tagged a release here yet:

```shell
gh api -X POST repos/btclib-org/bitcoin-node-tests/rulesets --input - <<'JSON'
{"name": "tag-integrity", "target": "tag", "enforcement": "active",
 "conditions": {"ref_name": {"include": ["refs/tags/v*"], "exclude": []}},
 "bypass_actors": [],
 "rules": [{"type": "required_signatures"}]}
JSON
```

`GET /rulesets` answers a summary per ruleset, with neither `rules` nor
`bypass_actors` among its keys, so those two come from the single-ruleset
endpoint:

```shell
for id in $(gh api repos/btclib-org/bitcoin-node-tests/rulesets \
    --jq '.[].id'); do
  gh api repos/btclib-org/bitcoin-node-tests/rulesets/"$id" \
    --jq '{name, target, enforcement, include: .conditions.ref_name.include,
           rules: [.rules[].type],
           bypass: [.bypass_actors[] | [.actor_id, .bypass_mode]],
           methods: [.rules[] | select(.type=="pull_request")
                              | .parameters.allowed_merge_methods]}'
done
```

## Merge methods

**Squash is the only method GitHub can be asked for**, and auto-merge
presses it once the review and the checks are in; the call is the one
under *Creating the repository*. Read back:

```shell
gh api repos/btclib-org/bitcoin-node-tests \
  --jq '{allow_squash_merge, allow_merge_commit, allow_rebase_merge,
         allow_auto_merge, squash_merge_commit_title,
         squash_merge_commit_message, delete_branch_on_merge}'
```

`COMMIT_OR_PR_TITLE` is the subject: the pull request title with its
number, or the subject of the single commit where a branch has one.
`COMMIT_MESSAGES` is the body, and it is where a `Co-Authored-By`
trailer written in the branch's commits survives the squash.
`delete_branch_on_merge` keeps the branch list a list of live work; a
pull request closed without merging keeps its head branch.

## Token permissions

**The default `GITHUB_TOKEN` is read-only repository-wide**, so a job
needing more must declare it, and the declarations are the record of
which jobs do:

```shell
git grep -nE '^ +[a-z-]+: write([[:blank:]]+#|$)' -- .github/workflows
```

Each grant that command finds carries its reason on its own line. The
workflow-level `permissions: contents: read` every workflow declares is
belt and braces, and it is what makes the intent readable in the file.

Whether this repository pins its own default or inherits the
organization's is unreadable afterwards — no endpoint reports an
override — so it is left to inherit, and this is the call that reads the
value it gets:

```shell
gh api repos/btclib-org/bitcoin-node-tests/actions/permissions/workflow \
  --jq '{default_workflow_permissions, can_approve_pull_request_reviews}'
```

The expected answer is `read` and `false`. Where it is not, the
organization default has moved, and section 11's command is the one that
moves it back for the organization rather than here.

## Publishing

**Nothing is published yet.** No `release.yml`, no `pypi-install.yml`:
this tree is tier 2 (section 2 of the organization standard), owing what
step 4 of [ISS 2220](https://github.com/btclib-org/btclib/issues/2220)
brings.

**No `pypi` or `testpypi` environment exists on this repository.**
Section 11's own rule is that each is named by a job of the release
workflow and carries a review from that job's own gate; an environment
nothing names and nothing gates is found at the endpoint and not
recorded here, and the tree that names neither job is this one, so
neither is recorded:

```shell
gh api repos/btclib-org/bitcoin-node-tests/environments --jq .total_count
```

The two arrive together with `release.yml`, at step 4 of the same issue,
the same pull request that adds the job each environment is named by.

## Read the Docs

**Not subscribed yet.** `docs/source/` and `.readthedocs.yaml` are in
this tree from the start (section 2's *The documentation*: a tree that
builds `docs/` and subscribes no service is complete), but importing the
project on [readthedocs.org](https://app.readthedocs.org/) is a web
action under the organization-wide `read-the-docs-community` GitHub App
installation, and is the maintainer's to do — not this pull request's.
Once imported, the slug, the automation rule and the read-back commands
are `btclib-wallet`'s `REPOSITORY.md` section of the same name, applied
to this repository's own name.

## Security settings

Secret scanning, its push protection, Dependabot alerts, Dependabot
security updates and private vulnerability reporting are free on a
public repository and off by default:

```shell
gh api -X PATCH repos/btclib-org/bitcoin-node-tests --input - <<'JSON'
{"security_and_analysis": {
   "secret_scanning": {"status": "enabled"},
   "secret_scanning_push_protection": {"status": "enabled"}}}
JSON
gh api -X PUT repos/btclib-org/bitcoin-node-tests/vulnerability-alerts
gh api -X PUT repos/btclib-org/bitcoin-node-tests/automated-security-fixes
gh api -X PUT \
  repos/btclib-org/bitcoin-node-tests/private-vulnerability-reporting
```

Code scanning's **default setup** has to stay off, this tree carrying no
`codeql.yml` yet either way, and the code-quality setting beside it:

```shell
gh api -X PATCH -F state=not-configured \
  repos/btclib-org/bitcoin-node-tests/code-scanning/default-setup
gh api -X PATCH -F state=not-configured \
  repos/btclib-org/bitcoin-node-tests/code-quality/setup
```

Read back:

```shell
gh api repos/btclib-org/bitcoin-node-tests --jq '.security_and_analysis'
gh api -i repos/btclib-org/bitcoin-node-tests/vulnerability-alerts | head -1
gh api repos/btclib-org/bitcoin-node-tests/automated-security-fixes
gh api repos/btclib-org/bitcoin-node-tests/private-vulnerability-reporting
gh api repos/btclib-org/bitcoin-node-tests/code-scanning/default-setup \
  --jq .state
gh api repos/btclib-org/bitcoin-node-tests/code-quality/setup --jq .state
```

The alerts endpoint has no body and answers with its status, 204 for
enabled and 404 for not. Private vulnerability reporting is what
`.github/ISSUE_TEMPLATE/config.yml` sends a reporter to (no
`SECURITY.md`: section 2 gives that file to a tier-1 tree); with it
disabled that link is a 404.

## Topics

Section 3 makes a package's `keywords` its topics, entry for entry, so
the topics are set from `pyproject.toml` rather than typed a second time:

```shell
sed -n '/^keywords = \[/,/^]/s/^ *"\(.*\)",$/\1/p' pyproject.toml \
  | jq -R . | jq -s '{names: .}' \
  | gh api -X PUT repos/btclib-org/bitcoin-node-tests/topics --input -
```

Read back, and compared, sorted because GitHub returns topics in an order
of its own; the diff is expected empty:

```shell
diff <(gh api repos/btclib-org/bitcoin-node-tests --jq '.topics[]' | sort) \
     <(sed -n '/^keywords = \[/,/^]/s/^ *"\(.*\)",$/\1/p' pyproject.toml \
       | sort)
```

The keywords, in order: `bitcoin`, `bitcoin-core`, `conformance-testing`,
`functional-tests`, `p2p`, `rpc`.

## Plan-gated settings

**The ceiling on concurrent jobs lives here**, and nowhere else in this
tree: it is a number the plan decides rather than anything this repository
configures, so prose that needs the reasoning — a workflow header,
`CONTRIBUTING.md` — states the ceiling unnumbered and points here:

```shell
gh api orgs/btclib-org --jq .plan.name
```

[GitHub's own table](https://docs.github.com/en/actions/reference/limits)
is what turns that answer into a number, shared across every repository
in the organization. That is what every trade above spends: a check
required of a pull request holds a slot every other pull request in the
organization then waits for.

Secret scanning's non-provider patterns and validity checks need paid
Secret Protection, and the API answers a `PATCH` with 200 while leaving
them disabled. The `detect-secrets` hook is the compensating control.

## What this file passes over

The endpoints above answer for more than this repository decides, and the
scope at the top is what leaves the rest out.

**Most of the repository document is not a setting.**
`gh api repos/btclib-org/bitcoin-node-tests --jq 'keys[]'` answers with
URLs, counts, timestamps and derived state beside the switches, and the
switches among them this file records are the ones a section above reads
back with a call of its own.

**A switch no section of the standard states a rule for stays out.**
`allow_forking`, `allow_update_branch`, `has_discussions`,
`has_downloads`, `is_template` and `web_commit_signoff_required` are in
that document and no section above reads any of them back.

**A credential this repository spends and does not hold.**
`claude-review.yml` reads `secrets.CLAUDE_CODE_OAUTH_TOKEN`, which
section 11 makes an organization secret at `visibility=all` in both
stores, so the repository's own stores are expected empty and a copy in
either would be that decision undone:

```shell
gh api repos/btclib-org/bitcoin-node-tests/actions/secrets --jq .total_count
gh api repos/btclib-org/bitcoin-node-tests/dependabot/secrets --jq .total_count
```

**A switch this repository does not set.** `claude-review.yml` calls
`btclib-org/.github`'s `reusable-claude-review.yml`, whose jobs guard on
`vars.CLAUDE_REVIEW_ENABLED`; a variable set here would take precedence
over one of the same name on the organization, so the repository's own
store is read too:

```shell
gh api repos/btclib-org/bitcoin-node-tests/actions/variables --jq .total_count
```
