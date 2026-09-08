from .regression_compatibility import CompatibilityStatus, compare_schema

def test_supported(): assert compare_schema('1.0','1.0') is CompatibilityStatus.SUPPORTED

def test_migratable(): assert compare_schema('1.0','1.1') is CompatibilityStatus.MIGRATABLE

def test_incompatible(): assert compare_schema('1.0','2.0') is CompatibilityStatus.INCOMPATIBLE
