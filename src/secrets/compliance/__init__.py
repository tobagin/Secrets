"""
Compliance module for Secrets Password Manager.

This module provides compliance functionality for HIPAA, PCI DSS, and GDPR regulations.
"""

from .compliance_manager import ComplianceManager, ComplianceFramework, ComplianceStatus
from .hipaa import HIPAAComplianceManager
from .pci_dss import PCIDSSComplianceManager
from .gdpr import GDPRComplianceManager

__all__ = [
    "ComplianceManager",
    "ComplianceFramework",
    "ComplianceStatus",
    "HIPAAComplianceManager",
    "PCIDSSComplianceManager",
    "GDPRComplianceManager",
]