# Changelog

All notable changes to the Local APK Store ecosystem will be documented in this file.

## [Unreleased]
### Added
- `apk_parser.py` to extract Android manifest metadata (package name, version, icon) using `pyaxmlparser`.
- Support for uploading icons and multiple screenshots in the Python backend API (`server.py`).
- `gemini.md` file to track operational instructions and automated Git pushing requirements.
- Base architecture for the Python backend (`Server/server.py`), Android client stub (`Client_App/`), and C++ Server Manager GUI (`Manager_App/`).
- Enforced CRLF line endings via `.gitattributes`.

### Changed
- **Architecture Shift (Android Client):** Transitioned away from standard `ACTION_VIEW` package installation intents. The client will now strictly require and rely on Shizuku/Dhizuku to facilitate true background/silent APK installations and version downgrades without user interaction prompts.
- `Server/server.py` now accepts multipart form data containing `icon` and multiple `screenshots` fields.
- `Server/server.py` handles preventing duplicate versions in the `db.json` file.
- Configured Git to auto-push to `origin` for all future modifications.

