#!/usr/bin/env python3
"""
Version synchronization monitoring and validation tool.

This script provides comprehensive monitoring of version synchronization
across all project files, ensuring consistency and detecting drift.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess


def run_sync_script() -> bool:
    """Run the sync_version.py script and return success status."""
    try:
        result = subprocess.run(
            [sys.executable, "scripts/sync_version.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        return result.returncode == 0
    except Exception:
        return False


def run_validation_script() -> Dict[str, Any]:
    """Run the validate_version.py script and return results."""
    try:
        result = subprocess.run(
            [sys.executable, "scripts/validate_version.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Parse output to determine consistency
        output = result.stdout
        is_consistent = "🎉 All version references are consistent!" in output
        
        return {
            'success': result.returncode == 0,
            'consistent': is_consistent,
            'output': output,
            'errors': result.stderr if result.stderr else None
        }
    except Exception as e:
        return {
            'success': False,
            'consistent': False,
            'output': '',
            'errors': str(e)
        }


def check_meson_integration() -> bool:
    """Check if version sync is properly integrated in meson.build."""
    meson_file = Path("meson.build")
    if not meson_file.exists():
        return False
    
    with open(meson_file, 'r') as f:
        content = f.read()
    
    # Check for sync_version integration
    return 'sync_version' in content and 'run_command(sync_version' in content


def create_sync_report() -> Dict[str, Any]:
    """Create a comprehensive synchronization report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'version_sync': {
            'meson_integration': check_meson_integration(),
            'sync_script_success': run_sync_script(),
        },
        'validation': run_validation_script(),
        'recommendations': []
    }
    
    # Add recommendations based on findings
    if not report['version_sync']['meson_integration']:
        report['recommendations'].append(
            "Integrate version synchronization into meson.build for automatic builds"
        )
    
    if not report['version_sync']['sync_script_success']:
        report['recommendations'].append(
            "Fix issues in sync_version.py script"
        )
    
    if not report['validation']['consistent']:
        report['recommendations'].append(
            "Run version synchronization to fix consistency issues"
        )
    
    return report


def print_sync_status():
    """Print a human-readable synchronization status."""
    print("Version Synchronization Status")
    print("=" * 50)
    
    report = create_sync_report()
    
    # Meson integration status
    meson_status = "✓" if report['version_sync']['meson_integration'] else "✗"
    print(f"{meson_status} Meson build integration")
    
    # Sync script status
    sync_status = "✓" if report['version_sync']['sync_script_success'] else "✗"
    print(f"{sync_status} Version synchronization script")
    
    # Validation status
    validation_status = "✓" if report['validation']['consistent'] else "✗"
    print(f"{validation_status} Version consistency validation")
    
    print()
    
    # Overall status
    all_good = (
        report['version_sync']['meson_integration'] and
        report['version_sync']['sync_script_success'] and
        report['validation']['consistent']
    )
    
    if all_good:
        print("🎉 Version synchronization system is fully operational!")
    else:
        print("⚠ Version synchronization needs attention")
        
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
    
    print(f"\nReport generated: {report['timestamp']}")


def save_sync_report(output_file: Optional[str] = None):
    """Save detailed synchronization report to JSON file."""
    report = create_sync_report()
    
    if output_file is None:
        output_file = f"version_sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Detailed report saved to: {output_file}")


def main():
    """Main monitoring function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        save_sync_report()
    else:
        print_sync_status()


if __name__ == "__main__":
    main()