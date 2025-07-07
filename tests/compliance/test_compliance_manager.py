"""Unit tests for compliance manager functionality."""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# We'll mock the security imports since they have dependencies
@pytest.fixture
def mock_audit_logger():
    """Mock audit logger for testing."""
    mock = Mock()
    mock.audit_compliance_event = Mock()
    return mock

@pytest.fixture
def mock_config_manager():
    """Mock encrypted config manager for testing."""
    mock = Mock()
    mock.get_config = Mock(return_value={})
    mock.set_config = Mock()
    return mock

def test_compliance_manager_creation():
    """Test that we can create the base compliance manager classes."""
    # This will test the basic structure without dependencies
    from secrets.compliance.compliance_manager import (
        ComplianceFramework,
        ComplianceStatus,
        ComplianceRequirement,
        RequirementCategory,
        ComplianceViolation,
        ComplianceReport
    )
    
    # Test enums
    assert ComplianceFramework.HIPAA.value == "HIPAA"
    assert ComplianceFramework.PCI_DSS.value == "PCI_DSS"
    assert ComplianceFramework.GDPR.value == "GDPR"
    
    assert ComplianceStatus.COMPLIANT.value == "compliant"
    assert ComplianceStatus.NON_COMPLIANT.value == "non_compliant"
    
    # Test data classes
    requirement = ComplianceRequirement(
        id="TEST-1",
        name="Test Requirement",
        description="A test requirement",
        category=RequirementCategory.TECHNICAL,
        priority=1,
        framework=ComplianceFramework.HIPAA,
        reference="Test Reference",
        verification_method="Manual check"
    )
    
    assert requirement.id == "TEST-1"
    assert requirement.framework == ComplianceFramework.HIPAA
    assert requirement.category == RequirementCategory.TECHNICAL
    
    violation = ComplianceViolation(
        id="VIOL-1",
        requirement_id="TEST-1",
        severity="high",
        description="Test violation",
        detected_at=datetime.now()
    )
    
    assert violation.requirement_id == "TEST-1"
    assert violation.severity == "high"
    assert not violation.resolved

def test_rbac_components():
    """Test RBAC data structures."""
    from secrets.compliance.rbac.rbac_manager import (
        Permission,
        Role,
        UserRole,
        AccessLevel,
        ResourceType
    )
    
    # Test Permission
    permission = Permission(
        id="test_perm",
        name="Test Permission",
        description="A test permission",
        resource_type=ResourceType.PASSWORD,
        access_level=AccessLevel.READ
    )
    
    assert permission.id == "test_perm"
    assert permission.resource_type == ResourceType.PASSWORD
    assert permission.access_level == AccessLevel.READ
    assert str(permission) == "password:read"
    
    # Test Role
    role = Role(
        id="test_role",
        name="Test Role",
        description="A test role",
        permissions={"test_perm"}
    )
    
    assert role.id == "test_role"
    assert "test_perm" in role.permissions
    
    role.add_permission("test_perm_2")
    assert "test_perm_2" in role.permissions
    
    role.remove_permission("test_perm")
    assert "test_perm" not in role.permissions
    
    # Test UserRole
    user_role = UserRole(
        user_id="user1",
        role_id="test_role",
        assigned_by="admin",
        assigned_date=datetime.now(),
        expiry_date=datetime.now() + timedelta(days=30)
    )
    
    assert user_role.user_id == "user1"
    assert user_role.is_valid()
    assert not user_role.is_expired()
    
    # Test expired role
    expired_role = UserRole(
        user_id="user1",
        role_id="test_role",
        assigned_by="admin",
        assigned_date=datetime.now() - timedelta(days=31),
        expiry_date=datetime.now() - timedelta(days=1)
    )
    
    assert expired_role.is_expired()
    assert not expired_role.is_valid()

@patch('secrets.compliance.compliance_manager.AuditLogger')
@patch('secrets.compliance.compliance_manager.EncryptedConfigManager')
def test_hipaa_compliance_manager(mock_config, mock_audit):
    """Test HIPAA compliance manager."""
    from secrets.compliance.hipaa.hipaa_compliance import HIPAAComplianceManager
    
    # Mock the dependencies
    mock_config_instance = Mock()
    mock_config_instance.get_config.return_value = {}
    mock_config_instance.set_config = Mock()
    mock_config.return_value = mock_config_instance
    
    mock_audit_instance = Mock()
    mock_audit.return_value = mock_audit_instance
    
    # Create HIPAA manager
    hipaa_manager = HIPAAComplianceManager(mock_config_instance, mock_audit_instance)
    
    # Test that requirements were initialized
    requirements = hipaa_manager.get_all_requirements()
    assert len(requirements) > 0
    
    # Test specific HIPAA requirements exist
    requirement_ids = {req.id for req in requirements}
    expected_requirements = [
        "HIPAA-AS-1",  # Security Officer
        "HIPAA-AS-2",  # Workforce Training
        "HIPAA-TS-1",  # Unique User Identification
        "HIPAA-TS-3",  # Audit Controls
    ]
    
    for req_id in expected_requirements:
        assert req_id in requirement_ids, f"Missing requirement: {req_id}"
    
    # Test requirement retrieval
    security_officer_req = hipaa_manager.get_requirement("HIPAA-AS-1")
    assert security_officer_req is not None
    assert security_officer_req.name == "Security Officer Designation"
    assert security_officer_req.priority == 1

@patch('secrets.compliance.compliance_manager.AuditLogger')
@patch('secrets.compliance.compliance_manager.EncryptedConfigManager')
def test_pci_dss_compliance_manager(mock_config, mock_audit):
    """Test PCI DSS compliance manager."""
    from secrets.compliance.pci_dss.pci_dss_compliance import PCIDSSComplianceManager
    
    # Mock the dependencies
    mock_config_instance = Mock()
    mock_config_instance.get_config.return_value = {}
    mock_config_instance.set_config = Mock()
    mock_config.return_value = mock_config_instance
    
    mock_audit_instance = Mock()
    mock_audit.return_value = mock_audit_instance
    
    # Create PCI DSS manager
    pci_manager = PCIDSSComplianceManager(mock_config_instance, mock_audit_instance)
    
    # Test that requirements were initialized
    requirements = pci_manager.get_all_requirements()
    assert len(requirements) > 0
    
    # Test specific PCI DSS requirements exist
    requirement_ids = {req.id for req in requirements}
    expected_requirements = [
        "PCI-8.3",  # Password Requirements
        "PCI-8.4",  # Account Lockout
        "PCI-10.1", # Audit Trail Implementation
        "PCI-3.5",  # Cryptographic Key Management
    ]
    
    for req_id in expected_requirements:
        assert req_id in requirement_ids, f"Missing requirement: {req_id}"
    
    # Test password complexity checking
    weak_password = "123"
    strong_password = "MyStr0ng!P@ssw0rd123"
    
    weak_result, weak_issues = pci_manager.check_password_complexity(weak_password)
    strong_result, strong_issues = pci_manager.check_password_complexity(strong_password)
    
    assert not weak_result
    assert len(weak_issues) > 0
    assert strong_result
    assert len(strong_issues) == 0

@patch('secrets.compliance.compliance_manager.AuditLogger')
@patch('secrets.compliance.compliance_manager.EncryptedConfigManager')
def test_gdpr_compliance_manager(mock_config, mock_audit):
    """Test GDPR compliance manager."""
    from secrets.compliance.gdpr.gdpr_compliance import (
        GDPRComplianceManager,
        ProcessingLawfulBasis,
        ConsentStatus
    )
    
    # Mock the dependencies
    mock_config_instance = Mock()
    mock_config_instance.get_config.return_value = {}
    mock_config_instance.set_config = Mock()
    mock_config.return_value = mock_config_instance
    
    mock_audit_instance = Mock()
    mock_audit_instance.audit_compliance_event = Mock()
    mock_audit.return_value = mock_audit_instance
    
    # Create GDPR manager
    gdpr_manager = GDPRComplianceManager(mock_config_instance, mock_audit_instance)
    
    # Test that requirements were initialized
    requirements = gdpr_manager.get_all_requirements()
    assert len(requirements) > 0
    
    # Test specific GDPR requirements exist
    requirement_ids = {req.id for req in requirements}
    expected_requirements = [
        "GDPR-P-1",  # Lawfulness, Fairness, and Transparency
        "GDPR-R-1",  # Right of Access
        "GDPR-R-3",  # Right to Erasure
        "GDPR-C-1",  # Valid Consent
    ]
    
    for req_id in expected_requirements:
        assert req_id in requirement_ids, f"Missing requirement: {req_id}"
    
    # Test consent management
    gdpr_manager.record_consent(
        data_subject_id="user123",
        purpose="password_management",
        lawful_basis=ProcessingLawfulBasis.CONSENT,
        consent_given=True
    )
    
    # Verify audit was called
    mock_audit_instance.audit_compliance_event.assert_called()
    
    # Test consent withdrawal
    success = gdpr_manager.withdraw_consent("user123", "password_management")
    assert success
    
    # Test data request handling
    request_id = gdpr_manager.handle_data_request(
        request_type="access",
        data_subject_id="user123",
        request_details={"requested_data": "all"}
    )
    
    assert request_id is not None
    assert request_id.startswith("access_user123_")

@patch('secrets.compliance.compliance_manager.AuditLogger')
@patch('secrets.compliance.compliance_manager.EncryptedConfigManager')
def test_rbac_manager(mock_config, mock_audit):
    """Test RBAC manager functionality."""
    from secrets.compliance.rbac.rbac_manager import (
        RBACManager,
        ResourceType,
        AccessLevel
    )
    
    # Mock the dependencies
    mock_config_instance = Mock()
    mock_config_instance.get_config.return_value = {"enabled": True}
    mock_config_instance.set_config = Mock()
    mock_config.return_value = mock_config_instance
    
    mock_audit_instance = Mock()
    mock_audit_instance.audit_compliance_event = Mock()
    mock_audit.return_value = mock_audit_instance
    
    # Create RBAC manager
    rbac_manager = RBACManager(mock_config_instance, mock_audit_instance)
    
    # Test that default permissions and roles were created
    permissions = rbac_manager._permissions
    roles = rbac_manager._roles
    
    assert len(permissions) > 0
    assert len(roles) > 0
    
    # Test specific permissions exist
    assert "password_read" in permissions
    assert "password_write" in permissions
    assert "password_admin" in permissions
    
    # Test specific roles exist
    assert "user" in roles
    assert "admin" in roles
    assert "security_officer" in roles
    
    # Test role assignment
    user_role = rbac_manager.assign_role_to_user(
        user_id="testuser",
        role_id="user",
        assigned_by="admin",
        justification="Standard user access"
    )
    
    assert user_role.user_id == "testuser"
    assert user_role.role_id == "user"
    assert user_role.is_valid()
    
    # Test permission checking
    user_permissions = rbac_manager.get_user_permissions("testuser")
    assert "password_read" in user_permissions
    assert "password_write" in user_permissions
    
    # Test access control
    access_granted, reason = rbac_manager.check_access(
        user_id="testuser",
        resource_type=ResourceType.PASSWORD,
        resource_id="test_password",
        access_level=AccessLevel.READ
    )
    
    assert access_granted
    assert reason is None
    
    # Test access denial
    access_denied, reason = rbac_manager.check_access(
        user_id="testuser",
        resource_type=ResourceType.SYSTEM,
        resource_id="test_system",
        access_level=AccessLevel.ADMIN
    )
    
    assert not access_denied
    assert "Missing permission" in reason
    
    # Test role revocation
    success = rbac_manager.revoke_role_from_user(
        user_id="testuser",
        role_id="user",
        revoked_by="admin",
        reason="Test revocation"
    )
    
    assert success
    
    # Verify user no longer has permissions
    user_permissions_after = rbac_manager.get_user_permissions("testuser")
    assert len(user_permissions_after) == 0

def test_compliance_export_import():
    """Test compliance configuration export/import."""
    from secrets.compliance.rbac.rbac_manager import RBACManager
    
    # Mock dependencies
    mock_config = Mock()
    mock_config.get_config.return_value = {"enabled": True}
    mock_config.set_config = Mock()
    
    mock_audit = Mock()
    mock_audit.audit_compliance_event = Mock()
    
    rbac_manager = RBACManager(mock_config, mock_audit)
    
    # Export configuration
    config_export = rbac_manager.export_rbac_configuration()
    
    assert "permissions" in config_export
    assert "roles" in config_export
    assert "user_roles" in config_export
    assert "configuration" in config_export
    assert "export_date" in config_export
    
    # Verify export contains expected data
    assert len(config_export["permissions"]) > 0
    assert len(config_export["roles"]) > 0
    
    # Test that export can be serialized to JSON
    json_export = json.dumps(config_export, indent=2)
    assert len(json_export) > 0
    
    # Test that export can be parsed back
    parsed_config = json.loads(json_export)
    assert parsed_config["permissions"] == config_export["permissions"]