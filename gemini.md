# Gemini Operational Rules

This file tracks specific instructions and workflow behaviors that Gemini must follow when working on the Local_APK_Store project (or globally) to ensure a smooth development process.

## 1. Version Control & History (Auto-Pushing)
- **Rule:** Every time a file is modified, created, or any change is applied to the project, Gemini **must** immediately `git add .`, `git commit -m "..."`, and `git push -u origin master` to push the changes to `origin`.
- **Reasoning:** A constant, unbroken change history is required so the user doesn't need to manually worry about pushing, and we have a reliable log of all actions regardless of whether the specific code actually worked on the first try.

## 2. Line Endings (CRLF)
- **Rule:** Ensure all source files use `CRLF` (Windows style) line endings.
- **Reasoning:** Standardization across the Windows-based EliteSoftware ecosystem. Enforced via `.gitattributes`.

## 3. Continuous Changelog
- **Rule:** A `changelog.md` file must be continuously updated whenever things are changed or added to the project.
- **Reasoning:** Provides a human-readable, centralized history of new features, bug fixes, and architectural changes over time.

*(These rules are strictly enforced and continuously appended by Gemini during the session.)*
