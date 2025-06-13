import os
import subprocess
import glob # For listing files

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
