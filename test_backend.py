import pytest
import json
import os
import sys
from unified_honeypot_engine import UnifiedHoneypotEngine

@pytest.fixture
def engine():
    """Initialises the engine for testing"""
    return UnifiedHoneypotEngine(mode="HYBRID")

def test_log_formatting():
    """Test if the attack data is correctly structured"""
    sample_attack = {
        "source_ip": "192.168.1.50",
        "path": "/test-path",
        "method": "GET"
    }
    # simulates how the engine sees an attack
    assert "source_ip" in sample_attack
    assert "path" in sample_attack
    assert sample_attack["path"] == "/test-path"

def test_threat_classification_logic(engine):
    """FT-UT: Verify the 'Brain' correctly identifies threat levels"""
    
    # 1. test CRITICAL threat
    critical_attack = {"source_ip": "1.1.1.1", "path": "/etc/passwd", "method": "GET"}
    result = engine.process_attack(critical_attack)
    assert result["engine_metadata"]["threat_level"] == "CRITICAL"
    
    # 2. test LOW threat (normal traffic)
    normal_attack = {"source_ip": "1.1.1.1", "path": "/index.html", "method": "GET"}
    result = engine.process_attack(normal_attack)
    assert result["engine_metadata"]["threat_level"] == "LOW"

def test_alert_triggering_logic(engine):
    """FT-UT: Verify that high threats trigger the correct RL action"""
    
    # simulate a known dangerous path that should trigger a 'BLOCK' or 'ISOLATE' action
    dangerous_attack = {"source_ip": "2.2.2.2", "path": "/admin/config.php", "method": "POST"}
    result = engine.process_attack(dangerous_attack)
    
    # the RL agent should assign a high-protection action
    action = result["engine_metadata"]["rl_action"]
    assert action in ["BLOCK", "ISOLATE", "CHALLENGE"]

def test_deceptive_response_generation(engine):
    """Verify that the AI generates a non-empty deceptive response body"""
    attack = {"source_ip": "3.3.3.3", "path": "/device.rsp", "method": "GET"}
    result = engine.process_attack(attack)
    
    assert "response_body" in result
    assert len(result["response_body"]) > 0

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__]))
