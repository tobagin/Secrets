import os
import subprocess
import glob # For listing files
import re # Added

class PasswordStore:
    def __init__(self, store_dir=None):
        self.store_dir = self._determine_store_dir(store_dir)
        if not os.path.isdir(self.store_dir):
            # Consider raising a custom exception
            raise FileNotFoundError(f"Password store directory not found: {self.store_dir}")

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

    def list_passwords(self):
        """
        Recursively scans the password store directory and returns a list of password entries.
        Each entry could be a dictionary or a custom object representing a password or folder.
        For now, it will return a flat list of paths relative to the store root.
        Ignores the .git directory and other non-password files.
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
            # Use `pass show -c <path>`
            # The `-c` flag copies to clipboard.
            # `pass show <path>` would print to stdout.
            command = ["pass", "show", "-c", path_to_password]

            # Set environment variable if PASSWORD_STORE_DIR was different from default
            env = os.environ.copy()
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
            env = os.environ.copy()
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

            env = os.environ.copy()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # `pass rm` might not output much on success
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
        """
        if not path_to_password:
            return False, "Password path cannot be empty."

        if ".." in path_to_password or path_to_password.startswith("/"):
             return False, "Invalid password path."

        try:
            # Use `pass show <path>` (without -c, so it prints to stdout)
            command = ["pass", "show", path_to_password]

            env = os.environ.copy()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # The first line is the password, subsequent lines are extra data.
                # `pass show` outputs the full content of the decrypted file.
                return True, process.stdout
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error showing password '{path_to_password}': {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred while showing password: {e}"

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
            command = ["pass", "insert"]
            if multiline:
                command.append("-m") # or --multiline
            if force:
                command.append("-f") # or --force
            command.append(path_to_password)

            env = os.environ.copy()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            # The content needs to be passed via stdin to the `pass insert` command
            process = subprocess.run(command, input=content, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                # `pass insert` might not output much on success
                return True, f"Successfully saved '{path_to_password}'."
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error saving password '{path_to_password}': {error_message}"
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
            # Use `pass grep <query>`
            # Note: `pass grep` can be slow on very large stores.
            # It searches the content of encrypted files.
            command = ["pass", "grep", query] # Add any other flags if needed, e.g. -i for case-insensitive

            env = os.environ.copy()
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

    def move_password(self, old_path, new_path):
        """
        Moves/renames a password entry using `pass mv`.
        Returns True on success, False otherwise, along with an output/error message.
        """
        if not old_path or not new_path:
            return False, "Old and new paths cannot be empty."

        # Basic validation for paths
        if ".." in old_path or old_path.startswith("/") or            ".." in new_path or new_path.startswith("/"):
             return False, "Invalid old or new path."

        if old_path == new_path:
            return False, "Old and new paths cannot be the same."

        try:
            command = ["pass", "mv", old_path, new_path]

            env = os.environ.copy()
            if self.store_dir != os.path.expanduser("~/.password-store"):
                 env["PASSWORD_STORE_DIR"] = self.store_dir

            process = subprocess.run(command, capture_output=True, text=True, check=False, env=env)

            if process.returncode == 0:
                return True, f"Successfully moved '{old_path}' to '{new_path}'."
            else:
                error_message = process.stderr.strip() if process.stderr.strip() else process.stdout.strip()
                return False, f"Error moving password: {error_message}"
        except FileNotFoundError:
            return False, "The 'pass' command was not found. Is it installed and in your PATH?"
        except Exception as e:
            return False, f"An unexpected error occurred while moving: {e}"

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
        # Regex for URL (simple version, assumes it starts with http/https or www.)
        url_regex = re.compile(r"^(https?://[^\s]+|[wW]{3}\.[^\s]+)$") # More permissive: re.compile(r"^\S+://\S+$")

        for line in other_lines:
            username_match = username_regex.match(line)
            if not details['username'] and username_match: # Take first username found
                details['username'] = username_match.group(2).strip()
                continue # Line claimed as username

            # Check for URL after username, as some URLs might have 'user' in them
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
    try:
        # Test with default store
        store = PasswordStore()
        print(f"Using password store: {store.store_dir}")

        passwords = store.list_passwords()
        print("\nAvailable passwords:")
        if passwords:
            for p in passwords:
                print(f"  - {p}")

            # Test copying the first password
            print(f"\nAttempting to copy '{passwords[0]}'...")
            success, message = store.copy_password(passwords[0])
            print(f"Copy status: {success}, Message: {message}")
        else:
            print("No passwords found.")

        # Test Git commands (these will likely require a configured remote)
        # print("\nAttempting git pull...")
        # success, message = store.git_pull()
        # print(f"Pull status: {success}, Message: {message}")

        # print("\nAttempting git push...")
        # success, message = store.git_push()
        # print(f"Push status: {success}, Message: {message}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")
