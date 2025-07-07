"""
GDPR compliance implementation for Secrets Password Manager.

This module implements the General Data Protection Regulation (GDPR)
compliance requirements for privacy and data protection.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...security import AuditLogger, EncryptedConfigManager
from ..compliance_manager import (
    ComplianceFramework,
    ComplianceManager,
    ComplianceRequirement,
    RequirementCategory,
)


class ProcessingLawfulBasis(Enum):
    """GDPR lawful basis for processing personal data."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class ConsentStatus(Enum):
    """Status of user consent."""
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    NOT_GIVEN = "not_given"
    EXPIRED = "expired"


class DataCategory(Enum):
    """Categories of personal data."""
    BASIC_IDENTITY = "basic_identity"  # Name, email
    AUTHENTICATION = "authentication"  # Passwords, keys
    USAGE_DATA = "usage_data"  # Access logs, preferences
    TECHNICAL_DATA = "technical_data"  # IP addresses, device info
    SPECIAL_CATEGORY = "special_category"  # Health, biometric data


class GDPRComplianceManager(ComplianceManager):
    """
    GDPR compliance manager implementation.
    
    Implements GDPR requirements including:
    - Privacy by Design and Default (Article 25)
    - Individual Rights (Articles 15-22)
    - Consent Management (Article 7)
    - Data Protection Impact Assessment (Article 35)
    - Breach Notification (Article 33-34)
    - Data Protection Officer (Article 37-39)
    """
    
    def __init__(
        self,
        config_manager: EncryptedConfigManager,
        audit_logger: AuditLogger,
    ):
        """Initialize GDPR compliance manager."""
        super().__init__(ComplianceFramework.GDPR, config_manager, audit_logger)
        self.logger = logging.getLogger(__name__)
        
        # GDPR specific tracking
        self._consent_records: Dict[str, Dict[str, Any]] = {}
        self._data_requests: List[Dict[str, Any]] = []
        self._data_breaches: List[Dict[str, Any]] = []
        self._processing_activities: List[Dict[str, Any]] = []
        self._data_retention_policies: Dict[str, Dict[str, Any]] = {}
    
    def _initialize_requirements(self) -> None:
        """Initialize GDPR compliance requirements."""
        # Principles of Processing (Article 5)
        self._add_processing_principles()
        
        # Lawful Basis (Article 6)
        self._add_lawful_basis_requirements()
        
        # Consent (Article 7)
        self._add_consent_requirements()
        
        # Individual Rights (Articles 15-22)
        self._add_individual_rights_requirements()
        
        # Privacy by Design (Article 25)
        self._add_privacy_by_design_requirements()
        
        # Security of Processing (Article 32)
        self._add_security_requirements()
        
        # Breach Notification (Articles 33-34)
        self._add_breach_notification_requirements()
        
        # DPO Requirements (Articles 37-39)
        self._add_dpo_requirements()
        
        # International Transfers (Chapter V)
        self._add_transfer_requirements()
        
        # Records of Processing (Article 30)
        self._add_records_requirements()
    
    def _add_processing_principles(self) -> None:
        """Add Article 5 - Principles of Processing requirements."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-P-1",
            name="Lawfulness, Fairness, and Transparency",
            description="Process personal data lawfully, fairly, and transparently",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 5(1)(a)",
            verification_method="Check lawful basis documentation",
            automated=True,
            controls=["lawful_basis_documented", "privacy_notice"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-P-2",
            name="Purpose Limitation",
            description="Process data for specified, explicit, and legitimate purposes only",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 5(1)(b)",
            verification_method="Check purpose specification",
            automated=True,
            controls=["purpose_specification", "compatible_use"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-P-3",
            name="Data Minimisation",
            description="Process adequate, relevant, and limited data",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 5(1)(c)",
            verification_method="Check data minimisation controls",
            automated=True,
            controls=["data_minimisation", "necessity_assessment"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-P-4",
            name="Accuracy",
            description="Ensure data is accurate and kept up to date",
            category=RequirementCategory.DATA_PROTECTION,
            priority=2,
            framework=ComplianceFramework.GDPR,
            reference="Article 5(1)(d)",
            verification_method="Check data accuracy procedures",
            automated=True,
            controls=["accuracy_verification", "update_procedures"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-P-5",
            name="Storage Limitation",
            description="Keep data only as long as necessary",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 5(1)(e)",
            verification_method="Check retention policies",
            automated=True,
            controls=["retention_policies", "automatic_deletion"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-P-6",
            name="Security Principle",
            description="Process data securely with appropriate technical and organisational measures",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 5(1)(f)",
            verification_method="Check security measures",
            automated=True,
            controls=["encryption", "access_controls", "security_measures"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-P-7",
            name="Accountability",
            description="Demonstrate compliance with GDPR principles",
            category=RequirementCategory.DOCUMENTATION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 5(2)",
            verification_method="Check accountability measures",
            automated=True,
            controls=["compliance_documentation", "accountability_measures"],
        ))
    
    def _add_lawful_basis_requirements(self) -> None:
        """Add Article 6 - Lawful Basis requirements."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-LB-1",
            name="Lawful Basis Identification",
            description="Identify and document lawful basis for each processing activity",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 6(1)",
            verification_method="Check lawful basis documentation",
            automated=True,
            controls=["lawful_basis_mapping", "processing_register"],
        ))
    
    def _add_consent_requirements(self) -> None:
        """Add Article 7 - Consent requirements."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-C-1",
            name="Valid Consent",
            description="Obtain valid consent that is freely given, specific, informed, and unambiguous",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 7(1)",
            verification_method="Check consent mechanism",
            automated=True,
            controls=["consent_mechanism", "consent_records"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-C-2",
            name="Consent Withdrawal",
            description="Make it as easy to withdraw consent as to give it",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 7(3)",
            verification_method="Check withdrawal mechanism",
            automated=True,
            controls=["withdrawal_mechanism", "consent_management"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-C-3",
            name="Child Consent",
            description="Obtain parental consent for children under 16",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 8",
            verification_method="Check age verification",
            automated=True,
            controls=["age_verification", "parental_consent"],
        ))
    
    def _add_individual_rights_requirements(self) -> None:
        """Add Individual Rights requirements (Articles 15-22)."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-R-1",
            name="Right of Access",
            description="Provide individuals access to their personal data",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 15",
            verification_method="Check access request handling",
            automated=True,
            controls=["access_request_process", "data_export"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-R-2",
            name="Right to Rectification",
            description="Allow individuals to correct inaccurate personal data",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 16",
            verification_method="Check rectification process",
            automated=True,
            controls=["data_correction", "rectification_process"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-R-3",
            name="Right to Erasure",
            description="Allow individuals to request deletion of their data",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 17",
            verification_method="Check erasure process",
            automated=True,
            controls=["data_deletion", "erasure_process", "right_to_be_forgotten"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-R-4",
            name="Right to Restrict Processing",
            description="Allow individuals to restrict processing of their data",
            category=RequirementCategory.DATA_PROTECTION,
            priority=2,
            framework=ComplianceFramework.GDPR,
            reference="Article 18",
            verification_method="Check restriction mechanism",
            automated=True,
            controls=["processing_restriction", "restriction_controls"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-R-5",
            name="Right to Data Portability",
            description="Provide data in machine-readable format for portability",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 20",
            verification_method="Check portability implementation",
            automated=True,
            controls=["data_portability", "structured_format"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-R-6",
            name="Right to Object",
            description="Allow individuals to object to processing",
            category=RequirementCategory.DATA_PROTECTION,
            priority=2,
            framework=ComplianceFramework.GDPR,
            reference="Article 21",
            verification_method="Check objection handling",
            automated=True,
            controls=["objection_process", "opt_out"],
        ))
    
    def _add_privacy_by_design_requirements(self) -> None:
        """Add Article 25 - Privacy by Design requirements."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-PBD-1",
            name="Data Protection by Design",
            description="Implement data protection measures at design stage",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 25(1)",
            verification_method="Check design measures",
            automated=True,
            controls=["privacy_by_design", "design_controls"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-PBD-2",
            name="Data Protection by Default",
            description="Ensure only necessary data is processed by default",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 25(2)",
            verification_method="Check default settings",
            automated=True,
            controls=["privacy_by_default", "default_settings"],
        ))
    
    def _add_security_requirements(self) -> None:
        """Add Article 32 - Security of Processing requirements."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-S-1",
            name="Appropriate Security Measures",
            description="Implement appropriate technical and organisational security measures",
            category=RequirementCategory.TECHNICAL,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 32(1)",
            verification_method="Check security implementation",
            automated=True,
            controls=["encryption", "pseudonymisation", "confidentiality", "integrity"],
        ))
    
    def _add_breach_notification_requirements(self) -> None:
        """Add Breach Notification requirements (Articles 33-34)."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-BN-1",
            name="Breach Notification to Authority",
            description="Notify supervisory authority of breaches within 72 hours",
            category=RequirementCategory.INCIDENT_RESPONSE,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 33",
            verification_method="Check breach notification process",
            automated=True,
            controls=["breach_detection", "72_hour_notification"],
        ))
        
        self.add_requirement(ComplianceRequirement(
            id="GDPR-BN-2",
            name="Breach Notification to Data Subjects",
            description="Notify data subjects of high-risk breaches without undue delay",
            category=RequirementCategory.INCIDENT_RESPONSE,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 34",
            verification_method="Check subject notification process",
            automated=True,
            controls=["high_risk_assessment", "subject_notification"],
        ))
    
    def _add_dpo_requirements(self) -> None:
        """Add DPO requirements (Articles 37-39)."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-DPO-1",
            name="Data Protection Officer Designation",
            description="Designate DPO where required and ensure proper position",
            category=RequirementCategory.ORGANIZATIONAL,
            priority=2,
            framework=ComplianceFramework.GDPR,
            reference="Article 37-39",
            verification_method="Check DPO designation",
            automated=True,
            controls=["dpo_designation", "dpo_independence"],
        ))
    
    def _add_transfer_requirements(self) -> None:
        """Add International Transfer requirements (Chapter V)."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-T-1",
            name="International Data Transfers",
            description="Ensure appropriate safeguards for international transfers",
            category=RequirementCategory.DATA_PROTECTION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Articles 44-49",
            verification_method="Check transfer mechanisms",
            automated=True,
            controls=["adequacy_decisions", "appropriate_safeguards"],
        ))
    
    def _add_records_requirements(self) -> None:
        """Add Records of Processing requirements (Article 30)."""
        self.add_requirement(ComplianceRequirement(
            id="GDPR-ROP-1",
            name="Records of Processing Activities",
            description="Maintain records of all processing activities",
            category=RequirementCategory.DOCUMENTATION,
            priority=1,
            framework=ComplianceFramework.GDPR,
            reference="Article 30",
            verification_method="Check processing records",
            automated=True,
            controls=["processing_register", "activity_records"],
        ))
    
    def verify_requirement(
        self, requirement_id: str, evidence: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify if a specific GDPR requirement is met.
        
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
            # Processing Principles
            "GDPR-P-1": self._verify_lawfulness_transparency,
            "GDPR-P-2": self._verify_purpose_limitation,
            "GDPR-P-3": self._verify_data_minimisation,
            "GDPR-P-4": self._verify_accuracy,
            "GDPR-P-5": self._verify_storage_limitation,
            "GDPR-P-6": self._verify_security_principle,
            "GDPR-P-7": self._verify_accountability,
            
            # Lawful Basis
            "GDPR-LB-1": self._verify_lawful_basis,
            
            # Consent
            "GDPR-C-1": self._verify_valid_consent,
            "GDPR-C-2": self._verify_consent_withdrawal,
            "GDPR-C-3": self._verify_child_consent,
            
            # Individual Rights
            "GDPR-R-1": self._verify_right_of_access,
            "GDPR-R-2": self._verify_right_to_rectification,
            "GDPR-R-3": self._verify_right_to_erasure,
            "GDPR-R-4": self._verify_right_to_restrict,
            "GDPR-R-5": self._verify_right_to_portability,
            "GDPR-R-6": self._verify_right_to_object,
            
            # Privacy by Design
            "GDPR-PBD-1": self._verify_privacy_by_design,
            "GDPR-PBD-2": self._verify_privacy_by_default,
            
            # Security
            "GDPR-S-1": self._verify_security_measures,
            
            # Breach Notification
            "GDPR-BN-1": self._verify_breach_notification_authority,
            "GDPR-BN-2": self._verify_breach_notification_subjects,
            
            # DPO
            "GDPR-DPO-1": self._verify_dpo_designation,
            
            # Transfers
            "GDPR-T-1": self._verify_international_transfers,
            
            # Records
            "GDPR-ROP-1": self._verify_processing_records,
        }
        
        verify_method = verification_methods.get(requirement_id)
        if verify_method:
            return verify_method()
        
        # For non-automated requirements, check if manually marked as implemented
        if not requirement.automated and requirement.implemented:
            return True, None
        
        return False, "Requirement not implemented or verified"
    
    def _verify_lawfulness_transparency(self) -> Tuple[bool, Optional[str]]:
        """Verify lawfulness, fairness, and transparency."""
        privacy_config = self.config.get_config("compliance.gdpr.privacy", {})
        
        if not privacy_config.get("privacy_notice_provided", False):
            return False, "Privacy notice not provided"
        
        # Check if lawful basis is documented for all processing
        if not privacy_config.get("lawful_basis_documented", False):
            return False, "Lawful basis not documented"
        
        return True, None
    
    def _verify_purpose_limitation(self) -> Tuple[bool, Optional[str]]:
        """Verify purpose limitation compliance."""
        purpose_config = self.config.get_config("compliance.gdpr.purpose_limitation", {})
        
        if not purpose_config.get("purposes_specified", False):
            return False, "Processing purposes not specified"
        
        if not purpose_config.get("compatible_use_only", False):
            return False, "Data used for incompatible purposes"
        
        return True, None
    
    def _verify_data_minimisation(self) -> Tuple[bool, Optional[str]]:
        """Verify data minimisation principles."""
        minimisation = self.config.get_config("compliance.gdpr.data_minimisation", {})
        
        if not minimisation.get("necessity_assessment", False):
            return False, "Necessity assessment not performed"
        
        if not minimisation.get("minimal_data_collection", False):
            return False, "Minimal data collection not implemented"
        
        return True, None
    
    def _verify_accuracy(self) -> Tuple[bool, Optional[str]]:
        """Verify data accuracy requirements."""
        accuracy = self.config.get_config("compliance.gdpr.accuracy", {})
        
        if not accuracy.get("accuracy_procedures", False):
            return False, "Data accuracy procedures not implemented"
        
        if not accuracy.get("update_mechanisms", False):
            return False, "Data update mechanisms not available"
        
        return True, None
    
    def _verify_storage_limitation(self) -> Tuple[bool, Optional[str]]:
        """Verify storage limitation compliance."""
        retention = self.config.get_config("compliance.gdpr.retention", {})
        
        if not retention.get("retention_policies_defined", False):
            return False, "Data retention policies not defined"
        
        if not retention.get("automatic_deletion", False):
            return False, "Automatic data deletion not implemented"
        
        return True, None
    
    def _verify_security_principle(self) -> Tuple[bool, Optional[str]]:
        """Verify security principle compliance."""
        security = self.config.get_config("security", {})
        
        if not security.get("encryption", {}).get("enabled", False):
            return False, "Encryption not enabled"
        
        if not security.get("access_controls", {}).get("enabled", False):
            return False, "Access controls not implemented"
        
        return True, None
    
    def _verify_accountability(self) -> Tuple[bool, Optional[str]]:
        """Verify accountability principle."""
        accountability = self.config.get_config("compliance.gdpr.accountability", {})
        
        if not accountability.get("compliance_documentation", False):
            return False, "Compliance documentation not maintained"
        
        if not accountability.get("accountability_measures", False):
            return False, "Accountability measures not implemented"
        
        return True, None
    
    def _verify_lawful_basis(self) -> Tuple[bool, Optional[str]]:
        """Verify lawful basis identification."""
        lawful_basis = self.config.get_config("compliance.gdpr.lawful_basis", {})
        
        if not lawful_basis.get("basis_mapped", False):
            return False, "Lawful basis not mapped to processing activities"
        
        if not lawful_basis.get("processing_register", False):
            return False, "Processing register not maintained"
        
        return True, None
    
    def _verify_valid_consent(self) -> Tuple[bool, Optional[str]]:
        """Verify valid consent mechanism."""
        consent = self.config.get_config("compliance.gdpr.consent", {})
        
        if not consent.get("consent_mechanism", False):
            return False, "Valid consent mechanism not implemented"
        
        if not consent.get("consent_records", False):
            return False, "Consent records not maintained"
        
        # Check if consent is freely given, specific, informed, and unambiguous
        consent_requirements = ["freely_given", "specific", "informed", "unambiguous"]
        for req in consent_requirements:
            if not consent.get(req, False):
                return False, f"Consent not {req.replace('_', ' ')}"
        
        return True, None
    
    def _verify_consent_withdrawal(self) -> Tuple[bool, Optional[str]]:
        """Verify consent withdrawal mechanism."""
        withdrawal = self.config.get_config("compliance.gdpr.consent.withdrawal", {})
        
        if not withdrawal.get("easy_withdrawal", False):
            return False, "Easy consent withdrawal not implemented"
        
        if not withdrawal.get("withdrawal_mechanism", False):
            return False, "Consent withdrawal mechanism not available"
        
        return True, None
    
    def _verify_child_consent(self) -> Tuple[bool, Optional[str]]:
        """Verify child consent handling."""
        child_consent = self.config.get_config("compliance.gdpr.child_consent", {})
        
        if not child_consent.get("age_verification", False):
            return False, "Age verification not implemented"
        
        if not child_consent.get("parental_consent", False):
            return False, "Parental consent mechanism not available"
        
        return True, None
    
    def _verify_right_of_access(self) -> Tuple[bool, Optional[str]]:
        """Verify right of access implementation."""
        access = self.config.get_config("compliance.gdpr.rights.access", {})
        
        if not access.get("access_request_process", False):
            return False, "Access request process not implemented"
        
        if not access.get("data_export_capability", False):
            return False, "Data export capability not available"
        
        return True, None
    
    def _verify_right_to_rectification(self) -> Tuple[bool, Optional[str]]:
        """Verify right to rectification."""
        rectification = self.config.get_config("compliance.gdpr.rights.rectification", {})
        
        if not rectification.get("correction_process", False):
            return False, "Data correction process not implemented"
        
        return True, None
    
    def _verify_right_to_erasure(self) -> Tuple[bool, Optional[str]]:
        """Verify right to erasure (right to be forgotten)."""
        erasure = self.config.get_config("compliance.gdpr.rights.erasure", {})
        
        if not erasure.get("deletion_process", False):
            return False, "Data deletion process not implemented"
        
        if not erasure.get("right_to_be_forgotten", False):
            return False, "Right to be forgotten not implemented"
        
        return True, None
    
    def _verify_right_to_restrict(self) -> Tuple[bool, Optional[str]]:
        """Verify right to restrict processing."""
        restriction = self.config.get_config("compliance.gdpr.rights.restriction", {})
        
        if not restriction.get("restriction_mechanism", False):
            return False, "Processing restriction mechanism not implemented"
        
        return True, None
    
    def _verify_right_to_portability(self) -> Tuple[bool, Optional[str]]:
        """Verify right to data portability."""
        portability = self.config.get_config("compliance.gdpr.rights.portability", {})
        
        if not portability.get("portability_capability", False):
            return False, "Data portability capability not implemented"
        
        if not portability.get("structured_format", False):
            return False, "Structured data format not available"
        
        return True, None
    
    def _verify_right_to_object(self) -> Tuple[bool, Optional[str]]:
        """Verify right to object to processing."""
        objection = self.config.get_config("compliance.gdpr.rights.objection", {})
        
        if not objection.get("objection_process", False):
            return False, "Objection process not implemented"
        
        return True, None
    
    def _verify_privacy_by_design(self) -> Tuple[bool, Optional[str]]:
        """Verify privacy by design implementation."""
        pbd = self.config.get_config("compliance.gdpr.privacy_by_design", {})
        
        if not pbd.get("design_controls", False):
            return False, "Privacy by design controls not implemented"
        
        return True, None
    
    def _verify_privacy_by_default(self) -> Tuple[bool, Optional[str]]:
        """Verify privacy by default implementation."""
        pbd = self.config.get_config("compliance.gdpr.privacy_by_default", {})
        
        if not pbd.get("default_privacy_settings", False):
            return False, "Privacy by default settings not configured"
        
        return True, None
    
    def _verify_security_measures(self) -> Tuple[bool, Optional[str]]:
        """Verify appropriate security measures."""
        security = self.config.get_config("security", {})
        
        # Check required security measures
        required_measures = ["encryption", "access_controls", "integrity_protection"]
        for measure in required_measures:
            if not security.get(measure, {}).get("enabled", False):
                return False, f"Security measure not enabled: {measure}"
        
        return True, None
    
    def _verify_breach_notification_authority(self) -> Tuple[bool, Optional[str]]:
        """Verify breach notification to authority."""
        breach_notification = self.config.get_config("compliance.gdpr.breach_notification", {})
        
        if not breach_notification.get("authority_notification", False):
            return False, "Authority breach notification not configured"
        
        if not breach_notification.get("72_hour_process", False):
            return False, "72-hour notification process not implemented"
        
        return True, None
    
    def _verify_breach_notification_subjects(self) -> Tuple[bool, Optional[str]]:
        """Verify breach notification to data subjects."""
        subject_notification = self.config.get_config("compliance.gdpr.breach_notification.subjects", {})
        
        if not subject_notification.get("high_risk_notification", False):
            return False, "High-risk breach notification to subjects not configured"
        
        return True, None
    
    def _verify_dpo_designation(self) -> Tuple[bool, Optional[str]]:
        """Verify DPO designation when required."""
        dpo = self.config.get_config("compliance.gdpr.dpo", {})
        
        # Check if DPO is required
        if dpo.get("required", False):
            if not dpo.get("designated", False):
                return False, "DPO required but not designated"
            
            if not dpo.get("independent", False):
                return False, "DPO independence not ensured"
        
        return True, None
    
    def _verify_international_transfers(self) -> Tuple[bool, Optional[str]]:
        """Verify international data transfer safeguards."""
        transfers = self.config.get_config("compliance.gdpr.international_transfers", {})
        
        if transfers.get("transfers_occurring", False):
            if not transfers.get("appropriate_safeguards", False):
                return False, "Appropriate safeguards for transfers not in place"
        
        return True, None
    
    def _verify_processing_records(self) -> Tuple[bool, Optional[str]]:
        """Verify records of processing activities."""
        records = self.config.get_config("compliance.gdpr.processing_records", {})
        
        if not records.get("records_maintained", False):
            return False, "Records of processing activities not maintained"
        
        if not records.get("activity_register", False):
            return False, "Processing activity register not available"
        
        return True, None
    
    def record_consent(
        self,
        data_subject_id: str,
        purpose: str,
        lawful_basis: ProcessingLawfulBasis,
        consent_given: bool = True,
        consent_date: Optional[datetime] = None
    ) -> None:
        """
        Record consent for data processing.
        
        Args:
            data_subject_id: ID of the data subject
            purpose: Purpose of data processing
            lawful_basis: Legal basis for processing
            consent_given: Whether consent was given
            consent_date: Date of consent (defaults to now)
        """
        if consent_date is None:
            consent_date = datetime.now()
        
        consent_record = {
            "data_subject_id": data_subject_id,
            "purpose": purpose,
            "lawful_basis": lawful_basis.value,
            "consent_given": consent_given,
            "consent_date": consent_date.isoformat(),
            "status": ConsentStatus.GIVEN.value if consent_given else ConsentStatus.NOT_GIVEN.value,
            "withdrawal_date": None,
        }
        
        if data_subject_id not in self._consent_records:
            self._consent_records[data_subject_id] = {}
        
        self._consent_records[data_subject_id][purpose] = consent_record
        
        # Log the consent
        self.audit.audit_compliance_event(
            framework="GDPR",
            event_type="consent_recorded",
            details=consent_record
        )
    
    def withdraw_consent(
        self,
        data_subject_id: str,
        purpose: str,
        withdrawal_date: Optional[datetime] = None
    ) -> bool:
        """
        Withdraw consent for data processing.
        
        Args:
            data_subject_id: ID of the data subject
            purpose: Purpose to withdraw consent for
            withdrawal_date: Date of withdrawal (defaults to now)
            
        Returns:
            True if consent was withdrawn, False if not found
        """
        if withdrawal_date is None:
            withdrawal_date = datetime.now()
        
        if (data_subject_id in self._consent_records and 
            purpose in self._consent_records[data_subject_id]):
            
            consent_record = self._consent_records[data_subject_id][purpose]
            consent_record["status"] = ConsentStatus.WITHDRAWN.value
            consent_record["withdrawal_date"] = withdrawal_date.isoformat()
            
            # Log the withdrawal
            self.audit.audit_compliance_event(
                framework="GDPR",
                event_type="consent_withdrawn",
                details={
                    "data_subject_id": data_subject_id,
                    "purpose": purpose,
                    "withdrawal_date": withdrawal_date.isoformat(),
                }
            )
            
            return True
        
        return False
    
    def handle_data_request(
        self,
        request_type: str,  # access, rectification, erasure, portability, restriction, objection
        data_subject_id: str,
        request_details: Dict[str, Any],
        request_date: Optional[datetime] = None
    ) -> str:
        """
        Handle a data subject rights request.
        
        Args:
            request_type: Type of request
            data_subject_id: ID of the data subject
            request_details: Details of the request
            request_date: Date of request (defaults to now)
            
        Returns:
            Request ID for tracking
        """
        if request_date is None:
            request_date = datetime.now()
        
        request_id = f"{request_type}_{data_subject_id}_{int(request_date.timestamp())}"
        
        request_record = {
            "request_id": request_id,
            "request_type": request_type,
            "data_subject_id": data_subject_id,
            "request_date": request_date.isoformat(),
            "status": "received",
            "details": request_details,
            "response_due_date": (request_date + timedelta(days=30)).isoformat(),  # GDPR 1 month
            "completed": False,
            "completion_date": None,
        }
        
        self._data_requests.append(request_record)
        
        # Log the request
        self.audit.audit_compliance_event(
            framework="GDPR",
            event_type="data_subject_request",
            details=request_record
        )
        
        return request_id
    
    def complete_data_request(
        self,
        request_id: str,
        completion_date: Optional[datetime] = None,
        response_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark a data subject request as completed.
        
        Args:
            request_id: ID of the request
            completion_date: Date of completion (defaults to now)
            response_details: Details of the response
            
        Returns:
            True if request was found and completed
        """
        if completion_date is None:
            completion_date = datetime.now()
        
        for request in self._data_requests:
            if request["request_id"] == request_id:
                request["status"] = "completed"
                request["completed"] = True
                request["completion_date"] = completion_date.isoformat()
                if response_details:
                    request["response_details"] = response_details
                
                # Log the completion
                self.audit.audit_compliance_event(
                    framework="GDPR",
                    event_type="data_request_completed",
                    details={
                        "request_id": request_id,
                        "completion_date": completion_date.isoformat(),
                        "on_time": completion_date <= datetime.fromisoformat(request["response_due_date"]),
                    }
                )
                
                return True
        
        return False
    
    def report_data_breach(
        self,
        breach_description: str,
        affected_individuals: int,
        data_categories: List[DataCategory],
        breach_date: Optional[datetime] = None,
        high_risk: bool = False
    ) -> str:
        """
        Report a data breach.
        
        Args:
            breach_description: Description of the breach
            affected_individuals: Number of affected individuals
            data_categories: Categories of data involved
            breach_date: Date of breach (defaults to now)
            high_risk: Whether breach is high risk to rights and freedoms
            
        Returns:
            Breach ID for tracking
        """
        if breach_date is None:
            breach_date = datetime.now()
        
        breach_id = f"breach_{int(breach_date.timestamp())}"
        
        breach_record = {
            "breach_id": breach_id,
            "description": breach_description,
            "breach_date": breach_date.isoformat(),
            "discovered_date": datetime.now().isoformat(),
            "affected_individuals": affected_individuals,
            "data_categories": [cat.value for cat in data_categories],
            "high_risk": high_risk,
            "authority_notified": False,
            "authority_notification_date": None,
            "subjects_notified": False,
            "subject_notification_date": None,
            "breach_contained": False,
            "containment_date": None,
        }
        
        self._data_breaches.append(breach_record)
        
        # Check if 72-hour notification is required
        notification_due = breach_date + timedelta(hours=72)
        
        # Log the breach
        self.audit.audit_compliance_event(
            framework="GDPR",
            event_type="data_breach_reported",
            severity="critical" if high_risk else "high",
            details={
                **breach_record,
                "notification_due": notification_due.isoformat(),
            }
        )
        
        return breach_id
    
    def export_personal_data(
        self,
        data_subject_id: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export all personal data for a data subject (Article 15 & 20).
        
        Args:
            data_subject_id: ID of the data subject
            format: Export format (json, csv, xml)
            
        Returns:
            Exported data
        """
        # This would collect data from all systems
        # For now, return consent and request data
        export_data = {
            "data_subject_id": data_subject_id,
            "export_date": datetime.now().isoformat(),
            "consent_records": self._consent_records.get(data_subject_id, {}),
            "data_requests": [
                req for req in self._data_requests
                if req["data_subject_id"] == data_subject_id
            ],
            "processing_activities": [
                activity for activity in self._processing_activities
                if data_subject_id in activity.get("data_subjects", [])
            ],
        }
        
        # Log the export
        self.audit.audit_compliance_event(
            framework="GDPR",
            event_type="data_exported",
            details={
                "data_subject_id": data_subject_id,
                "export_format": format,
                "records_exported": len(export_data["consent_records"]),
            }
        )
        
        return export_data
    
    def delete_personal_data(
        self,
        data_subject_id: str,
        deletion_reason: str = "erasure_request"
    ) -> bool:
        """
        Delete all personal data for a data subject (Article 17).
        
        Args:
            data_subject_id: ID of the data subject
            deletion_reason: Reason for deletion
            
        Returns:
            True if data was deleted
        """
        # Remove consent records
        if data_subject_id in self._consent_records:
            del self._consent_records[data_subject_id]
        
        # Mark data requests as deleted (keep for audit trail)
        for request in self._data_requests:
            if request["data_subject_id"] == data_subject_id:
                request["data_deleted"] = True
                request["deletion_date"] = datetime.now().isoformat()
        
        # Log the deletion
        self.audit.audit_compliance_event(
            framework="GDPR",
            event_type="personal_data_deleted",
            details={
                "data_subject_id": data_subject_id,
                "deletion_reason": deletion_reason,
                "deletion_date": datetime.now().isoformat(),
            }
        )
        
        return True
    
    def generate_gdpr_report(self) -> str:
        """
        Generate a GDPR compliance report.
        
        Returns:
            HTML formatted compliance report
        """
        report = self.assess_compliance()
        
        # Add GDPR-specific sections
        gdpr_html = f"""
        <div class="section">
            <h2>GDPR Compliance Summary</h2>
            
            <h3>Data Protection Principles</h3>
            <ul>
                <li>Lawfulness & Transparency: {self._check_status('GDPR-P-1')}</li>
                <li>Purpose Limitation: {self._check_status('GDPR-P-2')}</li>
                <li>Data Minimisation: {self._check_status('GDPR-P-3')}</li>
                <li>Accuracy: {self._check_status('GDPR-P-4')}</li>
                <li>Storage Limitation: {self._check_status('GDPR-P-5')}</li>
                <li>Security: {self._check_status('GDPR-P-6')}</li>
                <li>Accountability: {self._check_status('GDPR-P-7')}</li>
            </ul>
            
            <h3>Individual Rights</h3>
            <ul>
                <li>Right of Access: {self._check_status('GDPR-R-1')}</li>
                <li>Right to Rectification: {self._check_status('GDPR-R-2')}</li>
                <li>Right to Erasure: {self._check_status('GDPR-R-3')}</li>
                <li>Right to Data Portability: {self._check_status('GDPR-R-5')}</li>
            </ul>
            
            <h3>Privacy by Design</h3>
            <ul>
                <li>Data Protection by Design: {self._check_status('GDPR-PBD-1')}</li>
                <li>Data Protection by Default: {self._check_status('GDPR-PBD-2')}</li>
            </ul>
            
            <h3>Current Statistics</h3>
            <p>Active consent records: {sum(len(consents) for consents in self._consent_records.values())}</p>
            <p>Pending data requests: {len([r for r in self._data_requests if not r['completed']])}</p>
            <p>Data breaches reported: {len(self._data_breaches)}</p>
            <p>Processing activities documented: {len(self._processing_activities)}</p>
        </div>
        """
        
        # Insert GDPR section into base report
        base_html = self.export_report(report, "html")
        return base_html.replace("</body>", gdpr_html + "</body>")
    
    def _check_status(self, requirement_id: str) -> str:
        """Check and format requirement status."""
        is_compliant, reason = self.verify_requirement(requirement_id)
        if is_compliant:
            return "✓ Compliant"
        else:
            return f"✗ Non-compliant: {reason}"