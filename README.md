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

## Automatic synchronization for all registered sets

`rulesets.json` is the registry. The **Sync rulesets** workflow processes every entry; its `.github/workflows/sync-github.yml` filename is retained for compatibility. It checks daily at 02:17 UTC (10:17 UTC+8), supports **Actions → Sync rulesets → Run workflow**, and runs when the registry, workflow, scripts or tests change on main. GitHub may delay scheduled jobs, and public-repository schedules can be disabled after 60 days of inactivity.

The workflow uses the built-in `GITHUB_TOKEN` with job-level `contents: write`. No personal token or custom secret is required. Actions policy and branch protection must allow the job's normal commit to main. A rejected push fails without force-pushing.

### Add a future ruleset

Add an entry to the `rulesets` array in `rulesets.json`, keeping the existing entries. For example, after choosing a real source URL:

```json
{
  "name": "Example",
  "url": "https://raw.githubusercontent.com/OWNER/REPOSITORY/main/rule/Example/Example.json",
  "license": "GPL-3.0"
}
```

Names use letters, digits, underscores and hyphens, are unique ignoring case, and start with a letter or digit. URLs must use HTTPS without embedded credentials. Record the source's actual license and preserve any additional required license/attribution files when adding a source. No converter or workflow edit is needed for another supported domain ruleset.

Commit the registry update to main. The workflow downloads, validates and generates for each entry:

- `rules/NAME.yaml`: Clash/Mihomo classical YAML provider.
- `sources/NAME.json`: normalized upstream source snapshot.
- `sources/NAME.provenance.json`: source URL, license, rule count, source and output hashes.

A new provider URL will be `https://raw.githubusercontent.com/zzxjohn/clash-rules/main/rules/NAME.yaml`. Add that provider and its routing rule to the desired Clash profile separately; the registry does not choose routes or change gateway profiles.

### Conversion and failure behavior

Supported source schema: sing-box JSON version 2 with `domain`, `domain_suffix` (without a leading dot), and `domain_keyword`. Single-string shorthand and arrays are supported. All entries and their ordering are preserved. IP, regex, process, logical/inverted, and other rule types require a separate reviewed conversion; they are rejected rather than partially copied. A future ruleset name is unrestricted by the converter, but its rule types must be supported.

The complete registered batch is downloaded and validated before generated outputs are replaced. A failed source download or validation prevents the whole batch from updating and committing; the last published files remain intact. Only changed generated/source files are committed, so unchanged upstream data produces no commit. Removing a registry entry stops its synchronization; existing published files are retained until intentionally removed.

Local checks (Python 3 standard library only):

```sh
python3 -m unittest discover -s tests -v
python3 scripts/sync_rulesets.py
```

For offline validation, `python3 scripts/sync_rulesets.py --source-dir sources` expects `NAME.json` for every registered set. Override the registry using `--registry path/to/registry.json`. The old `scripts/sync_github.py` remains a compatibility entry point and delegates to the same registry-driven implementation.

## Source and license

The rule data comes from senshinya/singbox_ruleset, distributed under GNU GPL version 3. The upstream license text is preserved in [LICENSE](LICENSE). The conversion changes sing-box domain_keyword/domain_suffix entries into Clash DOMAIN-KEYWORD/DOMAIN-SUFFIX entries without changing their values. Conversion date: 2026-10-17.
