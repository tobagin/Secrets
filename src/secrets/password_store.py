import os
import subprocess
import glob # For listing files
import re # Added
import logging
from .utils.gpg_utils import GPGSetupHelper

# GTK imports are conditional to avoid hanging in headless environments
_gtk_available = False
try:
    import gi
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gio, GLib
    _gtk_available = True
except (ImportError, ValueError):
    # GTK not available or wrong version
    pass

class PasswordStore:
    def __init__(self, store_dir=None):
        self.store_dir_override = store_dir # Store the override if provided
        self.logger = logging.getLogger(f"{__name__}.PasswordStore")
        self.store_dir = self._determine_store_dir(self.store_dir_override)
        self.gpg_health_status = None  # Will be set by validate_gpg_setup()
        # Don't raise error here immediately; let UI handle prompting.

        # Initialize metadata manager (import locally to avoid circular imports)
        from .managers.metadata_manager import MetadataManager
        self.metadata_manager = MetadataManager(self.store_dir)
        
        # Content caching system to avoid redundant decryption
        self._content_cache = {}  # path -> {'content': str, 'timestamp': float, 'mtime': float}
        self._cache_timeout = 3600  # 1 hour cache timeout for bulk processing
        self._max_cache_size = 1000  # Increased cache size for bulk operations
        
        # Bulk processing optimization
        self._bulk_processing_mode = False
        self._bulk_cache_timeout = 7200  # 2 hours during bulk processing

    def enable_bulk_processing_mode(self):
        """Enable bulk processing mode for better caching."""
        self._bulk_processing_mode = True
        self.logger.info("Enabled bulk processing mode with enhanced caching")

    def disable_bulk_processing_mode(self):
        """Disable bulk processing mode and clean up cache."""
        self._bulk_processing_mode = False
        # Optionally clean up cache when exiting bulk mode
        self._cleanup_cache()
        self.logger.info("Disabled bulk processing mode")

    def _get_effective_cache_timeout(self):
        """Get the effective cache timeout based on processing mode."""
        return self._bulk_cache_timeout if self._bulk_processing_mode else self._cache_timeout

    def _get_file_mtime(self, password_path):
        """Get the modification time of a password file."""
        try:
            full_path = os.path.join(self.store_dir, password_path + ".gpg")
            return os.path.getmtime(full_path)
        except (OSError, IOError):
            return 0

    def _is_cache_valid(self, password_path, cache_entry):
        """Check if a cache entry is still valid."""
        import time
        current_time = time.time()
        
        # Check if cache has expired using effective timeout
        effective_timeout = self._get_effective_cache_timeout()
        if current_time - cache_entry['timestamp'] > effective_timeout:
            return False
        
        # Check if file has been modified
        current_mtime = self._get_file_mtime(password_path)
        if current_mtime != cache_entry['mtime']:
            return False
        
        return True

    def _cleanup_cache(self):
        """Clean up expired cache entries and maintain size limit."""
        import time
        current_time = time.time()
        
        # Remove expired entries using effective timeout
        effective_timeout = self._get_effective_cache_timeout()
        expired_keys = []
        for path, entry in self._content_cache.items():
            if current_time - entry['timestamp'] > effective_timeout:
                expired_keys.append(path)
        
        for key in expired_keys:
            del self._content_cache[key]
        
        # If still over size limit, remove oldest entries
        if len(self._content_cache) > self._max_cache_size:
            # Sort by timestamp and remove oldest
            sorted_entries = sorted(self._content_cache.items(), key=lambda x: x[1]['timestamp'])
            entries_to_remove = len(self._content_cache) - self._max_cache_size
            
            for i in range(entries_to_remove):
                path = sorted_entries[i][0]
                del self._content_cache[path]

    def _cache_content(self, password_path, content):
        """Cache password content with metadata."""
        import time
        
        # Clean up cache first
        self._cleanup_cache()
        
        # Add new entry
        self._content_cache[password_path] = {
            'content': content,
            'timestamp': time.time(),
            'mtime': self._get_file_mtime(password_path)
        }

    def _get_cached_content(self, password_path):
        """Get cached content if available and valid."""
        if password_path not in self._content_cache:
            return None
        
        cache_entry = self._content_cache[password_path]
        
        if self._is_cache_valid(password_path, cache_entry):
            self.logger.debug(f"Cache hit for password: {password_path}")
            return cache_entry['content']
        else:
            # Remove invalid cache entry
            del self._content_cache[password_path]
            self.logger.debug(f"Cache expired for password: {password_path}")
            return None

    def invalidate_cache(self, password_path=None):
        """Invalidate cache for a specific password or all passwords."""
        if password_path:
            if password_path in self._content_cache:
                del self._content_cache[password_path]
                self.logger.debug(f"Cache invalidated for password: {password_path}")
        else:
            self._content_cache.clear()
            self.logger.debug("All password cache invalidated")

    @property
    def is_initialized(self):
        """Check if the password store is properly initialized with a .gpg-id file."""
        if not os.path.isdir(self.store_dir):
            return False
        gpg_id_file = os.path.join(self.store_dir, ".gpg-id")
        return os.path.exists(gpg_id_file)

    def _determine_store_dir(self, store_dir_override=None):
        """Determines the password store directory."""
        if store_dir_override:
            return os.path.expanduser(store_dir_override)

        # Check PASSWORD_STORE_DIR environment variable first
        env_store_dir = os.environ.get("PASSWORD_STORE_DIR")
        if env_store_dir:
            return os.path.expanduser(env_store_dir)

        # Default to ~/.password-store
        return os.path.expanduser("~/.password-store")

    def validate_complete_setup(self):
        """
        Validates the complete setup including pass, GPG, and password store.
        Returns a tuple (is_valid, status_dict) where status_dict contains:
        - 'pass_installed': bool
        - 'gpg_installed': bool
        - 'gpg_keys_exist': bool
        - 'store_gpg_id_exists': bool
        - 'store_gpg_id': str or None
        - 'error_message': str or None
        - 'suggested_action': str or None
        - 'missing_dependencies': list
        - 'setup_required': bool
        """
        status = {
            'pass_installed': False,
            'gpg_installed': False,
            'gpg_keys_exist': False,
            'store_gpg_id_exists': False,
            'store_gpg_id': None,
            'error_message': None,
            'suggested_action': None,
            'missing_dependencies': [],
            'setup_required': False
        }

        # Check if pass is installed
        if not self._is_pass_installed():
            status['missing_dependencies'].append('pass')
            status['error_message'] = "The 'pass' command is not installed"
            status['suggested_action'] = "Install pass (password-store) package"
            status['setup_required'] = True
            return False, status
        else:
            status['pass_installed'] = True

        # Check if GPG is installed
        try:
            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            result = subprocess.run(["gpg", "--version"], capture_output=True, text=True, timeout=5, env=env)
            if result.returncode == 0:
                status['gpg_installed'] = True
            else:
                status['missing_dependencies'].append('gpg')
                status['error_message'] = "GPG command failed"
                status['suggested_action'] = "Install GnuPG (gpg)"
                status['setup_required'] = True
                return False, status
        except (FileNotFoundError, subprocess.TimeoutExpired):
            status['missing_dependencies'].append('gpg')
            status['error_message'] = "GPG not found or not responding"
            status['suggested_action'] = "Install GnuPG (gpg)"
            status['setup_required'] = True
            return False, status
        except Exception as e:
            status['missing_dependencies'].append('gpg')
            status['error_message'] = f"Error checking GPG: {e}"
            status['suggested_action'] = "Check GPG installation"
            status['setup_required'] = True
            return False, status

        # Check if any GPG keys exist
        try:
            # Use a shorter timeout and add --batch flag to prevent hanging
            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            result = subprocess.run(["gpg", "--batch", "--list-secret-keys", "--with-colons"],
                                  capture_output=True, text=True, timeout=5, env=env)
            if result.returncode == 0 and result.stdout.strip():
                status['gpg_keys_exist'] = True
            else:
                status['error_message'] = "No GPG secret keys found"
                status['suggested_action'] = "Create a GPG key automatically or manually"
                status['setup_required'] = True
                return False, status
        except subprocess.TimeoutExpired:
            status['error_message'] = "GPG key listing timed out (possible lock issue)"
            status['suggested_action'] = "Restart GPG agent: gpgconf --kill gpg-agent"
            status['setup_required'] = True
            return False, status
        except Exception as e:
            status['error_message'] = f"Error listing GPG keys: {e}"
            status['suggested_action'] = "Check GPG configuration"
            status['setup_required'] = True
            return False, status

        # Check if password store has a GPG ID configured
        if self.is_initialized:
            gpg_id_file = os.path.join(self.store_dir, ".gpg-id")
            if os.path.exists(gpg_id_file):
                try:
                    with open(gpg_id_file, 'r') as f:
                        store_gpg_id = f.read().strip()
                        status['store_gpg_id'] = store_gpg_id

                        # Check if this GPG ID exists in the keyring
                        # Set up GPG environment for Flatpak compatibility
                        env = GPGSetupHelper.setup_gpg_environment()
                        result = subprocess.run(["gpg", "--batch", "--list-keys", store_gpg_id],
                                              capture_output=True, text=True, timeout=5, env=env)
                        if result.returncode == 0:
                            status['store_gpg_id_exists'] = True
                            self.gpg_health_status = status
                            return True, status
                        else:
                            status['error_message'] = f"Password store GPG key '{store_gpg_id}' not found in keyring"
                            status['suggested_action'] = f"Import the key or re-initialize store"
                            status['setup_required'] = True
                            return False, status
                except Exception as e:
                    status['error_message'] = f"Error reading .gpg-id file: {e}"
                    status['suggested_action'] = "Check password store directory permissions"
                    status['setup_required'] = True
                    return False, status
            else:
                status['error_message'] = "Password store exists but has no .gpg-id file"
                status['suggested_action'] = "Re-initialize the password store"
                status['setup_required'] = True
                return False, status
        else:
            # Store not initialized, but GPG setup is valid
            status['error_message'] = "Password store not initialized"
            status['suggested_action'] = "Initialize password store automatically"
            status['setup_required'] = True
            return False, status

    def validate_gpg_setup(self):
        """
        Backward compatibility method for GPG-only validation.
        Use validate_complete_setup() for comprehensive validation.
        """
        is_valid, status = self.validate_complete_setup()
        # Remove pass-specific fields for backward compatibility
        gpg_status = {k: v for k, v in status.items()
                     if k not in ['pass_installed', 'missing_dependencies', 'setup_required']}
        return is_valid, gpg_status

    def get_gpg_status_message(self, status=None):
        """
        Returns a user-friendly message about the current GPG setup status.
        Can be called with a status dict or will use stored status from validate_gpg_setup().
        """
        if status is None:
            status = self.gpg_health_status

        if not status:
            return "GPG status unknown. Run validation first."

        if not status['gpg_installed']:
            return "❌ GnuPG (gpg) is not installed or not working properly."

        if not status['gpg_keys_exist']:
            return "❌ No GPG keys found. You need to create a GPG key first."

        if not self.is_initialized:
            return "⚠️ Password store is not initialized. GPG is working but the store needs setup."

        if not status['store_gpg_id_exists']:
            gpg_id = status.get('store_gpg_id', 'unknown')
            return f"❌ Password store is configured for GPG key '{gpg_id}' but this key is not in your keyring."

        return "✅ GPG setup is working correctly."

    def _is_pass_installed(self):
        """Checks if the 'pass' command-line tool is installed and executable."""
        try:
            # Check if we're running in Flatpak
            is_flatpak = os.path.exists('/.flatpak-info') or 'FLATPAK_ID' in os.environ

            if is_flatpak:
                # In Flatpak, pass is bundled and always available
                return True

            # Try running a simple, non-modifying pass command like 'pass version' or 'pass help'
            # 'pass help' is generally safe and available.
            process = subprocess.run(["pass", "help"], capture_output=True, text=True, check=False, timeout=5)
            # If FileNotFoundError is not raised, pass is considered found.
            # We don't strictly need to check process.returncode here,
            # as we're only interested in whether the command itself can be executed.
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception:
            # Other potential errors during subprocess.run, assume pass is not usable.
            return False


    def ensure_store_initialized(self, parent_window=None):
        """
        Checks if the password store directory exists. If not, prompts the user
        to create it. This method is intended to be called from the UI layer.
        Returns True if the store is ready to use, False otherwise.
        """
        if self.is_initialized:
            return True

        if parent_window and _gtk_available: # Only prompt if we have a parent window and GTK is available
            dialog = Adw.Dialog(
                heading="Password Store Setup",
                body=f"The password store directory at '{self.store_dir}' does not exist.\n\nWhat would you like to do?",
                transient_for=parent_window,
                modal=True
            )
            # Note: This code uses old MessageDialog API and needs updating to work with new Adw.Dialog
            # For now, we'll use a simpler approach
            dialog.add_response("cancel", "_Cancel")
            dialog.add_response("create_and_init", "Create & _Initialize")

            # Gtk.Dialog.run() is deprecated. For Adw.MessageDialog, present and connect to response.
            # For simplicity in this step, we'll use a blocking approach if possible,
            # or adapt to an async pattern if strictly necessary.
            # Adw.MessageDialog doesn't have a direct run_sync().
            # We'll need to handle the response asynchronously or use a Gtk.Dialog for sync.
            # Let's keep it simple for now and assume a way to get a sync response or adapt.
            # For a real app, an async approach with callbacks is better.
            # This is a placeholder for a synchronous-like interaction:
            response = None
            loop = GLib.MainLoop()
            def on_response(dialog_instance, res_id):
                nonlocal response, loop
                response = res_id
                loop.quit()

            dialog.connect("response", on_response)
            dialog.present()
            loop.run() # This blocks until loop.quit() is called
            dialog.close() # Explicitly close after handling

            if response == "create_only" or response == "create_and_init":
                try:
                    os.makedirs(self.store_dir, exist_ok=True)
                    # Directory created. If only creating, self.is_initialized remains False.
                    # If initializing, proceed to get GPG ID.
                    if response == "create_and_init":
                        if not self._is_pass_installed():
                            # 'pass' command is not found, show a dialog to inform the user.
                            pass_not_found_dialog = Adw.Dialog(
                                heading="'pass' Command Not Found",
                                body="The 'pass' command-line tool was not found on your system.\n\nPlease install 'pass' (the standard unix password manager) and try again.",
                                transient_for=parent_window,
                                modal=True
                            )
                            pass_not_found_dialog.add_response("ok_pass_missing", "_OK")
                            pass_not_found_dialog.connect("response", lambda d, r: d.close())
                            pass_not_found_dialog.present()
                            # Do not proceed with GPG ID prompt or initialization.
                        else:
                            # 'pass' is installed, proceed to get GPG ID and initialize.
                            gpg_id = self._prompt_for_gpg_id(parent_window)
                            if gpg_id:
                                init_success, init_message = self.init_store(gpg_id)
                                if not init_success:
                                    # Show error from init_store attempt
                                    err_dialog = Adw.Dialog(
                                        heading="Initialization Failed",
                                        body=f"Failed to initialize the password store with GPG ID '{gpg_id}'.\n\nError: {init_message}\n\nPlease ensure the GPG ID is correct and try initializing manually from the terminal: 'pass init {gpg_id}'",
                                        transient_for=parent_window,
                                        modal=True
                                    )
                                    err_dialog.add_response("ok", "_OK")
                                    err_dialog.connect("response", lambda d, r: d.close())
                                    err_dialog.present()
                            else:
                                # User cancelled GPG ID input or entered empty GPG ID
                                pass # self.is_initialized remains False
                    # else (response == "create_only"):
                    #   Directory created, but not initialized. self.is_initialized is still False.
                    #   The main window will show a toast indicating manual init is needed.
                except OSError as e:
                    # Handle error (e.g., show another dialog)
                    self.logger.error(f"Error creating directory {self.store_dir}: {e}", extra={
                        'store_dir': self.store_dir,
                        'error_type': type(e).__name__
                    })
                    # Show error dialog for directory creation failure
                    err_dialog = Adw.Dialog(
                        heading="Directory Creation Failed",
                        body=f"Could not create the directory '{self.store_dir}'.\n\nError: {e}",
                        transient_for=parent_window,
                        modal=True
                    )
                    err_dialog.add_response("ok", "_OK")
                    err_dialog.connect("response", lambda d, r: d.close())
                    err_dialog.present()
            # Return the current state of is_initialized
            return self.is_initialized
        else:
            self.logger.warning(f"Password store directory not found: {self.store_dir}. Cannot prompt without parent window.", extra={
                'store_dir': self.store_dir
            })
            return False

    def _prompt_for_gpg_id(self, parent_window):
        if not _gtk_available:
            return None

        dialog = Adw.Dialog(
            heading="Initialize Password Store",
            body="Enter your GPG Key ID (e.g., email@example.com or a key fingerprint) to initialize the store.",
            transient_for=parent_window,
            modal=True
        )
        entry_row = Adw.EntryRow(title="GPG Key ID")
        dialog.set_extra_child(entry_row)
        dialog.add_response("cancel_init", "_Cancel")
        dialog.add_response("initialize_store_action", "_Initialize")
        dialog.set_default_response("initialize_store_action")

        # Synchronous handling for simplicity here
        response_id = None
        loop = GLib.MainLoop()
        def on_response(d, res_id):
            nonlocal response_id, loop
            response_id = res_id
            loop.quit()
        dialog.connect("response", on_response)
        dialog.present()
        loop.run()

        gpg_id_text = None
        if response_id == "initialize_store_action":
            gpg_id_text = entry_row.get_text().strip()
            if not gpg_id_text: # Basic validation
                gpg_id_text = None # Treat empty as cancel
        
        dialog.close() # Ensure dialog is closed
        return gpg_id_text

    def list_passwords(self):
        """
        Recursively scans the password store directory and returns a list of password entries.
        Each entry could be a dictionary or a custom object representing a password or folder.
        For now, it will return a flat list of paths relative to the store root.
        Ignores the .git directory and other non-password files.

        Note: This method only lists .gpg files that exist. If GPG setup is invalid,
        passwords may exist but not be accessible. Use validate_gpg_setup() to check
        for GPG-related issues.
        """
        if not self.store_dir or not os.path.isdir(self.store_dir):
            return []

        password_files = []
        # +1 to include the trailing slash if store_dir doesn't have one, for correct slicing
        root_len = len(os.path.join(self.store_dir, ''))

        for root, dirs, files in os.walk(self.store_dir, topdown=True):
            # Exclude .git directory
            if '.git' in dirs:
                dirs.remove('.git')

            for file_name in files:
                if file_name.endswith(".gpg"):
                    full_path = os.path.join(root, file_name)
                    # Get path relative to store_dir, remove .gpg extension
                    relative_path = full_path[root_len:-4]
                    password_files.append(relative_path)

        password_files.sort()
        return password_files

    def list_folders(self):
        """
        Recursively scans the password store directory and returns a list of all folders.
        Returns a flat list of folder paths relative to the store root.
        Ignores the .git directory.
        """
        if not self.store_dir or not os.path.isdir(self.store_dir):
            return []

        folders = []
        # +1 to include the trailing slash if store_dir doesn't have one, for correct slicing
        root_len = len(os.path.join(self.store_dir, ''))

        for root, dirs, files in os.walk(self.store_dir, topdown=True):
            # Exclude .git directory
            if '.git' in dirs:
                dirs.remove('.git')

            # Add all directories found
            for dir_name in dirs:
                full_path = os.path.join(root, dir_name)
                # Get path relative to store_dir
                relative_path = full_path[root_len:]
                folders.append(relative_path)

        folders.sort()
        return folders

    def copy_password(self, path_to_password):
        """
        Copies the specified password to the clipboard using `pass show -c`.
        Returns True on success, False otherwise.
        Includes the output/error message from the command.
        """
        if not path_to_password:
            return False, "Password path cannot be empty."

        # It's crucial to validate path_to_password to prevent command injection
        # if it's constructed from untrusted input. Here, we assume it's from list_passwords.
        # Ensure it doesn't contain malicious characters.
        # A simple check: ensure it's a relative path without '..' or starting with '/'
        if ".." in path_to_password or path_to_password.startswith("/"):
             return False, "Invalid password path."

        try:
            # Ensure GUI pinentry is configured for Flatpak
            GPGSetupHelper.ensure_gui_pinentry()

            # Use `pass show -c <path>`
            # The `-c` flag copies to clipboard.
            # `pass show <path>` would print to stdout.
            command = ["pass", "show", "-c", path_to_password]

            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # `pass show -c` usually outputs "Copied <password_name> to clipboard."
                return True, process.stdout.strip()
            else:
                # pass may output error messages to stderr or stdout
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error copying password: {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def git_pull(self):
        """
        Runs `pass git pull` in the password store.
        Returns True on success, False otherwise, along with output/error.
        """
        return self._run_pass_git_command(["pull"])

    def git_push(self):
        """
        Runs `pass git push` in the password store.
        Returns True on success, False otherwise, along with output/error.
        """
        return self._run_pass_git_command(["push"])

    def _run_pass_git_command(self, git_args):
        """Helper to run `pass git <args>`."""
        try:
            command = ["pass", "git"] + git_args
            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                return True, process.stdout.strip() if process.stdout else "Success"
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error running 'pass git {' '.join(git_args)}': {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def init_store(self, gpg_id):
        """
        Initializes the password store with `pass init <gpg_id>`.
        Returns True on success, False otherwise, along with output/error.
        """
        if not gpg_id:
            return False, "GPG ID cannot be empty."
        try:
            command = ["pass", "init", gpg_id]
            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # Check if .gpg-id file was created as a sign of success
                if os.path.exists(os.path.join(self.store_dir, ".gpg-id")):
                    return True, f"Password store initialized successfully with GPG ID: {gpg_id}."
                else: # pass init might return 0 but fail to create .gpg-id if GPG ID is invalid
                    return False, f"'{gpg_id}' may not be a valid GPG ID or GPG setup issue. Store not fully initialized."
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error initializing password store: {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred during initialization: {e}"

    def delete_password(self, path_to_password):
        """
        Deletes the specified password using `pass rm --force`.
        Returns True on success, False otherwise.
        Includes the output/error message from the command.
        """
        if not path_to_password:
            return False, "Password path cannot be empty."

        # Validate path_to_password to prevent issues.
        if ".." in path_to_password or path_to_password.startswith("/"):
             return False, "Invalid password path."

        try:
            # Use `pass rm --force <path>`
            # The `--force` flag bypasses confirmation from `pass` itself,
            # as we'll handle confirmation in the GUI.
            command = ["pass", "rm", "--force", path_to_password]

            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # `pass rm` might not output much on success
                # Invalidate cache for this password since it was deleted
                self.invalidate_cache(path_to_password)
                return True, f"Successfully deleted '{path_to_password}'."
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error deleting password '{path_to_password}': {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred while deleting: {e}"

    def get_password_content(self, path_to_password):
        """
        Retrieves the content of the specified password file using `pass show`.
        Returns a tuple (success_bool, content_or_error_string).
        Uses caching to avoid redundant decryption operations.
        """
        if not path_to_password:
            return False, "Password path cannot be empty."

        if ".." in path_to_password or path_to_password.startswith("/"):
             return False, "Invalid password path."

        # Check cache first
        cached_content = self._get_cached_content(path_to_password)
        if cached_content is not None:
            return True, cached_content

        try:
            # Ensure GUI pinentry is configured for Flatpak
            GPGSetupHelper.ensure_gui_pinentry()

            # Use `pass show <path>` (without -c, so it prints to stdout)
            command = ["pass", "show", path_to_password]

            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # The first line is the password, subsequent lines are extra data.
                # `pass show` outputs the full content of the decrypted file.
                content = process.stdout
                
                # Cache the content for future use
                self._cache_content(path_to_password, content)
                
                return True, content
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error showing password '{path_to_password}': {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred while showing password: {e}"

    def get_bulk_password_contents(self, password_paths, max_workers=8):
        """
        Retrieve multiple password contents efficiently using threading and caching.
        Uses bulk processing mode to extend cache timeouts.
        Implements sequential processing for first few passwords to establish GPG session.
        
        Args:
            password_paths: List of password paths to retrieve
            max_workers: Maximum number of worker threads
            
        Returns:
            Dict mapping password_path -> (success, content_or_error)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        # Enable bulk processing mode for better caching
        self.enable_bulk_processing_mode()
        
        # Pre-warm GPG agent to establish session before bulk processing
        from .utils.gpg_utils import GPGSetupHelper
        warm_success, warm_message = GPGSetupHelper.warm_gpg_agent()
        if warm_success:
            self.logger.info(f"GPG agent pre-warmed: {warm_message}")
        else:
            self.logger.warning(f"GPG agent warming failed: {warm_message}")
        
        results = {}
        cached_results = {}
        uncached_paths = []
        
        # First, check which passwords are already cached
        for path in password_paths:
            cached_content = self._get_cached_content(path)
            if cached_content is not None:
                cached_results[path] = (True, cached_content)
            else:
                uncached_paths.append(path)
        
        self.logger.info(f"Bulk processing: {len(cached_results)} cached, {len(uncached_paths)} need decryption")
        
        if uncached_paths:
            # Process first 3 passwords sequentially to establish GPG session and cache passphrase
            sequential_paths = uncached_paths[:3]
            parallel_paths = uncached_paths[3:]
            
            self.logger.info(f"Processing {len(sequential_paths)} passwords sequentially to establish GPG session")
            
            # Sequential processing for session establishment
            for path in sequential_paths:
                try:
                    success, content = self.get_password_content(path)
                    results[path] = (success, content)
                    if success:
                        self.logger.debug(f"Successfully established GPG session with {path}")
                    else:
                        self.logger.warning(f"Failed to establish GPG session with {path}: {content}")
                    
                    # Small delay between sequential operations to let GPG agent stabilize
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process password {path} sequentially: {e}")
                    results[path] = (False, f"Processing failed: {e}")
            
            # Now process remaining passwords in parallel with very limited concurrency
            if parallel_paths:
                self.logger.info(f"Processing remaining {len(parallel_paths)} passwords in parallel")
                # Use very conservative concurrency to avoid overwhelming GPG agent
                max_parallel_workers = min(2, max_workers, len(parallel_paths))
                
                with ThreadPoolExecutor(max_workers=max_parallel_workers) as executor:
                    # Submit remaining password retrieval tasks
                    future_to_path = {
                        executor.submit(self.get_password_content, path): path 
                        for path in parallel_paths
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_path):
                        path = future_to_path[future]
                        try:
                            success, content = future.result(timeout=45)  # Longer timeout for parallel processing
                            results[path] = (success, content)
                        except Exception as e:
                            self.logger.warning(f"Failed to process password {path}: {e}")
                            results[path] = (False, f"Processing failed: {e}")
        
        # Combine cached and newly retrieved results
        results.update(cached_results)
        
        self.logger.info(f"Bulk processing complete: {len(results)} total passwords processed")
        
        # Keep bulk processing mode enabled for the session
        # It will be disabled when the controller is done with bulk operations
        
        return results

    def get_password_path_and_content(self, path_to_password):
        """
        Retrieves the path and content of the specified password file.
        Returns a dictionary {'path': path, 'content': content_string} on success,
        or {'error': error_message_string} on failure.
        """
        success, content_or_error = self.get_password_content(path_to_password)

        if success:
            return {'path': path_to_password, 'content': content_or_error}
        else:
            # content_or_error is already the error message string here
            return {'error': content_or_error}

    def insert_password(self, path_to_password, content, multiline=True, force=True):
        """
        Inserts or updates a password using `pass insert`.
        - path_to_password: The path for the password entry.
        - content: The full content to be inserted.
        - multiline: If True, uses -m flag for multiline input.
        - force: If True, uses -f flag to overwrite if exists (useful for updates).
        Returns True on success, False otherwise, along with an output/error message.
        """
        if not path_to_password:
            return False, "Password path cannot be empty."

        # Basic validation for the path
        if ".." in path_to_password or path_to_password.startswith("/"):
             return False, "Invalid password path."

        try:
            # Ensure GUI pinentry is configured for Flatpak
            GPGSetupHelper.ensure_gui_pinentry()

            command = ["pass", "insert"]
            if multiline:
                command.append("-m") # or --multiline
            if force:
                command.append("-f") # or --force
            command.append(path_to_password)

            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            # The content needs to be passed via stdin to the `pass insert` command
            # Add timeout to prevent hanging
            process = subprocess.run(command, input=content, capture_output=True, text=True, check=False, env=env, timeout=30)

            if process.returncode == 0:
                # `pass insert` might not output much on success
                # Invalidate cache for this password since it was modified
                self.invalidate_cache(path_to_password)
                return True, f"Successfully saved '{path_to_password}'."
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error saving password '{path_to_password}': {error_message}"
        except subprocess.TimeoutExpired:
            return False, "The 'pass' command timed out. This might be due to GPG waiting for a passphrase or running in a sandboxed environment."
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred while saving: {e}"

    def search_passwords(self, query):
        """
        Searches passwords using `pass grep`.
        Returns a tuple (success_bool, list_of_matching_paths_or_error_string).
        `pass grep` outputs matching entry names, one per line.
        """
        if not query:
            return False, "Search query cannot be empty."

        try:
            # Ensure GUI pinentry is configured for Flatpak
            GPGSetupHelper.ensure_gui_pinentry()

            # Use `pass grep <query>`
            # Note: `pass grep` can be slow on very large stores.
            # It searches the content of encrypted files.
            command = ["pass", "grep", query] # Add any other flags if needed, e.g. -i for case-insensitive

            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # Output is a list of matching password names, one per line.
                # Need to strip empty lines that might result from splitlines()
                matching_paths = [line for line in process.stdout.splitlines() if line.strip()]
                return True, matching_paths
            elif process.returncode == 1: # `grep` returns 1 if no lines were selected
                return True, [] # No matches found is not an error in this context
            else:
                # Other return codes indicate an error with `pass` or `grep` itself
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error searching passwords: {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred during search: {e}"

    def move_password(self, old_path, new_path, preserve_empty_folders=True):
        """
        Moves/renames a password entry using `pass mv`.

        Args:
            old_path (str): Current path of the password
            new_path (str): New path for the password
            preserve_empty_folders (bool): If True, preserve empty folders after move

        Returns:
            tuple: (success: bool, message: str)
        """
        if not old_path or not new_path:
            return False, "Old and new paths cannot be empty."

        # Basic validation for paths
        if ".." in old_path or old_path.startswith("/") or            ".." in new_path or new_path.startswith("/"):
             return False, "Invalid old or new path."

        if old_path == new_path:
            return False, "Old and new paths cannot be the same."

        # Store the old folder path for preservation check
        old_folder = os.path.dirname(old_path) if '/' in old_path else ""

        try:
            command = ["pass", "mv", old_path, new_path]

            # Set up GPG environment for Flatpak compatibility
            env = GPGSetupHelper.setup_gpg_environment()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # If preserve_empty_folders is True and we moved from a folder,
                # check if the old folder is now empty and recreate it if needed
                if preserve_empty_folders and old_folder:
                    self._preserve_empty_folder_after_move(old_folder)

                return True, f"Successfully moved '{old_path}' to '{new_path}'."
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error moving password: {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred while moving: {e}"

    def _preserve_empty_folder_after_move(self, folder_path):
        """
        Preserve an empty folder after a move operation by recreating it if it was removed.

        Args:
            folder_path (str): The folder path to preserve
        """
        if not folder_path:
            return

        try:
            full_folder_path = os.path.join(self.store_dir, folder_path)

            # Check if the folder no longer exists
            if not os.path.exists(full_folder_path):
                # Recreate the empty folder
                os.makedirs(full_folder_path, exist_ok=True)

        except Exception:
            # Silently ignore errors in folder preservation
            # This is a best-effort operation
            pass

    def create_folder(self, folder_path):
        """
        Create a folder in the password store.

        Args:
            folder_path (str): The path of the folder to create (e.g., "websites", "email/work")

        Returns:
            tuple: (success: bool, message: str)
        """
        if not folder_path or not folder_path.strip():
            return False, "Folder path cannot be empty"

        # Clean the folder path
        folder_path = folder_path.strip().strip('/')

        # Validate folder path (no invalid characters)
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in folder_path:
                return False, f"Folder path cannot contain '{char}'"

        try:
            # Create the full path in the password store
            full_folder_path = os.path.join(self.store_dir, folder_path)

            # Check if folder already exists
            if os.path.exists(full_folder_path):
                return False, f"Folder '{folder_path}' already exists"

            # Create the directory
            os.makedirs(full_folder_path, exist_ok=True)

            # Verify creation
            if os.path.isdir(full_folder_path):
                return True, f"Folder '{folder_path}' created successfully"
            else:
                return False, f"Failed to create folder '{folder_path}'"

        except OSError as e:
            return False, f"Error creating folder: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error creating folder: {str(e)}"

    def is_folder_empty(self, folder_path):
        """
        Check if a folder is empty (contains no .gpg files).

        Args:
            folder_path (str): The path of the folder to check

        Returns:
            tuple: (success: bool, is_empty: bool, message: str)
        """
        if not folder_path or not folder_path.strip():
            return False, False, "Folder path cannot be empty"

        # Clean the folder path
        folder_path = folder_path.strip().strip('/')

        try:
            # Create the full path in the password store
            full_folder_path = os.path.join(self.store_dir, folder_path)

            # Check if folder exists
            if not os.path.exists(full_folder_path):
                return False, False, f"Folder '{folder_path}' does not exist"

            if not os.path.isdir(full_folder_path):
                return False, False, f"'{folder_path}' is not a folder"

            # Check for .gpg files recursively
            for root, dirs, files in os.walk(full_folder_path):
                # Exclude .git directory
                if '.git' in dirs:
                    dirs.remove('.git')

                # Check if any .gpg files exist
                for file_name in files:
                    if file_name.endswith('.gpg'):
                        return True, False, f"Folder '{folder_path}' contains password files"

            # No .gpg files found
            return True, True, f"Folder '{folder_path}' is empty"

        except OSError as e:
            return False, False, f"Error checking folder: {str(e)}"
        except Exception as e:
            return False, False, f"Unexpected error checking folder: {str(e)}"

    def delete_folder(self, folder_path):
        """
        Delete an empty folder from the password store.

        Args:
            folder_path (str): The path of the folder to delete

        Returns:
            tuple: (success: bool, message: str)
        """
        if not folder_path or not folder_path.strip():
            return False, "Folder path cannot be empty"

        # Clean the folder path
        folder_path = folder_path.strip().strip('/')

        # Validate folder path
        if ".." in folder_path or folder_path.startswith("/"):
            return False, "Invalid folder path"

        try:
            # First check if folder is empty
            success, is_empty, message = self.is_folder_empty(folder_path)
            if not success:
                return False, message

            if not is_empty:
                return False, f"Cannot delete folder '{folder_path}': folder is not empty"

            # Create the full path in the password store
            full_folder_path = os.path.join(self.store_dir, folder_path)

            # Delete the directory
            os.rmdir(full_folder_path)

            # Verify deletion
            if not os.path.exists(full_folder_path):
                return True, f"Folder '{folder_path}' deleted successfully"
            else:
                return False, f"Failed to delete folder '{folder_path}'"

        except OSError as e:
            return False, f"Error deleting folder: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error deleting folder: {str(e)}"

    def rename_folder(self, old_folder_path, new_folder_path):
        """
        Rename a folder in the password store by moving all its contents.

        Args:
            old_folder_path (str): The current path of the folder to rename
            new_folder_path (str): The new path for the folder

        Returns:
            tuple: (success: bool, message: str)
        """
        if not old_folder_path or not new_folder_path:
            return False, "Old and new folder paths cannot be empty"

        # Clean the folder paths
        old_folder_path = old_folder_path.strip().strip('/')
        new_folder_path = new_folder_path.strip().strip('/')

        if old_folder_path == new_folder_path:
            return False, "Old and new folder paths cannot be the same"

        # Validate folder paths (no invalid characters)
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in new_folder_path:
                return False, f"New folder path cannot contain '{char}'"

        try:
            # Create the full paths in the password store
            old_full_path = os.path.join(self.store_dir, old_folder_path)
            new_full_path = os.path.join(self.store_dir, new_folder_path)

            # Check if old folder exists
            if not os.path.exists(old_full_path):
                return False, f"Folder '{old_folder_path}' does not exist"

            # Check if new folder already exists
            if os.path.exists(new_full_path):
                return False, f"Folder '{new_folder_path}' already exists"

            # Rename the directory
            os.rename(old_full_path, new_full_path)

            # Verify rename
            if os.path.isdir(new_full_path) and not os.path.exists(old_full_path):
                return True, f"Folder renamed from '{old_folder_path}' to '{new_folder_path}'"
            else:
                return False, f"Failed to rename folder '{old_folder_path}'"

        except OSError as e:
            return False, f"Error renaming folder: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error renaming folder: {str(e)}"

    # Metadata management methods

    def set_folder_metadata(self, folder_path: str, color: str, icon: str):
        """Set color and icon metadata for a folder."""
        self.metadata_manager.set_folder_metadata(folder_path, color, icon)

    def get_folder_metadata(self, folder_path: str):
        """Get color and icon metadata for a folder."""
        return self.metadata_manager.get_folder_metadata(folder_path)

    def set_password_metadata(self, password_path: str, color: str, icon: str):
        """Set color and icon metadata for a password."""
        self.metadata_manager.set_password_metadata(password_path, color, icon)

    def get_password_metadata(self, password_path: str):
        """Get color, icon, and favicon metadata for a password."""
        return self.metadata_manager.get_password_metadata(password_path)

    def set_password_favicon(self, password_path: str, favicon_data: str):
        """Set favicon base64 data for a password."""
        self.metadata_manager.set_password_favicon(password_path, favicon_data)

    def remove_folder_metadata(self, folder_path: str):
        """Remove metadata for a folder."""
        self.metadata_manager.remove_folder_metadata(folder_path)

    def remove_password_metadata(self, password_path: str):
        """Remove metadata for a password."""
        self.metadata_manager.remove_password_metadata(password_path)

    def rename_folder_metadata(self, old_path: str, new_path: str):
        """Update metadata when a folder is renamed."""
        self.metadata_manager.rename_folder_metadata(old_path, new_path)

    def rename_password_metadata(self, old_path: str, new_path: str):
        """Update metadata when a password is renamed/moved."""
        self.metadata_manager.rename_password_metadata(old_path, new_path)

    def is_folder_empty(self, folder_path):
        """
        Check if a folder is empty (contains no .gpg files).

        Args:
            folder_path (str): The path of the folder to check

        Returns:
            tuple: (success: bool, is_empty: bool, message: str)
        """
        if not folder_path or not folder_path.strip():
            return False, False, "Folder path cannot be empty"

        # Clean the folder path
        folder_path = folder_path.strip().strip('/')

        try:
            # Create the full path in the password store
            full_folder_path = os.path.join(self.store_dir, folder_path)

            # Check if folder exists
            if not os.path.exists(full_folder_path):
                return False, False, f"Folder '{folder_path}' does not exist"

            if not os.path.isdir(full_folder_path):
                return False, False, f"'{folder_path}' is not a folder"

            # Check for .gpg files recursively
            for root, dirs, files in os.walk(full_folder_path):
                # Exclude .git directory
                if '.git' in dirs:
                    dirs.remove('.git')

                # Check if any .gpg files exist
                for file_name in files:
                    if file_name.endswith('.gpg'):
                        return True, False, f"Folder '{folder_path}' contains password files"

            # No .gpg files found
            return True, True, f"Folder '{folder_path}' is empty"

        except OSError as e:
            return False, False, f"Error checking folder: {str(e)}"
        except Exception as e:
            return False, False, f"Unexpected error checking folder: {str(e)}"

    def delete_folder(self, folder_path):
        """
        Delete an empty folder from the password store.

        Args:
            folder_path (str): The path of the folder to delete

        Returns:
            tuple: (success: bool, message: str)
        """
        if not folder_path or not folder_path.strip():
            return False, "Folder path cannot be empty"

        # Clean the folder path
        folder_path = folder_path.strip().strip('/')

        # Validate folder path
        if ".." in folder_path or folder_path.startswith("/"):
            return False, "Invalid folder path"

        try:
            # First check if folder is empty
            success, is_empty, message = self.is_folder_empty(folder_path)
            if not success:
                return False, message

            if not is_empty:
                return False, f"Cannot delete folder '{folder_path}': folder is not empty"

            # Create the full path in the password store
            full_folder_path = os.path.join(self.store_dir, folder_path)

            # Delete the directory
            os.rmdir(full_folder_path)

            # Verify deletion
            if not os.path.exists(full_folder_path):
                return True, f"Folder '{folder_path}' deleted successfully"
            else:
                return False, f"Failed to delete folder '{folder_path}'"

        except OSError as e:
            return False, f"Error deleting folder: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error deleting folder: {str(e)}"

    def get_parsed_password_details(self, path_to_password):
        """
        Retrieves and parses the content of the specified password file.
        Extracts password (first line), username, URL, and other notes.
        Returns a dictionary with parsed fields, or an error string.
        Example return:
        {
            'password': 'actual_password',
            'username': 'user123',
            'url': 'https://example.com',
            'notes': 'Other details...',
            'full_content': 'raw_decrypted_content' # For edit dialog
        }
        Returns {'error': 'error message'} on failure to retrieve content.
        Fields in the success dictionary can be None if not found.
        """
        success, full_content = self.get_password_content(path_to_password)

        if not success:
            return {'error': full_content} # full_content is the error message here

        details = {
            'password': None,
            'username': None,
            'url': None,
            'notes': [], # Store notes as a list of lines initially
            'full_content': full_content
        }

        lines = full_content.splitlines()

        if not lines:
            # Empty file, but content retrieval was successful
            return details

        # Password is the first line
        details['password'] = lines[0]

        # Process remaining lines for username, URL, etc.
        other_lines = lines[1:]
        unclaimed_lines = [] # Lines that aren't username or URL

        # Regex for username (case-insensitive key, various separators)
        # Allows 'login:', 'user :', 'Username = value' etc.
        username_regex = re.compile(r"^(login|user(?:name)?)\s*[:=-]?\s*(.+)$", re.IGNORECASE)
        # Regex for URL field (url: prefix)
        url_field_regex = re.compile(r"^(url|website)\s*:\s*(.+)$", re.IGNORECASE)
        # Regex for direct URL (simple version, assumes it starts with http/https or www.)
        url_regex = re.compile(r"^(https?://[^\s]+|[wW]{3}\.[^\s]+)$") # More permissive: re.compile(r"^\S+://\S+$")

        for line in other_lines:
            username_match = username_regex.match(line)
            if not details['username'] and username_match: # Take first username found
                details['username'] = username_match.group(2).strip()
                continue # Line claimed as username

            # Check for URL field (url: prefix) first
            url_field_match = url_field_regex.match(line.strip())
            if not details['url'] and url_field_match: # Take first URL field found
                details['url'] = url_field_match.group(2).strip()
                continue # Line claimed as URL field

            # Check for direct URL after username, as some URLs might have 'user' in them
            # A simple check: if the line looks like a URL.
            # More robust URL detection can be complex.
            url_match = url_regex.match(line.strip()) # Strip line for URL check
            if not details['url'] and url_match: # Take first URL found
                details['url'] = url_match.group(0) # The whole match is the URL
                continue # Line claimed as URL

            unclaimed_lines.append(line)

        details['notes'] = "\n".join(unclaimed_lines).strip()
        if not details['notes']: # Ensure notes is None if empty after join/strip
            details['notes'] = None

        return details

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Test with default store
        store = PasswordStore()
        logger.info(f"Using password store: {store.store_dir}")

        passwords = store.list_passwords()
        logger.info("Available passwords:")
        if passwords:
            for p in passwords:
                logger.info(f"  - {p}")

            # Test copying the first password
            logger.info(f"Attempting to copy '{passwords[0]}'...")
            success, message = store.copy_password(passwords[0])
            logger.info(f"Copy status: {success}, Message: {message}")
        else:
            logger.info("No passwords found.")

        # Test Git commands (these will likely require a configured remote)
        # logger.info("Attempting git pull...")
        # success, message = store.git_pull()
        # logger.info(f"Pull status: {success}, Message: {message}")

        # logger.info("Attempting git push...")
        # success, message = store.git_push()
        # logger.info(f"Push status: {success}, Message: {message}")

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during testing: {e}")
