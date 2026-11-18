# Git Workflow (gridgen SOP)

- `develop` is the integration branch for gridgen. All work targets `develop`, never `main`.
- Do the work on a feature branch created from the latest `origin/develop` (for example `feat/<short-description>`).
- Push the feature branch and open a pull request with `base` set to `develop`.
- Do not commit directly to `develop` or `main`, and do not open pull requests into `main`.
- If the session starts on `develop`, create a feature branch from it before committing.
