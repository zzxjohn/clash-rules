# clash-rules
Rules from SingBox rule sets

## GitHub

[GitHub.yaml](rules/GitHub.yaml) is a Clash/Mihomo classical YAML ruleset converted from [senshinya/singbox_ruleset](https://github.com/senshinya/singbox_ruleset/blob/main/rule/GitHub/GitHub.json).

It preserves all 31 source rules: one domain keyword and 30 domain suffixes. The `github` keyword also matches hostnames outside official GitHub domains; the suffix list includes npm and Atom domains.

```yaml
rule-providers:
  github:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/zzxjohn/clash-rules/main/rules/GitHub.yaml
    path: ./ruleset/GitHub.yaml
    interval: 86400
    proxy: Proxy

rules:
  - RULE-SET,github,Proxy
  # Your other rules follow here.
```

`Proxy` must be an existing outbound or group. Put this rule before any other rule that should not take priority over GitHub traffic, including an AI provider that contains `api.github.com`.

The provider interval refreshes this hosted file only. Publishing these files does not activate the provider in any client configuration.

## Automatic synchronization

Once `.github/workflows/sync-github.yml` is committed to `main`, the **Sync GitHub ruleset** workflow checks upstream daily at 02:17 UTC (10:17 UTC+8). It also runs when the workflow, converter or tests are updated, and can be started under **Actions → Sync GitHub ruleset → Run workflow**. GitHub may delay scheduled jobs. Public-repository schedules can be disabled after 60 days without repository activity; review the Actions page if updates stop.

The workflow uses GitHub's built-in `GITHUB_TOKEN` with job-level `contents: write`. No personal access token or custom secret is required. Repository/organization Actions policy and branch protection must permit this job to commit to `main`; a rejected push fails normally and never force-pushes.

Each run tests conversion safeguards, downloads the public upstream JSON, validates its complete schema, and generates `rules/GitHub.yaml`. It retains the corresponding normalized source in `sources/GitHub.json` and records source/output hashes in `sources/GitHub.provenance.json`. It commits only when these files change. Unknown fields, duplicate keys, unsupported schema versions, empty rules and malformed values cause failure instead of silently dropping rules. A failed download or validation preserves the last published ruleset.

To check locally with Python 3 (standard library only):

```sh
python3 -m unittest discover -s tests -v
python3 scripts/sync_github.py
```

For offline conversion, use `python3 scripts/sync_github.py --source-file sources/GitHub.json`. All rule values and their ordering are preserved; generated comments and formatting differ from the original JSON.

## Source and license

The rule data comes from senshinya/singbox_ruleset, distributed under GNU GPL version 3. The upstream license text is preserved in [LICENSE](LICENSE). The conversion changes sing-box domain_keyword/domain_suffix entries into Clash DOMAIN-KEYWORD/DOMAIN-SUFFIX entries without changing their values. Conversion date: 2026-10-17.
