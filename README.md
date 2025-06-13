# Secrets - A GTK4/Libadwaita GUI for pass

Secrets is a desktop application that provides a clean and user-friendly graphical interface for managing your passwords with `pass`, the standard unix password manager. It leverages the power and security of `pass`, GPG, and Git, wrapped in a modern GTK4/Libadwaita UI.

## Key Features

Currently implemented features include:

*   **Password Store Management:**
    *   Hierarchical tree view of your password store.
    *   Add new password entries with multiline content.
    *   Edit the full content of existing password entries.
    *   Delete password entries (with confirmation).
    *   Move or rename password entries within the store.
*   **Core Interactions:**
    *   Copy password contents to the clipboard.
    *   Full-text search of password contents (via `pass grep`).
*   **Version Control:**
    *   Basic Git integration:
        *   Pull changes from a remote repository.
        *   Push local changes to a remote repository.
*   **User Interface:**
    *   Modern interface built with GTK4 and Libadwaita.
    *   Toast notifications for feedback on actions.

## Technology Stack

*   **Programming Language:** Python
*   **UI Toolkit:** GTK4 & Libadwaita
*   **Build System:** Meson
*   **Underlying Tools:** `pass` (the standard unix password manager), GnuPG, Git

## Getting Started (Development)

1.  **Prerequisites:**
    *   Ensure `pass`, `git`, and `gpg` are installed and configured.
    *   Python >= 3.8 (or as per GTK4 requirements)
    *   Meson and Ninja build tools.
    *   GTK4 and Libadwaita development libraries.

2.  **Build:**
    ```bash
    meson setup builddir
    meson compile -C builddir
    ```

3.  **Run:**
    You can run the application directly from the source tree (after building) for development:
    ```bash
    ./run-dev.sh
    ```
    (Assuming `run-dev.sh` is a script that sets up environment variables like `PYTHONPATH` and executes `python -m secrets` or the development executable. We might need to create this script or adjust the run command, e.g., `python -m secrets` if path is set up, or directly `./builddir/secrets-dev` if that's the executable from `meson.build`.)

    Alternatively, to run the development executable directly (path might vary based on exact Meson setup):
    ```bash
    ./builddir/secrets-dev
    ```
    (Note: The executable name `secrets-dev` was defined in the root `meson.build`.)

    For the GResources to be found correctly when running uninstalled, Meson's `devenv` might be useful:
    ```bash
    meson devenv -C builddir
    # Then, from within the environment:
    # python -m secrets
    # or ./secrets-dev (if builddir is added to PATH by devenv)
    ```

## Future Enhancements

This project aims to incorporate many more features from the `pass` ecosystem and enhance user experience. See the project's issue tracker or future roadmap discussions for details.

---
*This README is actively being updated as the project evolves.*
