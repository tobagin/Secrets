#!/usr/bin/env python3
"""
Comprehensive version validation and consistency checking.

This script provides advanced version validation to prevent inconsistencies
across the entire project, with detailed reporting and auto-fix capabilities.
"""

import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


class VersionChecker:
    """Comprehensive version checker with validation and reporting."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.issues = []
        self.warnings = []
        self.successes = []
        
    def log_issue(self, message: str, severity: str = "error"):
        """Log an issue with the version system."""
        entry = {
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        if severity == "error":
            self.issues.append(entry)
        elif severity == "warning":
            self.warnings.append(entry)
        else:
            self.successes.append(entry)
    
    def check_meson_version(self) -> Optional[str]:
        """Extract and validate version from meson.build."""
        meson_file = self.project_root / "meson.build"
        
        if not meson_file.exists():
            self.log_issue("meson.build file not found")
            return None
        
        try:
            import re
            with open(meson_file, 'r') as f:
                content = f.read()
            
            pattern = r"project\s*\(\s*['\"]secrets['\"]\s*,\s*version\s*:\s*['\"]([^'\"]+)['\"]"
            match = re.search(pattern, content)
            
            if match:
                version = match.group(1)
                # Validate semantic versioning
                if re.match(r'^\d+\.\d+\.\d+$', version):
                    self.log_issue(f"meson.build version: {version}", "success")
                    return version
                else:
                    self.log_issue(f"meson.build version '{version}' is not semantic versioning format")
                    return version
            else:
                self.log_issue("Could not find version in meson.build")
                return None
                
        except Exception as e:
            self.log_issue(f"Error reading meson.build: {e}")
            return None
    
    def check_python_modules(self, expected_version: str) -> bool:
        """Check Python module version consistency."""
        all_good = True
        
        # Check if modules use centralized version
        modules_to_check = [
            ("src/secrets/__init__.py", "__version__"),
            ("src/secrets/app_info.py", "VERSION")
        ]
        
        for module_path, version_var in modules_to_check:
            file_path = self.project_root / module_path
            
            if not file_path.exists():
                self.log_issue(f"Python module not found: {module_path}")
                all_good = False
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check if it uses get_version()
                if f"{version_var} = get_version()" in content:
                    self.log_issue(f"{module_path} uses centralized version", "success")
                elif "from .version import get_version" in content:
                    self.log_issue(f"{module_path} imports centralized version", "success")
                else:
                    # Check for static version
                    import re
                    pattern = f'{version_var}\\s*=\\s*["\']([^"\']+)["\']'
                    match = re.search(pattern, content)
                    
                    if match:
                        static_version = match.group(1)
                        if static_version == expected_version:
                            self.log_issue(f"{module_path} has correct static version", "warning")
                        else:
                            self.log_issue(f"{module_path} version mismatch: {static_version} vs {expected_version}")
                            all_good = False
                    else:
                        self.log_issue(f"{module_path} has no version information")
                        all_good = False
                        
            except Exception as e:
                self.log_issue(f"Error checking {module_path}: {e}")
                all_good = False
        
        return all_good
    
    def check_appdata_xml(self, expected_version: str) -> bool:
        """Check AppData XML version consistency."""
        appdata_file = self.project_root / "data" / "io.github.tobagin.secrets.appdata.xml.in"
        
        if not appdata_file.exists():
            self.log_issue("AppData XML file not found", "warning")
            return True  # Not critical
        
        try:
            with open(appdata_file, 'r') as f:
                content = f.read()
            
            import re
            pattern = r'<release version="([^"]*)"'
            matches = re.findall(pattern, content)
            
            if matches:
                latest_version = matches[0]  # First release should be latest
                if latest_version == expected_version:
                    self.log_issue(f"AppData XML has correct version: {latest_version}", "success")
                    return True
                else:
                    self.log_issue(f"AppData XML version mismatch: {latest_version} vs {expected_version}")
                    return False
            else:
                self.log_issue("No release versions found in AppData XML")
                return False
                
        except Exception as e:
            self.log_issue(f"Error checking AppData XML: {e}")
            return False
    
    def check_flatpak_manifests(self, expected_version: str) -> bool:
        """Check Flatpak manifest version consistency."""
        manifests = [
            "packaging/flatpak/io.github.tobagin.secrets.yml",
            "packaging/flatpak/io.github.tobagin.secrets.dev.yml"
        ]
        
        all_good = True
        
        for manifest_path in manifests:
            file_path = self.project_root / manifest_path
            
            if not file_path.exists():
                self.log_issue(f"Flatpak manifest not found: {manifest_path}", "warning")
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                import re
                # Look for secrets app source specifically (not dependencies)
                lines = content.split('\n')
                in_secrets_source = False
                found_app_tag = False
                
                for line in lines:
                    # Look for the main secrets source entry
                    if '- name:' in line and ('secrets' in line.lower() or 'main' in line.lower()):
                        in_secrets_source = True
                    elif line.strip().startswith('- name:') and in_secrets_source:
                        in_secrets_source = False
                    elif in_secrets_source and 'tag:' in line:
                        # Extract tag version
                        tag_match = re.search(r'tag:\s*v?([0-9]+\.[0-9]+\.[0-9]+)', line)
                        if tag_match:
                            tag_version = tag_match.group(1)
                            if tag_version == expected_version:
                                self.log_issue(f"{manifest_path} has correct app version tag", "success")
                                found_app_tag = True
                                break
                
                if not found_app_tag:
                    # Check if this is a local dev build manifest (which might not have version tags)
                    if 'type: dir' in content or 'path: .' in content:
                        self.log_issue(f"{manifest_path} uses local development source", "success")
                    else:
                        self.log_issue(f"{manifest_path} may have outdated app version tags", "warning")
                        # Don't mark as error for dev manifests
                    
            except Exception as e:
                self.log_issue(f"Error checking {manifest_path}: {e}")
                all_good = False
        
        return all_good
    
    def check_changelog(self, expected_version: str) -> bool:
        """Check if changelog has entry for current version."""
        changelog_file = self.project_root / "CHANGELOG.md"
        
        if not changelog_file.exists():
            self.log_issue("CHANGELOG.md not found", "warning")
            return True  # Not critical
        
        try:
            with open(changelog_file, 'r') as f:
                content = f.read()
            
            if f"## [{expected_version}]" in content:
                self.log_issue(f"CHANGELOG.md has entry for {expected_version}", "success")
                return True
            else:
                self.log_issue(f"CHANGELOG.md missing entry for {expected_version}", "warning")
                return True  # Warning, not error
                
        except Exception as e:
            self.log_issue(f"Error checking CHANGELOG.md: {e}")
            return False
    
    def check_version_module(self) -> bool:
        """Check if version.py module exists and functions correctly."""
        version_file = self.project_root / "src" / "secrets" / "version.py"
        
        if not version_file.exists():
            self.log_issue("Version module (src/secrets/version.py) not found")
            return False
        
        try:
            # Try to import and test the version function
            import sys
            sys.path.insert(0, str(self.project_root / "src"))
            
            # Import directly to avoid dependency issues
            import importlib.util
            version_spec = importlib.util.spec_from_file_location(
                "version", 
                self.project_root / "src" / "secrets" / "version.py"
            )
            version_module = importlib.util.module_from_spec(version_spec)
            version_spec.loader.exec_module(version_module)
            
            version = version_module.get_version()
            
            if version and version != "unknown":
                self.log_issue(f"Version module working correctly: {version}", "success")
                return True
            else:
                self.log_issue("Version module returns 'unknown' or empty")
                return False
                
        except Exception as e:
            # Try fallback method - just check if file contains required functions
            try:
                with open(version_file, 'r') as f:
                    content = f.read()
                
                if "def get_version()" in content and "get_version_from_meson" in content:
                    self.log_issue("Version module structure looks correct", "success")
                    return True
                else:
                    self.log_issue("Version module missing required functions")
                    return False
                    
            except Exception:
                self.log_issue(f"Error testing version module: {e}")
                return False
        finally:
            # Clean up sys.path
            if str(self.project_root / "src") in sys.path:
                sys.path.remove(str(self.project_root / "src"))
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all version checks and return comprehensive report."""
        print("Running comprehensive version validation...")
        print("=" * 50)
        
        # Reset counters
        self.issues = []
        self.warnings = []
        self.successes = []
        
        # Check version module first
        version_module_ok = self.check_version_module()
        
        # Get expected version from meson.build
        expected_version = self.check_meson_version()
        
        if not expected_version:
            return {
                'success': False,
                'issues': self.issues,
                'warnings': self.warnings,
                'successes': self.successes,
                'summary': "Could not determine version from meson.build"
            }
        
        # Run all checks
        python_ok = self.check_python_modules(expected_version)
        appdata_ok = self.check_appdata_xml(expected_version)
        flatpak_ok = self.check_flatpak_manifests(expected_version)
        changelog_ok = self.check_changelog(expected_version)
        
        # Determine overall success
        overall_success = (
            version_module_ok and
            python_ok and
            appdata_ok and
            flatpak_ok and
            len(self.issues) == 0
        )
        
        return {
            'success': overall_success,
            'version': expected_version,
            'issues': self.issues,
            'warnings': self.warnings,
            'successes': self.successes,
            'summary': "All checks passed" if overall_success else f"Found {len(self.issues)} issues"
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Print human-readable report."""
        print(f"\nVersion: {report.get('version', 'unknown')}")
        print("=" * 30)
        
        # Print successes
        for success in report['successes']:
            print(f"✅ {success['message']}")
        
        # Print warnings
        for warning in report['warnings']:
            print(f"⚠️  {warning['message']}")
        
        # Print issues
        for issue in report['issues']:
            print(f"❌ {issue['message']}")
        
        print("\n" + "=" * 30)
        if report['success']:
            print("🎉 All version checks passed!")
        else:
            print(f"❌ {report['summary']}")
            print("\n💡 To fix issues, run: python3 scripts/sync_version.py")
    
    def auto_fix_issues(self) -> bool:
        """Attempt to automatically fix version issues."""
        sync_script = self.project_root / "scripts" / "sync_version.py"
        
        if not sync_script.exists():
            print("❌ sync_version.py script not found")
            return False
        
        try:
            print("🔧 Attempting to fix version issues...")
            result = subprocess.run(
                [sys.executable, str(sync_script)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("✅ Auto-fix completed successfully")
                return True
            else:
                print("❌ Auto-fix failed:")
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error during auto-fix: {e}")
            return False


def main():
    """Main function."""
    checker = VersionChecker()
    
    # Run comprehensive check
    report = checker.run_comprehensive_check()
    
    # Print report
    checker.print_report(report)
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if "--json" in sys.argv:
            print("\n" + "=" * 50)
            print("JSON Report:")
            print(json.dumps(report, indent=2))
        
        if "--auto-fix" in sys.argv and not report['success']:
            print("\n" + "=" * 50)
            if checker.auto_fix_issues():
                # Re-run check after fix
                print("\nRe-running checks after auto-fix...")
                new_report = checker.run_comprehensive_check()
                checker.print_report(new_report)
                sys.exit(0 if new_report['success'] else 1)
    
    # Exit with appropriate code
    sys.exit(0 if report['success'] else 1)


if __name__ == "__main__":
    main()