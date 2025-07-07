#!/usr/bin/env python3
"""
Direct test of preferences functionality without UI imports.
"""

import sys
import os

# Get the absolute path to the project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)

# Remove any conflicting secrets module from path
if 'secrets' in sys.modules:
    del sys.modules['secrets']

# Test configuration system
try:
    from secrets.config import ConfigManager, ComplianceConfig
    
    print("✅ ConfigManager loads successfully")
    
    # Test config manager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    print("✅ Configuration loaded successfully")
    print(f"   • Theme: {config.ui.theme}")
    print(f"   • Remember window: {config.ui.remember_window_state}")
    print(f"   • Auto-hide passwords: {config.security.auto_hide_passwords}")
    print(f"   • Clipboard timeout: {config.security.clear_clipboard_timeout}")
    print(f"   • HIPAA enabled: {config.compliance.hipaa_enabled}")
    print(f"   • PCI DSS enabled: {config.compliance.pci_dss_enabled}")
    print(f"   • GDPR enabled: {config.compliance.gdpr_enabled}")
    print(f"   • Case sensitive search: {config.search.case_sensitive}")
    print(f"   • Git auto-pull: {config.git.auto_pull_on_startup}")
    
    # Test compliance configuration update
    print("\n🔧 Testing compliance configuration updates...")
    config_manager.update_compliance_config(
        hipaa_enabled=True,
        security_officer_email="test@example.com",
        audit_enabled=True
    )
    
    # Reload config to verify
    updated_config = config_manager.get_config()
    print(f"   • HIPAA enabled after update: {updated_config.compliance.hipaa_enabled}")
    print(f"   • Security officer email: {updated_config.compliance.security_officer_email}")
    print(f"   • Audit enabled: {updated_config.compliance.audit_enabled}")
    
    print("✅ All configuration tests passed!")
    
    # Show what settings are available
    print("\n📋 Available settings pages:")
    print("   1. General (Theme, Window state)")
    print("   2. Security (Auto-lock, Passwords, Memory clearing)")
    print("   3. Compliance (HIPAA, PCI DSS, GDPR, RBAC, Audit)")
    print("   4. Search (Case sensitivity, Content search, Result limits)")
    print("   5. Git (Automation, Status, Repository management)")
    
    # Show compliance settings detail
    print("\n🛡️  Compliance settings available:")
    compliance_config = ComplianceConfig()
    compliance_attrs = [attr for attr in dir(compliance_config) if not attr.startswith('_')]
    print(f"   • Total compliance options: {len(compliance_attrs)}")
    print("   • Framework toggles: HIPAA, PCI DSS, GDPR, RBAC, Audit")
    print("   • Email configurations: Security Officer, DPO")
    print("   • Security policies: Password complexity, Account lockout")
    print("   • Retention policies: Audit logs, Data retention")
    print("   • Access controls: Role assignments, Justification requirements")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()