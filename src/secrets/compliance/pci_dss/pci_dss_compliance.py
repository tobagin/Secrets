"""
PCI DSS compliance implementation for Secrets Password Manager.

This module implements the Payment Card Industry Data Security Standard (PCI DSS)
compliance requirements for systems that handle payment card data.
"""

import hashlib
import logging
import re
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


class PCIDSSComplianceManager(ComplianceManager):
    """
    PCI DSS compliance manager implementation.
    
    Implements PCI DSS v4.0 requirements across 12 main requirements:
    1. Install and maintain network security controls
    2. Apply secure configurations to all system components
    3. Protect stored account data
    4. Protect cardholder data with strong cryptography during transmission
    5. Protect all systems and networks from malicious software
    6. Develop and maintain secure systems and software
    7. Restrict access to system components and cardholder data by business need to know
    8. Identify users and authenticate access to system components
    9. Restrict physical access to cardholder data
    10. Log and monitor all access to system components and cardholder data
    11. Test security of systems and networks regularly
    12. Support information security with organizational policies and programs
    """
    
    def __init__(
        self,
        config_manager: EncryptedConfigManager,
        audit_logger: AuditLogger,
    ):
        """Initialize PCI DSS compliance manager."""
        super().__init__(ComplianceFramework.PCI_DSS, config_manager, audit_logger)
        self.logger = logging.getLogger(__name__)
        
        # PCI DSS specific tracking
        self._password_history: Dict[str, List[str]] = {}  # User -> password hashes
        self._failed_login_attempts: Dict[str, List[datetime]] = {}
        self._vulnerability_scans: List[Dict[str, Any]] = []
        self._key_rotation_dates: Dict[str, datetime] = {}
        self._card_data_access_log: List[Dict[str, Any]] = []
    
    def _initialize_requirements(self) -> None:
        """Initialize PCI DSS compliance requirements."""
        # Requirement 1: Network Security Controls
        self._add_network_security_requirements()
        
        # Requirement 2: Secure Configurations
        self._add_secure_configuration_requirements()
        
        # Requirement 3: Protect Stored Account Data
        self._add_data_protection_requirements()
        
        # Requirement 4: Transmission Encryption
        self._add_transmission_encryption_requirements()
        
        # Requirement 5: Malware Protection
        self._add_malware_protection_requirements()
        
        # Requirement 6: Secure Development
        self._add_secure_development_requirements()
        
        # Requirement 7: Access Restriction
        self._add_access_restriction_requirements()
        
        # Requirement 8: User Authentication
        self._add_authentication_requirements()
        
        # Requirement 9: Physical Access
        self._add_physical_access_requirements()
        
        # Requirement 10: Logging and Monitoring
        self._add_logging_monitoring_requirements()
        
        # Requirement 11: Security Testing
        self._add_security_testing_requirements()
        
        # Requirement 12: Organizational Policies
        # Organizational policies not relevant for personal use
    
    def _add_network_security_requirements(self) -> None:
        """Add Requirement 1: Network Security Controls."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-1.1",
            name="Network Security Controls",
            description="Install and maintain network security controls",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 1",
            verification_method="Check network security configuration",
            automated=True,
            controls=["firewall_configuration", "network_segmentation"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-1.2",
            name="Network Segmentation",
            description="Network segmentation to isolate cardholder data environment",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 1.2",
            verification_method="Verify network segmentation",
            automated=False,
            controls=["network_isolation", "cde_boundaries"],
        ))
    
    def _add_secure_configuration_requirements(self) -> None:
        """Add Requirement 2: Secure Configurations."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-2.1",
            name="Default Credentials",
            description="Change all default passwords and remove unnecessary default accounts",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 2.1",
            verification_method="Check for default credentials",
            automated=True,
            controls=["no_default_passwords", "account_review"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-2.2",
            name="System Hardening",
            description="Develop configuration standards for all system components",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 2.2",
            verification_method="Check system hardening standards",
            automated=True,
            controls=["hardening_standards", "secure_configurations"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-2.3",
            name="Encryption of Non-Console Access",
            description="Encrypt all non-console administrative access",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 2.3",
            verification_method="Verify encrypted administrative access",
            automated=True,
            controls=["encrypted_admin_access", "secure_protocols"],
        ))
    
    def _add_data_protection_requirements(self) -> None:
        """Add Requirement 3: Protect Stored Account Data."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-3.1",
            name="Data Retention and Disposal",
            description="Limit data retention and define disposal procedures",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 3.1",
            verification_method="Check data retention policies",
            automated=True,
            controls=["retention_policy", "secure_deletion"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-3.2",
            name="Sensitive Authentication Data",
            description="Do not store sensitive authentication data after authorization",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 3.2",
            verification_method="Check for stored sensitive data",
            automated=True,
            controls=["no_sad_storage", "data_discovery"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-3.4",
            name="PAN Masking",
            description="Render PAN unreadable anywhere it is stored",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 3.4",
            verification_method="Verify PAN encryption/masking",
            automated=True,
            controls=["pan_encryption", "data_masking"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-3.5",
            name="Cryptographic Key Management",
            description="Protect cryptographic keys used for cardholder data encryption",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 3.5",
            verification_method="Check key management procedures",
            automated=True,
            controls=["key_management", "key_rotation", "split_knowledge"],
        ))
    
    def _add_transmission_encryption_requirements(self) -> None:
        """Add Requirement 4: Transmission Encryption."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-4.1",
            name="Transmission Encryption",
            description="Use strong cryptography during transmission over public networks",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 4.1",
            verification_method="Verify transmission encryption",
            automated=True,
            controls=["tls_encryption", "strong_protocols"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-4.2",
            name="End-User Messaging",
            description="Never send unprotected PANs via end-user messaging",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 4.2",
            verification_method="Check messaging controls",
            automated=False,
            controls=["messaging_controls", "data_classification"],
        ))
    
    def _add_malware_protection_requirements(self) -> None:
        """Add Requirement 5: Malware Protection."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-5.1",
            name="Anti-Malware Deployment",
            description="Deploy anti-malware solutions on all systems",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 5.1",
            verification_method="Check anti-malware deployment",
            automated=False,
            controls=["antivirus_deployed", "malware_protection"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-5.2",
            name="Anti-Malware Updates",
            description="Ensure anti-malware solutions are kept current",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 5.2",
            verification_method="Check anti-malware update status",
            automated=False,
            controls=["signature_updates", "regular_scans"],
        ))
    
    def _add_secure_development_requirements(self) -> None:
        """Add Requirement 6: Secure Development."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-6.1",
            name="Vulnerability Management",
            description="Identify and manage security vulnerabilities",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 6.1",
            verification_method="Check vulnerability management process",
            automated=True,
            controls=["vulnerability_scanning", "patch_management"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-6.2",
            name="Security Patches",
            description="Install applicable security patches within appropriate timeframes",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 6.2",
            verification_method="Check patch management",
            automated=True,
            controls=["patch_timeline", "critical_patches"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-6.3",
            name="Secure Development Lifecycle",
            description="Develop software securely",
            category=RequirementCategory.TECHNICAL,
            priority=2,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 6.3",
            verification_method="Review SDLC processes",
            automated=False,
            controls=["secure_coding", "code_review", "security_testing"],
        ))
    
    def _add_access_restriction_requirements(self) -> None:
        """Add Requirement 7: Access Restriction."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-7.1",
            name="Least Privilege",
            description="Limit access to system components by business need to know",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 7.1",
            verification_method="Review access control implementation",
            automated=True,
            controls=["least_privilege", "need_to_know"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-7.2",
            name="Access Control Systems",
            description="Establish access control systems for cardholder data",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 7.2",
            verification_method="Check access control systems",
            automated=True,
            controls=["access_control", "access_policies"],
        ))
    
    def _add_authentication_requirements(self) -> None:
        """Add Requirement 8: User Authentication."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-8.1",
            name="User Identification",
            description="Assign unique ID to each person with computer access",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 8.2",
            verification_method="Check unique user IDs",
            automated=True,
            controls=["unique_user_ids", "no_shared_accounts"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-8.2",
            name="Strong Authentication",
            description="Implement strong authentication methods",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 8.3",
            verification_method="Verify authentication strength",
            automated=True,
            controls=["password_complexity", "mfa_implementation"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-8.3",
            name="Password Requirements",
            description="Password/passphrase meets minimum requirements",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 8.3.6",
            verification_method="Check password policy",
            automated=True,
            controls=[
                "min_length_12",
                "complexity_requirements",
                "password_history",
                "password_expiry",
            ],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-8.4",
            name="Account Lockout",
            description="Lock out user after failed access attempts",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 8.3.4",
            verification_method="Check account lockout policy",
            automated=True,
            controls=["lockout_threshold", "lockout_duration"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-8.5",
            name="Session Management",
            description="Idle sessions timeout after 15 minutes or less",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 8.2.8",
            verification_method="Check session timeout",
            automated=True,
            controls=["session_timeout", "re_authentication"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-8.6",
            name="Multi-Factor Authentication",
            description="MFA for all non-console access",
            category=RequirementCategory.ACCESS_CONTROL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 8.4",
            verification_method="Verify MFA implementation",
            automated=True,
            controls=["mfa_required", "mfa_methods"],
        ))
    
    def _add_physical_access_requirements(self) -> None:
        """Add Requirement 9: Physical Access."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-9.1",
            name="Physical Access Controls",
            description="Limit physical access to cardholder data",
            category=RequirementCategory.PHYSICAL,
            priority=2,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 9.1",
            verification_method="Review physical security controls",
            automated=False,
            controls=["physical_access_controls", "visitor_management"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-9.2",
            name="Media Protection",
            description="Protect media containing cardholder data",
            category=RequirementCategory.PHYSICAL,
            priority=2,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 9.4",
            verification_method="Check media protection procedures",
            automated=False,
            controls=["media_inventory", "secure_storage", "media_destruction"],
        ))
    
    def _add_logging_monitoring_requirements(self) -> None:
        """Add Requirement 10: Logging and Monitoring."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-10.1",
            name="Audit Trail Implementation",
            description="Implement audit trails for all system components",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 10.2",
            verification_method="Verify audit trail coverage",
            automated=True,
            controls=["comprehensive_logging", "log_all_access"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-10.2",
            name="Log Events",
            description="Log all required security events",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 10.2.1",
            verification_method="Check logged event types",
            automated=True,
            controls=[
                "user_access_logs",
                "privileged_actions",
                "access_denials",
                "system_events",
            ],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-10.3",
            name="Log Protection",
            description="Protect audit trail files from unauthorized modifications",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 10.3",
            verification_method="Verify log protection mechanisms",
            automated=True,
            controls=["log_integrity", "access_controls", "centralized_logging"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-10.4",
            name="Log Review",
            description="Review logs of all system components daily",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 10.4",
            verification_method="Check log review process",
            automated=True,
            controls=["daily_review", "exception_reporting", "follow_up"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-10.5",
            name="Log Retention",
            description="Retain audit logs for at least one year",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 10.5.1",
            verification_method="Check log retention period",
            automated=True,
            controls=["retention_period", "online_availability"],
        ))
    
    def _add_security_testing_requirements(self) -> None:
        """Add Requirement 11: Security Testing."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-11.1",
            name="Network Vulnerability Scanning",
            description="Test for presence of wireless access points quarterly",
            category=RequirementCategory.MONITORING,
            priority=2,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 11.2",
            verification_method="Review scanning results",
            automated=False,
            controls=["wireless_scanning", "rogue_detection"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-11.2",
            name="Vulnerability Scanning",
            description="Run internal and external vulnerability scans quarterly",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 11.3",
            verification_method="Check scan reports",
            automated=True,
            controls=["quarterly_scans", "remediation_process"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-11.3",
            name="Penetration Testing",
            description="Perform penetration testing annually",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 11.4",
            verification_method="Review penetration test results",
            automated=False,
            controls=["annual_pentest", "segmentation_testing"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-11.4",
            name="Intrusion Detection",
            description="Deploy intrusion detection/prevention systems",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 11.5",
            verification_method="Check IDS/IPS deployment",
            automated=True,
            controls=["ids_deployment", "alert_monitoring"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-11.5",
            name="File Integrity Monitoring",
            description="Deploy file integrity monitoring",
            category=RequirementCategory.MONITORING,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 11.5.2",
            verification_method="Verify FIM deployment",
            automated=True,
            controls=["fim_deployment", "change_detection"],
        ))
    
    def _add_organizational_policy_requirements(self) -> None:
        """Add Requirement 12: Organizational Policies."""
        self.add_requirement(ComplianceRequirement(
            id="PCI-12.1",
            name="Security Policy",
            description="Establish, publish, and disseminate security policy",
            category=RequirementCategory.ORGANIZATIONAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 12.1",
            verification_method="Review security policy",
            automated=False,
            controls=["security_policy", "annual_review"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-12.2",
            name="Risk Assessment",
            description="Perform formal risk assessment annually",
            category=RequirementCategory.ORGANIZATIONAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 12.3",
            verification_method="Check risk assessment documentation",
            automated=True,
            controls=["annual_risk_assessment", "risk_treatment"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-12.3",
            name="Security Awareness",
            description="Implement security awareness program",
            category=RequirementCategory.ORGANIZATIONAL,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 12.6",
            verification_method="Review training program",
            automated=True,
            controls=["security_training", "annual_training"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="PCI-12.4",
            name="Incident Response",
            description="Implement incident response plan",
            category=RequirementCategory.INCIDENT_RESPONSE,
            priority=1,
            framework=ComplianceFramework.PCI_DSS,
            reference="PCI DSS v4.0 Requirement 12.10",
            verification_method="Review incident response procedures",
            automated=True,
            controls=["incident_response_plan", "24_7_availability"],
        ))
    
    def verify_requirement(
        self, requirement_id: str, evidence: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify if a specific PCI DSS requirement is met.
        
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
            # Network Security
            "PCI-1.1": self._verify_network_security,
            
            # Secure Configurations
            "PCI-2.1": self._verify_default_credentials,
            "PCI-2.2": self._verify_system_hardening,
            "PCI-2.3": self._verify_encrypted_access,
            
            # Data Protection
            "PCI-3.1": self._verify_data_retention,
            "PCI-3.2": self._verify_sad_storage,
            "PCI-3.4": self._verify_pan_masking,
            "PCI-3.5": self._verify_key_management,
            
            # Transmission Security
            "PCI-4.1": self._verify_transmission_encryption,
            
            # Vulnerability Management
            "PCI-6.1": self._verify_vulnerability_management,
            "PCI-6.2": self._verify_patch_management,
            
            # Access Control
            "PCI-7.1": self._verify_least_privilege,
            "PCI-7.2": self._verify_access_control_systems,
            
            # Authentication
            "PCI-8.1": self._verify_unique_ids,
            "PCI-8.2": self._verify_strong_authentication,
            "PCI-8.3": self._verify_password_requirements,
            "PCI-8.4": self._verify_account_lockout,
            "PCI-8.5": self._verify_session_management,
            "PCI-8.6": self._verify_mfa,
            
            # Logging and Monitoring
            "PCI-10.1": self._verify_audit_trails,
            "PCI-10.2": self._verify_log_events,
            "PCI-10.3": self._verify_log_protection,
            "PCI-10.4": self._verify_log_review,
            "PCI-10.5": self._verify_log_retention,
            
            # Security Testing
            "PCI-11.2": self._verify_vulnerability_scanning,
            "PCI-11.4": self._verify_intrusion_detection,
            "PCI-11.5": self._verify_file_integrity,
            
            # Organizational
            "PCI-12.2": self._verify_risk_assessment,
            "PCI-12.3": self._verify_security_awareness,
            "PCI-12.4": self._verify_incident_response,
        }
        
        verify_method = verification_methods.get(requirement_id)
        if verify_method:
            return verify_method()
        
        # For non-automated requirements, check if manually marked as implemented
        if not requirement.automated and requirement.implemented:
            return True, None
        
        return False, "Requirement not implemented or verified"
    
    def _verify_network_security(self) -> Tuple[bool, Optional[str]]:
        """Verify network security controls."""
        network_config = self.config.get_config("security.network", {})
        
        if not network_config.get("firewall_enabled", False):
            return False, "Firewall not enabled"
        
        if not network_config.get("network_segmentation", False):
            return False, "Network segmentation not implemented"
        
        return True, None
    
    def _verify_default_credentials(self) -> Tuple[bool, Optional[str]]:
        """Verify no default credentials are in use."""
        # Check for default password policy
        password_policy = self.config.get_config("security.password_policy", {})
        
        if password_policy.get("allow_default_passwords", True):
            return False, "Default passwords are allowed"
        
        # Check if default account review has been performed
        account_review = self.config.get_config("compliance.pci_dss.account_review", {})
        if not account_review.get("default_accounts_removed", False):
            return False, "Default accounts not reviewed/removed"
        
        return True, None
    
    def _verify_system_hardening(self) -> Tuple[bool, Optional[str]]:
        """Verify system hardening standards."""
        hardening = self.config.get_config("security.system_hardening", {})
        
        if not hardening.get("standards_defined", False):
            return False, "System hardening standards not defined"
        
        # Check if unnecessary services are disabled
        if not hardening.get("unnecessary_services_disabled", False):
            return False, "Unnecessary services not disabled"
        
        return True, None
    
    def _verify_encrypted_access(self) -> Tuple[bool, Optional[str]]:
        """Verify encrypted administrative access."""
        access_config = self.config.get_config("security.administrative_access", {})
        
        if not access_config.get("encryption_required", False):
            return False, "Encryption not required for admin access"
        
        # Check protocols
        allowed_protocols = access_config.get("allowed_protocols", [])
        insecure_protocols = ["telnet", "ftp", "http"]
        
        for protocol in allowed_protocols:
            if protocol.lower() in insecure_protocols:
                return False, f"Insecure protocol allowed: {protocol}"
        
        return True, None
    
    def _verify_data_retention(self) -> Tuple[bool, Optional[str]]:
        """Verify data retention and disposal policies."""
        retention = self.config.get_config("compliance.pci_dss.data_retention", {})
        
        if not retention.get("policy_defined", False):
            return False, "Data retention policy not defined"
        
        # Check if secure deletion is configured
        if not retention.get("secure_deletion_enabled", False):
            return False, "Secure deletion not enabled"
        
        return True, None
    
    def _verify_sad_storage(self) -> Tuple[bool, Optional[str]]:
        """Verify sensitive authentication data is not stored."""
        sad_config = self.config.get_config("compliance.pci_dss.sad_protection", {})
        
        if sad_config.get("stores_cvv", False):
            return False, "System stores CVV data"
        
        if sad_config.get("stores_pin", False):
            return False, "System stores PIN data"
        
        return True, None
    
    def _verify_pan_masking(self) -> Tuple[bool, Optional[str]]:
        """Verify PAN masking implementation."""
        masking = self.config.get_config("security.data_masking", {})
        
        if not masking.get("pan_masking_enabled", False):
            return False, "PAN masking not enabled"
        
        # Check masking format (should show only first 6 and last 4 digits)
        mask_format = masking.get("pan_mask_format", "")
        if mask_format != "XXXXXX******XXXX":
            return False, f"Incorrect PAN masking format: {mask_format}"
        
        return True, None
    
    def _verify_key_management(self) -> Tuple[bool, Optional[str]]:
        """Verify cryptographic key management."""
        key_mgmt = self.config.get_config("security.key_management", {})
        
        if not key_mgmt.get("key_rotation_enabled", False):
            return False, "Key rotation not enabled"
        
        # Check key rotation period (PCI DSS recommends annual)
        rotation_days = key_mgmt.get("rotation_interval_days", 0)
        if rotation_days > 365:
            return False, f"Key rotation interval too long: {rotation_days} days"
        
        # Check split knowledge
        if not key_mgmt.get("split_knowledge", False):
            return False, "Split knowledge not implemented"
        
        # Check dual control
        if not key_mgmt.get("dual_control", False):
            return False, "Dual control not implemented"
        
        return True, None
    
    def _verify_transmission_encryption(self) -> Tuple[bool, Optional[str]]:
        """Verify transmission encryption."""
        transmission = self.config.get_config("security.transmission", {})
        
        if not transmission.get("encryption_required", False):
            return False, "Transmission encryption not required"
        
        # Check minimum TLS version
        min_tls = transmission.get("min_tls_version", "1.0")
        if float(min_tls) < 1.2:
            return False, f"TLS version too old: {min_tls} (min: 1.2)"
        
        return True, None
    
    def _verify_vulnerability_management(self) -> Tuple[bool, Optional[str]]:
        """Verify vulnerability management process."""
        vuln_mgmt = self.config.get_config("compliance.pci_dss.vulnerability_management", {})
        
        if not vuln_mgmt.get("process_defined", False):
            return False, "Vulnerability management process not defined"
        
        # Check if vulnerability sources are monitored
        if not vuln_mgmt.get("sources_monitored", False):
            return False, "Vulnerability sources not monitored"
        
        return True, None
    
    def _verify_patch_management(self) -> Tuple[bool, Optional[str]]:
        """Verify patch management process."""
        patch_mgmt = self.config.get_config("compliance.pci_dss.patch_management", {})
        
        if not patch_mgmt.get("process_defined", False):
            return False, "Patch management process not defined"
        
        # Check critical patch timeline (PCI DSS requires within 1 month)
        critical_timeline = patch_mgmt.get("critical_patch_days", 60)
        if critical_timeline > 30:
            return False, f"Critical patch timeline too long: {critical_timeline} days"
        
        return True, None
    
    def _verify_least_privilege(self) -> Tuple[bool, Optional[str]]:
        """Verify least privilege implementation."""
        access_control = self.config.get_config("security.access_control", {})
        
        if not access_control.get("least_privilege_enforced", False):
            return False, "Least privilege not enforced"
        
        if not access_control.get("need_to_know_basis", False):
            return False, "Need-to-know basis not implemented"
        
        return True, None
    
    def _verify_access_control_systems(self) -> Tuple[bool, Optional[str]]:
        """Verify access control systems."""
        # For single-user application, verify master password protection
        if not self.config.get_config("security.require_authentication", True):
            return False, "Master password authentication not enabled"
        
        # Check password complexity requirements
        if not self.config.get_config("compliance.password_complexity_enabled", True):
            return False, "Password complexity requirements not enabled"
        
        return True, None
    
    def _verify_unique_ids(self) -> Tuple[bool, Optional[str]]:
        """Verify single-user security."""
        # For single-user app, verify master password is required
        if not self.config.get_config("security.require_authentication", True):
            return False, "Master password authentication not enforced"
        
        # No shared accounts in single-user app
        return True, None
    
    def _verify_strong_authentication(self) -> Tuple[bool, Optional[str]]:
        """Verify strong authentication implementation."""
        auth_config = self.config.get_config("security.authentication", {})
        
        if not auth_config.get("strong_auth_required", False):
            return False, "Strong authentication not required"
        
        return True, None
    
    def _verify_password_requirements(self) -> Tuple[bool, Optional[str]]:
        """Verify password requirements meet PCI DSS standards."""
        password_policy = self.config.get_config("security.password_policy", {})
        
        # Check minimum length (PCI DSS v4.0 requires 12 characters)
        min_length = password_policy.get("min_length", 0)
        if min_length < 12:
            return False, f"Password minimum length too short: {min_length} (min: 12)"
        
        # Check complexity requirements
        if not password_policy.get("require_uppercase", False):
            return False, "Uppercase letters not required"
        
        if not password_policy.get("require_lowercase", False):
            return False, "Lowercase letters not required"
        
        if not password_policy.get("require_numbers", False):
            return False, "Numbers not required"
        
        if not password_policy.get("require_special", False):
            return False, "Special characters not required"
        
        # Check password history (PCI DSS requires last 4 passwords)
        history_count = password_policy.get("history_count", 0)
        if history_count < 4:
            return False, f"Password history too short: {history_count} (min: 4)"
        
        # Check password expiry (PCI DSS requires max 90 days)
        expiry_days = password_policy.get("expiry_days", 0)
        if expiry_days == 0 or expiry_days > 90:
            return False, f"Password expiry too long: {expiry_days} days (max: 90)"
        
        return True, None
    
    def _verify_account_lockout(self) -> Tuple[bool, Optional[str]]:
        """Verify account lockout policy."""
        lockout_policy = self.config.get_config("security.account_lockout", {})
        
        if not lockout_policy.get("enabled", False):
            return False, "Account lockout not enabled"
        
        # Check lockout threshold (PCI DSS requires max 6 attempts)
        threshold = lockout_policy.get("failed_attempts", 10)
        if threshold > 6:
            return False, f"Lockout threshold too high: {threshold} (max: 6)"
        
        # Check lockout duration (PCI DSS requires min 30 minutes)
        duration_minutes = lockout_policy.get("lockout_duration_minutes", 0)
        if duration_minutes < 30:
            return False, f"Lockout duration too short: {duration_minutes} min (min: 30)"
        
        return True, None
    
    def _verify_session_management(self) -> Tuple[bool, Optional[str]]:
        """Verify session management."""
        session_config = self.config.get_config("security.session", {})
        
        # Check idle timeout (PCI DSS requires max 15 minutes)
        idle_timeout = session_config.get("idle_timeout_minutes", 30)
        if idle_timeout > 15:
            return False, f"Idle timeout too long: {idle_timeout} min (max: 15)"
        
        # Check re-authentication for sensitive operations
        if not session_config.get("re_auth_required", False):
            return False, "Re-authentication not required for sensitive operations"
        
        return True, None
    
    def _verify_mfa(self) -> Tuple[bool, Optional[str]]:
        """Verify multi-factor authentication."""
        mfa_config = self.config.get_config("security.mfa", {})
        
        if not mfa_config.get("enabled", False):
            return False, "MFA not enabled"
        
        # Check if MFA is required for all non-console access
        if not mfa_config.get("required_for_all_access", False):
            return False, "MFA not required for all non-console access"
        
        # Check MFA methods (should have at least 2)
        methods = mfa_config.get("methods", [])
        if len(methods) < 2:
            return False, f"Insufficient MFA methods: {len(methods)} (min: 2)"
        
        return True, None
    
    def _verify_audit_trails(self) -> Tuple[bool, Optional[str]]:
        """Verify audit trail implementation."""
        audit_config = self.config.get_config("security.audit", {})
        
        if not audit_config.get("enabled", False):
            return False, "Audit trails not enabled"
        
        # Check if all system components are covered
        if not audit_config.get("comprehensive_coverage", False):
            return False, "Audit trails don't cover all system components"
        
        return True, None
    
    def _verify_log_events(self) -> Tuple[bool, Optional[str]]:
        """Verify required events are logged."""
        audit_config = self.config.get_config("security.audit", {})
        
        required_events = [
            "user_access",
            "privileged_actions",
            "access_denials",
            "authentication",
            "authorization",
            "data_access",
            "configuration_changes",
            "system_events",
        ]
        
        logged_events = audit_config.get("logged_events", [])
        missing_events = [e for e in required_events if e not in logged_events]
        
        if missing_events:
            return False, f"Missing log events: {', '.join(missing_events)}"
        
        return True, None
    
    def _verify_log_protection(self) -> Tuple[bool, Optional[str]]:
        """Verify log protection mechanisms."""
        log_protection = self.config.get_config("security.audit.protection", {})
        
        if not log_protection.get("integrity_protection", False):
            return False, "Log integrity protection not enabled"
        
        if not log_protection.get("access_controlled", False):
            return False, "Log access not properly controlled"
        
        if not log_protection.get("centralized_logging", False):
            return False, "Centralized logging not implemented"
        
        return True, None
    
    def _verify_log_review(self) -> Tuple[bool, Optional[str]]:
        """Verify log review process."""
        log_review = self.config.get_config("compliance.pci_dss.log_review", {})
        
        if not log_review.get("daily_review", False):
            return False, "Daily log review not performed"
        
        # Check last review date
        last_review = log_review.get("last_review_date")
        if last_review:
            review_date = datetime.fromisoformat(last_review)
            if datetime.now() - review_date > timedelta(days=1):
                return False, f"Log review overdue (last: {last_review})"
        else:
            return False, "No log review performed"
        
        return True, None
    
    def _verify_log_retention(self) -> Tuple[bool, Optional[str]]:
        """Verify log retention period."""
        retention = self.config.get_config("security.audit.retention", {})
        
        # PCI DSS requires at least 1 year retention
        retention_days = retention.get("retention_days", 0)
        if retention_days < 365:
            return False, f"Log retention too short: {retention_days} days (min: 365)"
        
        # Check if 3 months are available online
        online_days = retention.get("online_retention_days", 0)
        if online_days < 90:
            return False, f"Online retention too short: {online_days} days (min: 90)"
        
        return True, None
    
    def _verify_vulnerability_scanning(self) -> Tuple[bool, Optional[str]]:
        """Verify vulnerability scanning."""
        vuln_scanning = self.config.get_config("compliance.pci_dss.vulnerability_scanning", {})
        
        if not vuln_scanning.get("quarterly_scans", False):
            return False, "Quarterly vulnerability scans not performed"
        
        # Check last scan date
        last_scan = vuln_scanning.get("last_scan_date")
        if last_scan:
            scan_date = datetime.fromisoformat(last_scan)
            if datetime.now() - scan_date > timedelta(days=90):
                return False, f"Vulnerability scan overdue (last: {last_scan})"
        else:
            return False, "No vulnerability scan performed"
        
        return True, None
    
    def _verify_intrusion_detection(self) -> Tuple[bool, Optional[str]]:
        """Verify intrusion detection systems."""
        ids_config = self.config.get_config("security.intrusion_detection", {})
        
        if not ids_config.get("enabled", False):
            return False, "IDS/IPS not enabled"
        
        if not ids_config.get("monitored_24_7", False):
            return False, "IDS/IPS not monitored 24/7"
        
        return True, None
    
    def _verify_file_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify file integrity monitoring."""
        fim_config = self.config.get_config("security.file_integrity", {})
        
        if not fim_config.get("enabled", False):
            return False, "File integrity monitoring not enabled"
        
        # Check if critical files are monitored
        if not fim_config.get("critical_files_monitored", False):
            return False, "Critical files not monitored"
        
        # Check alert mechanism
        if not fim_config.get("real_time_alerts", False):
            return False, "Real-time alerts not configured"
        
        return True, None
    
    def _verify_risk_assessment(self) -> Tuple[bool, Optional[str]]:
        """Verify risk assessment."""
        risk_assessment = self.config.get_config("compliance.pci_dss.risk_assessment", {})
        
        if not risk_assessment.get("completed", False):
            return False, "Risk assessment not completed"
        
        # Check if assessment is current (annual requirement)
        assessment_date = risk_assessment.get("date")
        if assessment_date:
            date = datetime.fromisoformat(assessment_date)
            if datetime.now() - date > timedelta(days=365):
                return False, f"Risk assessment outdated (date: {assessment_date})"
        else:
            return False, "Risk assessment date not recorded"
        
        return True, None
    
    def _verify_security_awareness(self) -> Tuple[bool, Optional[str]]:
        """Verify security awareness program."""
        awareness = self.config.get_config("compliance.pci_dss.security_awareness", {})
        
        if not awareness.get("program_implemented", False):
            return False, "Security awareness program not implemented"
        
        # Check training frequency (annual requirement)
        if not awareness.get("annual_training", False):
            return False, "Annual security training not performed"
        
        return True, None
    
    def _verify_incident_response(self) -> Tuple[bool, Optional[str]]:
        """Verify incident response plan."""
        incident_response = self.config.get_config("compliance.pci_dss.incident_response", {})
        
        if not incident_response.get("plan_documented", False):
            return False, "Incident response plan not documented"
        
        # Check 24/7 availability
        if not incident_response.get("24_7_available", False):
            return False, "24/7 incident response not available"
        
        # Check if plan has been tested
        last_test = incident_response.get("last_test_date")
        if last_test:
            test_date = datetime.fromisoformat(last_test)
            if datetime.now() - test_date > timedelta(days=365):
                return False, f"Incident response plan test outdated (last: {last_test})"
        else:
            return False, "Incident response plan never tested"
        
        return True, None
    
    def check_password_complexity(self, password: str) -> Tuple[bool, List[str]]:
        """
        Check if password meets PCI DSS complexity requirements.
        
        Args:
            password: The password to check
            
        Returns:
            Tuple of (is_compliant, list of issues)
        """
        issues = []
        
        # Check minimum length (12 characters)
        if len(password) < 12:
            issues.append(f"Password too short: {len(password)} characters (min: 12)")
        
        # Check for uppercase
        if not re.search(r'[A-Z]', password):
            issues.append("Missing uppercase letter")
        
        # Check for lowercase
        if not re.search(r'[a-z]', password):
            issues.append("Missing lowercase letter")
        
        # Check for numbers
        if not re.search(r'[0-9]', password):
            issues.append("Missing number")
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Missing special character")
        
        return len(issues) == 0, issues
    
    def check_password_history(self, user_id: str, password_hash: str) -> bool:
        """
        Check if password was used in the last 4 passwords.
        
        Args:
            user_id: The user ID
            password_hash: Hash of the new password
            
        Returns:
            True if password is acceptable (not in history)
        """
        history = self._password_history.get(user_id, [])
        
        # Check if password was used in last 4
        if password_hash in history[-4:]:
            return False
        
        # Add to history
        history.append(password_hash)
        
        # Keep only last 4
        if len(history) > 4:
            history = history[-4:]
        
        self._password_history[user_id] = history
        return True
    
    def record_failed_login(self, user_id: str) -> Tuple[bool, int]:
        """
        Record a failed login attempt.
        
        Args:
            user_id: The user ID
            
        Returns:
            Tuple of (should_lock, attempt_count)
        """
        now = datetime.now()
        
        # Get or create attempt list
        attempts = self._failed_login_attempts.get(user_id, [])
        
        # Remove old attempts (outside 30 minute window)
        cutoff = now - timedelta(minutes=30)
        attempts = [a for a in attempts if a > cutoff]
        
        # Add new attempt
        attempts.append(now)
        self._failed_login_attempts[user_id] = attempts
        
        # Check if should lock (6 attempts in 30 minutes)
        should_lock = len(attempts) >= 6
        
        # Log the event
        self.audit.audit_compliance_event(
            framework="PCI_DSS",
            event_type="failed_login",
            details={
                "user_id": user_id,
                "attempt_count": len(attempts),
                "locked": should_lock,
            }
        )
        
        return should_lock, len(attempts)
    
    def clear_failed_logins(self, user_id: str) -> None:
        """Clear failed login attempts for a user."""
        if user_id in self._failed_login_attempts:
            del self._failed_login_attempts[user_id]
    
    def log_card_data_access(
        self,
        user_id: str,
        action: str,
        masked_pan: str,
        reason: str
    ) -> None:
        """
        Log access to card data for PCI DSS compliance.
        
        Args:
            user_id: User accessing the data
            action: Action performed (view, modify, delete)
            masked_pan: Masked PAN (e.g., "123456******1234")
            reason: Business reason for access
        """
        access_record = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "masked_pan": masked_pan,
            "reason": reason,
        }
        
        self._card_data_access_log.append(access_record)
        
        # Also log to audit system
        self.audit.audit_compliance_event(
            framework="PCI_DSS",
            event_type="card_data_access",
            details=access_record
        )
    
    def record_vulnerability_scan(
        self,
        scan_type: str,
        scan_date: datetime,
        findings: List[Dict[str, Any]],
        remediated: bool = False
    ) -> None:
        """
        Record vulnerability scan results.
        
        Args:
            scan_type: Type of scan (internal/external)
            scan_date: Date of scan
            findings: List of findings
            remediated: Whether findings were remediated
        """
        scan_record = {
            "scan_type": scan_type,
            "scan_date": scan_date.isoformat(),
            "findings_count": len(findings),
            "critical_count": len([f for f in findings if f.get("severity") == "critical"]),
            "high_count": len([f for f in findings if f.get("severity") == "high"]),
            "remediated": remediated,
        }
        
        self._vulnerability_scans.append(scan_record)
        
        # Update config
        self.config.set_config(
            "compliance.pci_dss.vulnerability_scanning.last_scan_date",
            scan_date.isoformat()
        )
        
        # Log the scan
        self.audit.audit_compliance_event(
            framework="PCI_DSS",
            event_type="vulnerability_scan",
            details=scan_record
        )
    
    def record_key_rotation(self, key_id: str, rotation_date: Optional[datetime] = None) -> None:
        """
        Record cryptographic key rotation.
        
        Args:
            key_id: Identifier for the key
            rotation_date: Date of rotation (defaults to now)
        """
        if rotation_date is None:
            rotation_date = datetime.now()
        
        self._key_rotation_dates[key_id] = rotation_date
        
        # Log the rotation
        self.audit.audit_compliance_event(
            framework="PCI_DSS",
            event_type="key_rotation",
            details={
                "key_id": key_id,
                "rotation_date": rotation_date.isoformat(),
            }
        )
    
    def check_key_rotation_due(self, key_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if a key is due for rotation.
        
        Args:
            key_id: Identifier for the key
            
        Returns:
            Tuple of (is_due, days_overdue)
        """
        if key_id not in self._key_rotation_dates:
            return True, None
        
        last_rotation = self._key_rotation_dates[key_id]
        days_since = (datetime.now() - last_rotation).days
        
        # PCI DSS recommends annual rotation
        if days_since > 365:
            return True, days_since - 365
        
        return False, None
    
    def generate_pci_dss_report(self) -> str:
        """
        Generate a PCI DSS compliance report.
        
        Returns:
            HTML formatted compliance report
        """
        report = self.assess_compliance()
        
        # Add PCI DSS specific sections
        pci_html = f"""
        <div class="section">
            <h2>PCI DSS Compliance Summary</h2>
            
            <h3>Access Control</h3>
            <ul>
                <li>Unique User IDs: {self._check_status('PCI-8.1')}</li>
                <li>Strong Authentication: {self._check_status('PCI-8.2')}</li>
                <li>Password Requirements: {self._check_status('PCI-8.3')}</li>
                <li>Account Lockout: {self._check_status('PCI-8.4')}</li>
                <li>Multi-Factor Authentication: {self._check_status('PCI-8.6')}</li>
            </ul>
            
            <h3>Data Protection</h3>
            <ul>
                <li>Data Retention: {self._check_status('PCI-3.1')}</li>
                <li>PAN Masking: {self._check_status('PCI-3.4')}</li>
                <li>Key Management: {self._check_status('PCI-3.5')}</li>
                <li>Transmission Encryption: {self._check_status('PCI-4.1')}</li>
            </ul>
            
            <h3>Monitoring and Testing</h3>
            <ul>
                <li>Audit Trails: {self._check_status('PCI-10.1')}</li>
                <li>Log Protection: {self._check_status('PCI-10.3')}</li>
                <li>Daily Log Review: {self._check_status('PCI-10.4')}</li>
                <li>Vulnerability Scanning: {self._check_status('PCI-11.2')}</li>
                <li>File Integrity Monitoring: {self._check_status('PCI-11.5')}</li>
            </ul>
            
            <h3>Recent Activity</h3>
            <p>Card data access events: {len(self._card_data_access_log)}</p>
            <p>Failed login attempts tracked: {sum(len(a) for a in self._failed_login_attempts.values())}</p>
            <p>Vulnerability scans performed: {len(self._vulnerability_scans)}</p>
        </div>
        """
        
        # Insert PCI section into base report
        base_html = self.export_report(report, "html")
        return base_html.replace("</body>", pci_html + "</body>")
    
    def _check_status(self, requirement_id: str) -> str:
        """Check and format requirement status."""
        is_compliant, reason = self.verify_requirement(requirement_id)
        if is_compliant:
            return "✓ Compliant"
        else:
            return f"✗ Non-compliant: {reason}"