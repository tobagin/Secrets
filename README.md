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
    The easiest way to run the application for development:
    ```bash
    ./run-dev.sh
    ```

    Or use the simple launcher:
    ```bash
    ./secrets-dev
    ```

    **Development Script Options:**
    ```bash
    ./run-dev.sh --help          # Show all options
    ./run-dev.sh                 # Run with meson devenv (default, recommended)
    ./run-dev.sh --meson         # Run with meson devenv (explicit)
    ./run-dev.sh --direct        # Run directly without meson
    ```

    **Alternative Methods:**
    ```bash
    # Run with meson run target
    meson compile -C builddir secrets-dev

    # Run the generated entry point script
    ./builddir/secrets-dev

    # Run with meson devenv directly
    meson devenv -C builddir python3 -m secrets.main

    # Run the module directly (fallback)
    python3 -m secrets.main
    ```

## Future Enhancements

This project aims to incorporate many more features from the `pass` ecosystem and enhance user experience. See the project's issue tracker or future roadmap discussions for details.

---
*This README is actively being updated as the project evolves.*
