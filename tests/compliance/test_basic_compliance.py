"""Basic compliance module tests without dependencies."""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_compliance_enums_and_dataclasses():
    """Test that compliance enums and data classes work correctly."""
    from secrets.compliance.compliance_manager import (
        ComplianceFramework,
        ComplianceStatus,
        ComplianceRequirement,
        RequirementCategory,
        ComplianceViolation,
        ComplianceReport
    )
    
    # Test ComplianceFramework enum
    assert ComplianceFramework.HIPAA.value == "HIPAA"
    assert ComplianceFramework.PCI_DSS.value == "PCI_DSS" 
    assert ComplianceFramework.GDPR.value == "GDPR"
    
    # Test ComplianceStatus enum
    assert ComplianceStatus.COMPLIANT.value == "compliant"
    assert ComplianceStatus.NON_COMPLIANT.value == "non_compliant"
    assert ComplianceStatus.PARTIAL.value == "partial"
    
    # Test RequirementCategory enum
    assert RequirementCategory.TECHNICAL.value == "technical"
    assert RequirementCategory.ADMINISTRATIVE.value == "administrative"
    assert RequirementCategory.PHYSICAL.value == "physical"
    
    # Test ComplianceRequirement dataclass
    requirement = ComplianceRequirement(
        id="TEST-REQ-1",
        name="Test Requirement",
        description="A test compliance requirement",
        category=RequirementCategory.TECHNICAL,
        priority=1,
        framework=ComplianceFramework.HIPAA,
        reference="Section 164.308",
        verification_method="Automated check"
    )
    
    assert requirement.id == "TEST-REQ-1"
    assert requirement.name == "Test Requirement"
    assert requirement.category == RequirementCategory.TECHNICAL
    assert requirement.framework == ComplianceFramework.HIPAA
    assert requirement.priority == 1
    assert not requirement.implemented  # Default value
    assert requirement.automated == False  # Default value
    
    # Test ComplianceViolation dataclass
    violation = ComplianceViolation(
        id="VIOL-001",
        requirement_id="TEST-REQ-1",
        severity="high",
        description="Test violation description",
        detected_at=datetime.now()
    )
    
    assert violation.id == "VIOL-001"
    assert violation.requirement_id == "TEST-REQ-1"
    assert violation.severity == "high"
    assert not violation.resolved  # Default value
    assert violation.resolved_at is None  # Default value
    
    # Test ComplianceReport dataclass
    report = ComplianceReport(
        framework=ComplianceFramework.PCI_DSS,
        assessment_date=datetime.now(),
        status=ComplianceStatus.PARTIAL,
        score=75.5,
        total_requirements=20,
        implemented_requirements=15,
        violations=[violation],
        recommendations=["Implement missing controls"],
        next_review_date=datetime.now() + timedelta(days=90)
    )
    
    assert report.framework == ComplianceFramework.PCI_DSS
    assert report.status == ComplianceStatus.PARTIAL
    assert report.score == 75.5
    assert report.total_requirements == 20
    assert report.implemented_requirements == 15
    assert len(report.violations) == 1
    assert len(report.recommendations) == 1

def test_rbac_enums_and_dataclasses():
    """Test RBAC enums and data classes."""
    from secrets.compliance.rbac.rbac_manager import (
        AccessLevel,
        ResourceType,
        Permission,
        Role,
        UserRole
    )
    
    # Test AccessLevel enum
    assert AccessLevel.NONE.value == "none"
    assert AccessLevel.READ.value == "read"
    assert AccessLevel.WRITE.value == "write"
    assert AccessLevel.DELETE.value == "delete"
    assert AccessLevel.ADMIN.value == "admin"
    
    # Test ResourceType enum
    assert ResourceType.PASSWORD.value == "password"
    assert ResourceType.CONFIGURATION.value == "configuration"
    assert ResourceType.AUDIT_LOG.value == "audit_log"
    assert ResourceType.USER_ACCOUNT.value == "user_account"
    
    # Test Permission dataclass
    permission = Permission(
        id="test_permission",
        name="Test Permission",
        description="A test permission for reading passwords",
        resource_type=ResourceType.PASSWORD,
        access_level=AccessLevel.READ
    )
    
    assert permission.id == "test_permission"
    assert permission.name == "Test Permission"
    assert permission.resource_type == ResourceType.PASSWORD
    assert permission.access_level == AccessLevel.READ
    assert str(permission) == "password:read"
    
    # Test Role dataclass
    role = Role(
        id="test_role",
        name="Test Role",
        description="A test role for basic users"
    )
    
    assert role.id == "test_role"
    assert role.name == "Test Role"
    assert len(role.permissions) == 0  # Default empty set
    assert len(role.parent_roles) == 0  # Default empty set
    assert not role.is_system_role  # Default False
    
    # Test adding and removing permissions
    role.add_permission("test_permission")
    assert "test_permission" in role.permissions
    
    role.remove_permission("test_permission")
    assert "test_permission" not in role.permissions
    
    # Test UserRole dataclass
    assigned_date = datetime.now()
    expiry_date = assigned_date + timedelta(days=30)
    
    user_role = UserRole(
        user_id="test_user",
        role_id="test_role",
        assigned_by="admin_user",
        assigned_date=assigned_date,
        expiry_date=expiry_date
    )
    
    assert user_role.user_id == "test_user"
    assert user_role.role_id == "test_role"
    assert user_role.assigned_by == "admin_user"
    assert user_role.assigned_date == assigned_date
    assert user_role.expiry_date == expiry_date
    assert user_role.active  # Default True
    
    # Test validity checks
    assert user_role.is_valid()  # Should be valid (active and not expired)
    assert not user_role.is_expired()  # Should not be expired
    
    # Test expired role
    past_date = datetime.now() - timedelta(days=1)
    expired_user_role = UserRole(
        user_id="test_user",
        role_id="test_role", 
        assigned_by="admin_user",
        assigned_date=assigned_date,
        expiry_date=past_date
    )
    
    assert expired_user_role.is_expired()  # Should be expired
    assert not expired_user_role.is_valid()  # Should not be valid
    
    # Test inactive role
    user_role.active = False
    assert not user_role.is_valid()  # Should not be valid when inactive

def test_gdpr_enums():
    """Test GDPR-specific enums."""
    from secrets.compliance.gdpr.gdpr_compliance import (
        ProcessingLawfulBasis,
        ConsentStatus,
        DataCategory
    )
    
    # Test ProcessingLawfulBasis enum
    assert ProcessingLawfulBasis.CONSENT.value == "consent"
    assert ProcessingLawfulBasis.CONTRACT.value == "contract"
    assert ProcessingLawfulBasis.LEGAL_OBLIGATION.value == "legal_obligation"
    assert ProcessingLawfulBasis.VITAL_INTERESTS.value == "vital_interests"
    assert ProcessingLawfulBasis.PUBLIC_TASK.value == "public_task"
    assert ProcessingLawfulBasis.LEGITIMATE_INTERESTS.value == "legitimate_interests"
    
    # Test ConsentStatus enum
    assert ConsentStatus.GIVEN.value == "given"
    assert ConsentStatus.WITHDRAWN.value == "withdrawn"
    assert ConsentStatus.NOT_GIVEN.value == "not_given"
    assert ConsentStatus.EXPIRED.value == "expired"
    
    # Test DataCategory enum
    assert DataCategory.BASIC_IDENTITY.value == "basic_identity"
    assert DataCategory.AUTHENTICATION.value == "authentication"
    assert DataCategory.USAGE_DATA.value == "usage_data"
    assert DataCategory.TECHNICAL_DATA.value == "technical_data"
    assert DataCategory.SPECIAL_CATEGORY.value == "special_category"

def test_imports():
    """Test that all compliance modules can be imported."""
    # Test main compliance module
    import secrets.compliance
    
    # Test individual compliance managers
    from secrets.compliance import (
        ComplianceManager,
        ComplianceFramework,
        ComplianceStatus,
        HIPAAComplianceManager,
        PCIDSSComplianceManager,
        GDPRComplianceManager,
        RBACManager,
        Role,
        Permission,
        AccessLevel
    )
    
    # Verify classes are available
    assert ComplianceManager is not None
    assert HIPAAComplianceManager is not None
    assert PCIDSSComplianceManager is not None
    assert GDPRComplianceManager is not None
    assert RBACManager is not None
    
    # Verify enums are available
    assert ComplianceFramework.HIPAA is not None
    assert ComplianceStatus.COMPLIANT is not None
    assert AccessLevel.READ is not None
    
    # Verify data classes are available
    assert Role is not None
    assert Permission is not None

if __name__ == "__main__":
    # Run basic tests
    test_compliance_enums_and_dataclasses()
    test_rbac_enums_and_dataclasses()
    test_gdpr_enums()
    test_imports()
    print("All basic compliance tests passed!")