"""
HIPAA compliance implementation for Secrets Password Manager.

This module implements the Health Insurance Portability and Accountability Act (HIPAA)
compliance requirements including Security Rule provisions for administrative,
technical, and physical safeguards.
"""

import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...security import AuditLogger, EncryptedConfigManager
from ..compliance_manager import (
    ComplianceFramework,
    ComplianceManager,
    ComplianceRequirement,
    RequirementCategory,
)


class HIPAAComplianceManager(ComplianceManager):
    """
    HIPAA compliance manager implementation.
    
    Implements HIPAA Security Rule requirements for:
    - Administrative Safeguards (§164.308)
    - Physical Safeguards (§164.310)
    - Technical Safeguards (§164.312)
    - Organizational Requirements (§164.314)
    - Policies and Procedures (§164.316)
    """
    
    def __init__(
        self,
        config_manager: EncryptedConfigManager,
        audit_logger: AuditLogger,
    ):
        """Initialize HIPAA compliance manager."""
        super().__init__(ComplianceFramework.HIPAA, config_manager, audit_logger)
        self.logger = logging.getLogger(__name__)
        
        # Initialize HIPAA-specific tracking
        self._phi_access_log: List[Dict[str, Any]] = []
        self._workforce_training: Dict[str, datetime] = {}
        self._access_authorizations: Dict[str, Set[str]] = {}
        self._contingency_plan_tested: Optional[datetime] = None
        self._risk_assessment_date: Optional[datetime] = None
    
    def _initialize_requirements(self) -> None:
        """Initialize HIPAA compliance requirements."""
        # Administrative Safeguards - §164.308
        self._add_administrative_safeguards()
        
        # Physical Safeguards - §164.310
        self._add_physical_safeguards()
        
        # Technical Safeguards - §164.312
        self._add_technical_safeguards()
        
        # Organizational Requirements - §164.314
        self._add_organizational_requirements()
        
        # Policies and Procedures - §164.316
        self._add_policies_procedures()
    
    def _add_administrative_safeguards(self) -> None:
        """Add administrative safeguard requirements."""
        # Security Officer - §164.308(a)(2)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-1",
            name="Security Officer Designation",
            description="Identify the security official responsible for developing and implementing security policies",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(2)",
            verification_method="Check security officer configuration",
            automated=True,
            controls=["security_officer_assigned"],
        ))
        
        # Workforce Training - §164.308(a)(5)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-2",
            name="Security Awareness Training",
            description="Implement security awareness and training program for all workforce members",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(5)(i)",
            verification_method="Check training completion records",
            automated=True,
            controls=["workforce_training_completed", "periodic_reminders"],
        ))
        
        # Access Management - §164.308(a)(4)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-3",
            name="Access Authorization",
            description="Implement procedures for granting access to ePHI",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(4)(ii)(B)",
            verification_method="Check access authorization procedures",
            automated=True,
            controls=["access_authorization_process", "access_review_process"],
        ))
        
        # Workforce Clearance - §164.308(a)(3)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-4",
            name="Workforce Clearance Procedure",
            description="Implement procedures to determine access appropriateness",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=2,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(3)(ii)(B)",
            verification_method="Check workforce clearance procedures",
            automated=False,
            controls=["background_check_process", "access_determination"],
        ))
        
        # Risk Assessment - §164.308(a)(1)(ii)(A)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-5",
            name="Risk Assessment",
            description="Conduct accurate and thorough assessment of potential risks to ePHI",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(1)(ii)(A)",
            verification_method="Check risk assessment documentation",
            automated=True,
            controls=["risk_assessment_completed", "risk_assessment_current"],
        ))
        
        # Sanction Policy - §164.308(a)(1)(ii)(C)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-6",
            name="Sanction Policy",
            description="Apply appropriate sanctions against workforce members who violate policies",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=2,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(1)(ii)(C)",
            verification_method="Check sanction policy existence",
            automated=True,
            controls=["sanction_policy_defined", "violation_tracking"],
        ))
        
        # Information System Review - §164.308(a)(8)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-7",
            name="Information System Activity Review",
            description="Regularly review information system activity records",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=2,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(8)",
            verification_method="Check audit log review process",
            automated=True,
            controls=["audit_log_review", "anomaly_detection"],
        ))
        
        # Contingency Plan - §164.308(a)(7)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-AS-8",
            name="Contingency Plan",
            description="Establish data backup, disaster recovery, and emergency mode operation plans",
            category=RequirementCategory.ADMINISTRATIVE,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.308(a)(7)(i)",
            verification_method="Check contingency plan documentation",
            automated=True,
            controls=["backup_procedures", "disaster_recovery_plan", "emergency_access"],
        ))
    
    def _add_physical_safeguards(self) -> None:
        """Add physical safeguard requirements."""
        # Facility Access Controls - §164.310(a)(1)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-PS-1",
            name="Facility Access Controls",
            description="Limit physical access to electronic information systems",
            category=RequirementCategory.PHYSICAL,
            priority=2,
            framework=ComplianceFramework.HIPAA,
            reference="§164.310(a)(1)",
            verification_method="Check facility access controls",
            automated=False,
            controls=["physical_access_control", "visitor_control"],
        ))
        
        # Workstation Use - §164.310(b)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-PS-2",
            name="Workstation Use",
            description="Specify proper functions and physical attributes of workstation surroundings",
            category=RequirementCategory.PHYSICAL,
            priority=2,
            framework=ComplianceFramework.HIPAA,
            reference="§164.310(b)",
            verification_method="Check workstation policies",
            automated=True,
            controls=["workstation_policy", "screen_privacy"],
        ))
        
        # Device and Media Controls - §164.310(d)(1)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-PS-3",
            name="Device and Media Controls",
            description="Implement policies for disposal and re-use of electronic media",
            category=RequirementCategory.PHYSICAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.310(d)(1)",
            verification_method="Check media disposal procedures",
            automated=True,
            controls=["media_disposal", "media_sanitization", "device_inventory"],
        ))
    
    def _add_technical_safeguards(self) -> None:
        """Add technical safeguard requirements."""
        # Access Control - §164.312(a)(1)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-TS-1",
            name="Unique User Identification",
            description="Assign unique name/number for identifying and tracking user identity",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.312(a)(2)(i)",
            verification_method="Check unique user identification",
            automated=True,
            controls=["unique_user_ids", "user_tracking"],
        ))
        
        # Automatic Logoff - §164.312(a)(2)(iii)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-TS-2",
            name="Automatic Logoff",
            description="Implement electronic procedures to terminate session after predetermined inactivity",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.312(a)(2)(iii)",
            verification_method="Check automatic logoff configuration",
            automated=True,
            controls=["session_timeout", "auto_lock"],
        ))
        
        # Audit Controls - §164.312(b)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-TS-3",
            name="Audit Controls",
            description="Implement hardware, software, and procedural mechanisms to record ePHI access",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.312(b)",
            verification_method="Check audit logging implementation",
            automated=True,
            controls=["comprehensive_audit_logging", "log_integrity", "log_retention"],
        ))
        
        # Integrity - §164.312(c)(1)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-TS-4",
            name="Data Integrity Controls",
            description="Implement electronic mechanisms to ensure ePHI is not improperly altered",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.312(c)(1)",
            verification_method="Check data integrity controls",
            automated=True,
            controls=["data_validation", "integrity_checking", "version_control"],
        ))
        
        # Transmission Security - §164.312(e)(1)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-TS-5",
            name="Transmission Security",
            description="Implement technical security measures to guard against unauthorized ePHI access during transmission",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.312(e)(1)",
            verification_method="Check transmission encryption",
            automated=True,
            controls=["transmission_encryption", "secure_protocols"],
        ))
        
        # Encryption and Decryption - §164.312(a)(2)(iv)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-TS-6",
            name="Encryption and Decryption",
            description="Implement mechanism to encrypt and decrypt ePHI",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.312(a)(2)(iv)",
            verification_method="Check encryption implementation",
            automated=True,
            controls=["data_encryption", "key_management"],
        ))
    
    def _add_organizational_requirements(self) -> None:
        """Add organizational requirements."""
        # Business Associate Contracts - §164.314(a)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-OR-1",
            name="Business Associate Agreements",
            description="Obtain satisfactory assurances from business associates",
            category=RequirementCategory.ORGANIZATIONAL,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.314(a)(1)",
            verification_method="Check BAA documentation",
            automated=False,
            controls=["baa_tracking", "vendor_management"],
        ))
        
        # Requirements for Group Health Plans - §164.314(b)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-OR-2",
            name="Group Health Plan Requirements",
            description="Ensure plan documents incorporate provisions for ePHI security",
            category=RequirementCategory.ORGANIZATIONAL,
            priority=3,
            framework=ComplianceFramework.HIPAA,
            reference="§164.314(b)(1)",
            verification_method="Check plan documentation",
            automated=False,
            controls=["plan_documents"],
        ))
    
    def _add_policies_procedures(self) -> None:
        """Add policies and procedures requirements."""
        # Policies and Procedures - §164.316(a)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-PP-1",
            name="Security Policies and Procedures",
            description="Implement reasonable and appropriate policies and procedures",
            category=RequirementCategory.DOCUMENTATION,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.316(a)",
            verification_method="Check policy documentation",
            automated=True,
            controls=["security_policies", "procedure_documentation"],
        ))
        
        # Documentation - §164.316(b)(1)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-PP-2",
            name="Documentation Requirements",
            description="Maintain written record of required policies and procedures",
            category=RequirementCategory.DOCUMENTATION,
            priority=1,
            framework=ComplianceFramework.HIPAA,
            reference="§164.316(b)(1)",
            verification_method="Check documentation retention",
            automated=True,
            controls=["documentation_retention", "version_control"],
        ))
        
        # Updates - §164.316(b)(2)(iii)
        self.add_requirement(ComplianceRequirement(
            id="HIPAA-PP-3",
            name="Periodic Updates",
            description="Review and update documentation in response to environmental changes",
            category=RequirementCategory.DOCUMENTATION,
            priority=2,
            framework=ComplianceFramework.HIPAA,
            reference="§164.316(b)(2)(iii)",
            verification_method="Check update procedures",
            automated=True,
            controls=["periodic_review", "change_management"],
        ))
    
    def verify_requirement(
        self, requirement_id: str, evidence: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify if a specific HIPAA requirement is met.
        
        Args:
            requirement_id: The requirement to verify
            evidence: Optional evidence supporting compliance
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        requirement = self.get_requirement(requirement_id)
        if not requirement:
            return False, f"Unknown requirement: {requirement_id}"
        
        # Route to specific verification method based on requirement
        verification_methods = {
            "HIPAA-AS-1": self._verify_security_officer,
            "HIPAA-AS-2": self._verify_workforce_training,
            "HIPAA-AS-3": self._verify_access_authorization,
            "HIPAA-AS-5": self._verify_risk_assessment,
            "HIPAA-AS-6": self._verify_sanction_policy,
            "HIPAA-AS-7": self._verify_audit_review,
            "HIPAA-AS-8": self._verify_contingency_plan,
            "HIPAA-TS-1": self._verify_unique_users,
            "HIPAA-TS-2": self._verify_automatic_logoff,
            "HIPAA-TS-3": self._verify_audit_controls,
            "HIPAA-TS-4": self._verify_data_integrity,
            "HIPAA-TS-5": self._verify_transmission_security,
            "HIPAA-TS-6": self._verify_encryption,
            "HIPAA-PP-1": self._verify_security_policies,
            "HIPAA-PP-2": self._verify_documentation,
            "HIPAA-PP-3": self._verify_periodic_updates,
        }
        
        verify_method = verification_methods.get(requirement_id)
        if verify_method:
            return verify_method()
        
        # For non-automated requirements, check if manually marked as implemented
        if not requirement.automated and requirement.implemented:
            return True, None
        
        return False, "Requirement not implemented or verified"
    
    def _verify_security_officer(self) -> Tuple[bool, Optional[str]]:
        """Verify security practices for personal health data."""
        # For single-user app, verify security settings are enabled
        if not self.config.get_config("security.lock_on_idle", True):
            return False, "Auto-lock not enabled for health data protection"
        
        if not self.config.get_config("security.clear_clipboard_timeout", 45) <= 45:
            return False, "Clipboard timeout too long for health data"
        
        return True, None
    
    def _verify_workforce_training(self) -> Tuple[bool, Optional[str]]:
        """Verify personal security awareness for health data."""
        # For single-user app, check if health data review reminders are configured
        review_days = self.config.get_config("compliance.health_data_review_days", 90)
        
        if review_days > 365:
            return False, "Health data review interval too long (should be < 1 year)"
        
        # Verify backup practices for health data
        backup_days = self.config.get_config("compliance.backup_verification_days", 30)
        if backup_days > 90:
            return False, "Backup verification interval too long for health data"
        
        return True, None
    
    def _verify_access_authorization(self) -> Tuple[bool, Optional[str]]:
        """Verify access authorization procedures."""
        # For single-user application, access is controlled by master password
        # Check if strong authentication is enabled
        if not self.config.get_config("security.require_authentication", True):
            return False, "Authentication not properly configured"
        
        # Check if auto-lock is enabled for security
        if not self.config.get_config("security.lock_on_idle", True):
            return False, "Auto-lock not enabled for idle sessions"
        
        # Check review interval
        review_interval = access_review.get("interval_days", 90)
        last_review = access_review.get("last_review_date")
        
        if last_review:
            last_date = datetime.fromisoformat(last_review)
            if datetime.now() - last_date > timedelta(days=review_interval):
                return False, f"Access review overdue (last: {last_review})"
        else:
            return False, "No access review performed"
        
        return True, None
    
    def _verify_risk_assessment(self) -> Tuple[bool, Optional[str]]:
        """Verify risk assessment completion."""
        risk_assessment = self.config.get_config("compliance.hipaa.risk_assessment", {})
        
        if not risk_assessment.get("completed", False):
            return False, "Risk assessment not completed"
        
        # Check if assessment is current (within 1 year)
        assessment_date = risk_assessment.get("date")
        if assessment_date:
            date = datetime.fromisoformat(assessment_date)
            if datetime.now() - date > timedelta(days=365):
                return False, f"Risk assessment outdated (date: {assessment_date})"
        else:
            return False, "Risk assessment date not recorded"
        
        return True, None
    
    def _verify_sanction_policy(self) -> Tuple[bool, Optional[str]]:
        """Verify sanction policy existence."""
        sanction_policy = self.config.get_config("compliance.hipaa.sanction_policy", {})
        
        if not sanction_policy.get("defined", False):
            return False, "Sanction policy not defined"
        
        # Check required components
        required_components = ["violation_levels", "sanctions", "appeal_process"]
        for component in required_components:
            if component not in sanction_policy:
                return False, f"Sanction policy missing: {component}"
        
        return True, None
    
    def _verify_audit_review(self) -> Tuple[bool, Optional[str]]:
        """Verify audit log review process."""
        # Check if audit logging is enabled
        audit_config = self.config.get_config("security.audit", {})
        if not audit_config.get("enabled", False):
            return False, "Audit logging not enabled"
        
        # Check review process
        review_config = self.config.get_config("compliance.hipaa.audit_review", {})
        if not review_config.get("enabled", False):
            return False, "Audit review process not configured"
        
        # Check review frequency
        review_interval = review_config.get("interval_days", 7)
        last_review = review_config.get("last_review_date")
        
        if last_review:
            last_date = datetime.fromisoformat(last_review)
            if datetime.now() - last_date > timedelta(days=review_interval):
                return False, f"Audit review overdue (last: {last_review})"
        else:
            return False, "No audit review performed"
        
        return True, None
    
    def _verify_contingency_plan(self) -> Tuple[bool, Optional[str]]:
        """Verify contingency plan existence and testing."""
        contingency = self.config.get_config("compliance.hipaa.contingency_plan", {})
        
        if not contingency.get("documented", False):
            return False, "Contingency plan not documented"
        
        # Check required components
        required = ["data_backup", "disaster_recovery", "emergency_mode"]
        for component in required:
            if not contingency.get(component, {}).get("defined", False):
                return False, f"Contingency plan missing: {component}"
        
        # Check testing
        last_test = contingency.get("last_test_date")
        if last_test:
            test_date = datetime.fromisoformat(last_test)
            if datetime.now() - test_date > timedelta(days=180):  # 6 months
                return False, f"Contingency plan test overdue (last: {last_test})"
        else:
            return False, "Contingency plan never tested"
        
        return True, None
    
    def _verify_unique_users(self) -> Tuple[bool, Optional[str]]:
        """Verify unique user identification."""
        # This would check the actual user management system
        # For now, we'll check configuration
        user_config = self.config.get_config("security.user_management", {})
        
        if not user_config.get("unique_ids_enforced", False):
            return False, "Unique user IDs not enforced"
        
        if not user_config.get("user_tracking_enabled", False):
            return False, "User tracking not enabled"
        
        return True, None
    
    def _verify_automatic_logoff(self) -> Tuple[bool, Optional[str]]:
        """Verify automatic logoff configuration."""
        # Check auto-lock settings
        auto_lock = self.config.get_config("security.auto_lock", {})
        
        if not auto_lock.get("enabled", False):
            return False, "Auto-lock not enabled"
        
        # HIPAA recommends max 30 minutes of inactivity
        timeout_minutes = auto_lock.get("timeout_minutes", 30)
        if timeout_minutes > 30:
            return False, f"Auto-lock timeout too long: {timeout_minutes} minutes (max: 30)"
        
        return True, None
    
    def _verify_audit_controls(self) -> Tuple[bool, Optional[str]]:
        """Verify audit control implementation."""
        audit_config = self.config.get_config("security.audit", {})
        
        if not audit_config.get("enabled", False):
            return False, "Audit logging not enabled"
        
        # Check comprehensive logging
        required_events = [
            "authentication", "password_access", "configuration_changes",
            "data_export", "security_violations"
        ]
        
        logged_events = audit_config.get("logged_events", [])
        missing_events = [e for e in required_events if e not in logged_events]
        
        if missing_events:
            return False, f"Missing audit events: {', '.join(missing_events)}"
        
        # Check log integrity
        if not audit_config.get("integrity_protection", False):
            return False, "Audit log integrity protection not enabled"
        
        # Check retention (HIPAA requires 6 years)
        retention_days = audit_config.get("retention_days", 0)
        if retention_days < 2190:  # 6 years
            return False, f"Audit log retention too short: {retention_days} days (min: 2190)"
        
        return True, None
    
    def _verify_data_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify data integrity controls."""
        # Check if version control is enabled
        version_control = self.config.get_config("security.version_control", {})
        if not version_control.get("enabled", False):
            return False, "Version control not enabled"
        
        # Check integrity validation
        integrity = self.config.get_config("security.data_integrity", {})
        if not integrity.get("validation_enabled", False):
            return False, "Data integrity validation not enabled"
        
        return True, None
    
    def _verify_transmission_security(self) -> Tuple[bool, Optional[str]]:
        """Verify transmission security."""
        # Check Git operations encryption
        git_config = self.config.get_config("security.git", {})
        if not git_config.get("https_only", False):
            return False, "Git operations not restricted to HTTPS"
        
        # Check certificate pinning
        cert_pinning = self.config.get_config("security.certificate_pinning", {})
        if not cert_pinning.get("enabled", False):
            return False, "Certificate pinning not enabled"
        
        return True, None
    
    def _verify_encryption(self) -> Tuple[bool, Optional[str]]:
        """Verify encryption implementation."""
        # Check GPG configuration
        gpg_config = self.config.get_config("security.gpg", {})
        
        # Check key strength (HIPAA recommends minimum 2048-bit)
        min_key_size = gpg_config.get("min_key_size", 2048)
        if min_key_size < 2048:
            return False, f"GPG key size too small: {min_key_size} bits (min: 2048)"
        
        # Check if encryption is enforced
        if not gpg_config.get("encryption_required", True):
            return False, "Encryption not enforced"
        
        return True, None
    
    def _verify_security_policies(self) -> Tuple[bool, Optional[str]]:
        """Verify security policies documentation."""
        policies = self.config.get_config("compliance.hipaa.security_policies", {})
        
        if not policies.get("documented", False):
            return False, "Security policies not documented"
        
        # Check required policies
        required_policies = [
            "access_control", "workforce_training", "incident_response",
            "data_backup", "risk_management", "physical_security"
        ]
        
        documented_policies = policies.get("policies", [])
        missing_policies = [p for p in required_policies if p not in documented_policies]
        
        if missing_policies:
            return False, f"Missing policies: {', '.join(missing_policies)}"
        
        return True, None
    
    def _verify_documentation(self) -> Tuple[bool, Optional[str]]:
        """Verify documentation requirements."""
        documentation = self.config.get_config("compliance.hipaa.documentation", {})
        
        # Check retention period (HIPAA requires 6 years)
        retention_years = documentation.get("retention_years", 0)
        if retention_years < 6:
            return False, f"Documentation retention too short: {retention_years} years (min: 6)"
        
        # Check version control
        if not documentation.get("version_controlled", False):
            return False, "Documentation not version controlled"
        
        return True, None
    
    def _verify_periodic_updates(self) -> Tuple[bool, Optional[str]]:
        """Verify periodic update procedures."""
        updates = self.config.get_config("compliance.hipaa.periodic_updates", {})
        
        if not updates.get("process_defined", False):
            return False, "Update process not defined"
        
        # Check review frequency
        review_interval = updates.get("review_interval_days", 365)
        last_review = updates.get("last_review_date")
        
        if last_review:
            review_date = datetime.fromisoformat(last_review)
            if datetime.now() - review_date > timedelta(days=review_interval):
                return False, f"Documentation review overdue (last: {last_review})"
        else:
            return False, "Documentation never reviewed"
        
        return True, None
    
    def log_phi_access(
        self,
        user_id: str,
        patient_id: str,
        access_type: str,
        purpose: str,
        data_accessed: List[str]
    ) -> None:
        """
        Log PHI (Protected Health Information) access for HIPAA compliance.
        
        Args:
            user_id: User accessing the PHI
            patient_id: Patient whose PHI was accessed
            access_type: Type of access (read, write, delete)
            purpose: Purpose of access
            data_accessed: List of data elements accessed
        """
        access_record = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "patient_id": patient_id,
            "access_type": access_type,
            "purpose": purpose,
            "data_accessed": data_accessed,
        }
        
        self._phi_access_log.append(access_record)
        
        # Also log to audit system
        self.audit.audit_compliance_event(
            framework="HIPAA",
            event_type="phi_access",
            details=access_record
        )
    
    def record_workforce_training(
        self,
        user_id: str,
        training_type: str,
        completion_date: Optional[datetime] = None
    ) -> None:
        """
        Record workforce training completion.
        
        Args:
            user_id: User who completed training
            training_type: Type of training completed
            completion_date: Date of completion (defaults to now)
        """
        if completion_date is None:
            completion_date = datetime.now()
        
        self._workforce_training[user_id] = completion_date
        
        # Update configuration
        training_records = self.config.get_config(
            "compliance.hipaa.workforce_training.records", {}
        )
        training_records[user_id] = {
            "type": training_type,
            "completion_date": completion_date.isoformat(),
        }
        self.config.set_config(
            "compliance.hipaa.workforce_training.records", training_records
        )
        
        # Log the training
        self.audit.audit_compliance_event(
            framework="HIPAA",
            event_type="training_completed",
            details={
                "user_id": user_id,
                "training_type": training_type,
                "completion_date": completion_date.isoformat(),
            }
        )
    
    def authorize_access(
        self,
        user_id: str,
        resource: str,
        access_level: str,
        justification: str
    ) -> bool:
        """
        Authorize user access to a resource.
        
        Args:
            user_id: User requesting access
            resource: Resource to access
            access_level: Level of access requested
            justification: Business justification
            
        Returns:
            True if access granted, False otherwise
        """
        # Check if user has existing authorization
        user_authorizations = self._access_authorizations.get(user_id, set())
        
        # Simple authorization check (would be more complex in production)
        auth_key = f"{resource}:{access_level}"
        authorized = auth_key in user_authorizations
        
        # Log the authorization attempt
        self.audit.audit_compliance_event(
            framework="HIPAA",
            event_type="access_authorization",
            details={
                "user_id": user_id,
                "resource": resource,
                "access_level": access_level,
                "justification": justification,
                "granted": authorized,
            }
        )
        
        return authorized
    
    def generate_hipaa_report(self) -> str:
        """
        Generate a HIPAA compliance report.
        
        Returns:
            HTML formatted compliance report
        """
        report = self.assess_compliance()
        
        # Add HIPAA-specific sections
        hipaa_html = f"""
        <div class="section">
            <h2>HIPAA-Specific Compliance Details</h2>
            
            <h3>Administrative Safeguards</h3>
            <ul>
                <li>Security Officer: {self._check_status('HIPAA-AS-1')}</li>
                <li>Workforce Training: {self._check_status('HIPAA-AS-2')}</li>
                <li>Access Management: {self._check_status('HIPAA-AS-3')}</li>
                <li>Risk Assessment: {self._check_status('HIPAA-AS-5')}</li>
            </ul>
            
            <h3>Technical Safeguards</h3>
            <ul>
                <li>Access Controls: {self._check_status('HIPAA-TS-1')}</li>
                <li>Audit Controls: {self._check_status('HIPAA-TS-3')}</li>
                <li>Integrity Controls: {self._check_status('HIPAA-TS-4')}</li>
                <li>Transmission Security: {self._check_status('HIPAA-TS-5')}</li>
                <li>Encryption: {self._check_status('HIPAA-TS-6')}</li>
            </ul>
            
            <h3>Recent PHI Access</h3>
            <p>Total PHI access events: {len(self._phi_access_log)}</p>
            
            <h3>Workforce Training Status</h3>
            <p>Trained users: {len(self._workforce_training)}</p>
        </div>
        """
        
        # Insert HIPAA section into base report
        base_html = self.export_report(report, "html")
        return base_html.replace("</body>", hipaa_html + "</body>")
    
    def _check_status(self, requirement_id: str) -> str:
        """Check and format requirement status."""
        is_compliant, reason = self.verify_requirement(requirement_id)
        if is_compliant:
            return "✓ Compliant"
        else:
            return f"✗ Non-compliant: {reason}"