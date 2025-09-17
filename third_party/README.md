# third_party Directory

This folder records external assets that influence the Windows build. Source archives are not committed; metadata and license
texts live alongside each asset entry.

To update:

1. Pull the desired commit/tag or install version locally for verification.
2. Record metadata in `inventory.yml` (category, origin, vendor method, version/tag, license, rationale, risks).
3. Store the upstream license text in `LICENSES/<name>-<license>.txt`.
4. If code is mirrored, include a README inside the vendored directory summarizing scope and upstream URL.
5. Run `pre-commit run --all-files` to ensure YAML formatting remains valid.
