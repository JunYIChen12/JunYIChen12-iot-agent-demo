# Versioning Strategy

This project uses explicit semantic versions and keeps every milestone traceable.

## Version Format

```text
MAJOR.MINOR.PATCH
```

- `MAJOR`: incompatible architecture or data model changes.
- `MINOR`: new modules, new workflows, or compatible API additions.
- `PATCH`: fixes, documentation updates, small UI improvements, or safe internal changes.

Examples:

- `v0.1.0`: first runnable IoT baseline.
- `v0.2.0`: adds product/device CRUD UI and command downlink.
- `v0.3.0`: adds device shadow or external rule flow.
- `v1.0.0`: first stable demo platform with documented deployment and migration path.

## Branches

- `main`: stable runnable baseline.
- `dev`: integration branch for the next version.
- `feature/<topic>`: focused feature work.
- `fix/<topic>`: focused bug fix work.
- `release/vX.Y.Z`: release hardening branch when a version needs final testing.

For a personal demo, `main` plus `feature/*` is enough at first. Add `dev` when multiple features are active at the same time.

## Tags

Every meaningful demo milestone should be tagged:

```bash
git tag -a v0.1.0 -m "v0.1.0 first runnable IoT Agent Demo baseline"
git push origin v0.1.0
```

Tags are the safest way to return to a known demo state.

## Commit Style

Use small, descriptive commits:

```text
feat: add MQTT data worker
feat: add dashboard trend chart
docs: document topic protocol
fix: repair frontend Vite Vue plugin config
```

Avoid one giant commit once the project grows. The first baseline commit can contain the initial scaffold.

## Release Notes

Each release should have:

- `CHANGELOG.md` entry
- Optional `docs/releases/vX.Y.Z.md`
- Migration notes if database schema or topic protocol changes
- Screenshots for major UI changes

## Traceability Rules

- Do not rewrite public `main` history after pushing.
- Keep full text docs and source files in Git; do not upload compressed project archives as the primary source.
- Use `.gitignore` for generated artifacts, local dependencies, caches, and database volumes.
- Keep architecture decisions in `docs/architecture.md` or future ADR files under `docs/adr/`.
