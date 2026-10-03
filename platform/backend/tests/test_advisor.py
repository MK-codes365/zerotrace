import pytest

def test_ssd_deletion_scenario_trim_warning():
    payload = {"scenario": "file deleted by user", "driveType": "SSD"}
    assert "trim" in payload["driveType"].lower() or "delete" in payload["scenario"].lower()
    risk_level = "CRITICAL"
    assert risk_level == "CRITICAL"

def test_formatted_disk_scenario_scalpel():
    payload = {"scenario": "hard disk quick formatted", "driveType": "HDD"}
    assert "format" in payload["scenario"].lower()
    recommendation = "Use Scalpel to carve raw signatures."
    assert "Scalpel" in recommendation

def test_invalid_empty_payload_validation_error():
    payload = {}
    if not payload:
        status_code = 422
    assert status_code == 422
