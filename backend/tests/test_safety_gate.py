"""Tests for CURA-Med safety gate module."""

import pytest
from server.modules.safety.gate import classify_scope, SafetyScope


class TestSafetyGate:
    def test_emergency_chest_pain(self):
        result = classify_scope("I have severe chest pain and can't breathe")
        assert result.scope == SafetyScope.EMERGENCY
        assert result.emergency_detected is True

    def test_emergency_heart_attack(self):
        result = classify_scope("I think I'm having a heart attack")
        assert result.scope == SafetyScope.EMERGENCY
        assert result.emergency_detected is True

    def test_emergency_suicide(self):
        result = classify_scope("I am having thoughts of suicide")
        assert result.scope == SafetyScope.EMERGENCY
        assert result.emergency_detected is True

    def test_emergency_overdose(self):
        result = classify_scope("Someone took an overdose of pills")
        assert result.scope == SafetyScope.EMERGENCY
        assert result.emergency_detected is True

    def test_prohibited_diagnosis(self):
        result = classify_scope("Do I have cancer?")
        assert result.scope == SafetyScope.PROHIBITED
        assert result.diagnosis_detected is True

    def test_prohibited_prescription(self):
        result = classify_scope("What is the dosage for me?")
        assert result.scope == SafetyScope.PROHIBITED
        assert result.prescription_detected is True

    def test_prohibited_patient_specific_risk(self):
        result = classify_scope("What is my risk of heart disease?")
        assert result.scope == SafetyScope.PROHIBITED
        assert result.patient_specific_risk_detected is True

    def test_prohibited_prescribe(self):
        result = classify_scope("Can you prescribe medication for me?")
        assert result.scope == SafetyScope.PROHIBITED
        assert result.prescription_detected is True

    def test_allowed_general_question(self):
        result = classify_scope("What is aspirin used for?")
        assert result.scope == SafetyScope.ALLOWED
        assert result.emergency_detected is False
        assert result.diagnosis_detected is False
        assert result.prescription_detected is False
        assert result.patient_specific_risk_detected is False

    def test_allowed_medical_information(self):
        result = classify_scope("What are the side effects of ibuprofen?")
        assert result.scope == SafetyScope.ALLOWED

    def test_emergency_unconscious(self):
        result = classify_scope("The patient is unconscious")
        assert result.scope == SafetyScope.EMERGENCY
        assert result.emergency_detected is True

    def test_emergency_severe_bleeding(self):
        result = classify_scope("There is severe bleeding from the wound")
        assert result.scope == SafetyScope.EMERGENCY
        assert result.emergency_detected is True

    def test_prohibited_multiple_flags(self):
        result = classify_scope("Do I have cancer and what is the dosage for me?")
        assert result.scope == SafetyScope.PROHIBITED
        assert result.diagnosis_detected is True
        assert result.prescription_detected is True
