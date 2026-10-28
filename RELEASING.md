# Releasing

Releases are built by GitHub Actions — no manual packaging.

1. Bump `"version"` in `custom_components/tempur_sleeptracker_ai/manifest.json`
   (semantic versioning) and commit it.
2. Run the test suite: `python -m pytest`.
3. Tag and push the tag:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
   The tag (minus the leading `v`) **must** match the manifest version —
   the Release workflow fails the build if they differ.
4. The `Release` workflow zips the integration into
   `tempur_sleeptracker_ai.zip` and creates a GitHub release with
   auto-generated notes. Edit the release notes on GitHub to highlight
   user-facing changes.
5. HACS picks up the new release automatically (see `hacs.json`:
   `zip_release` is enabled, so users install from the release zip and
   only see tagged releases, not the default branch).
