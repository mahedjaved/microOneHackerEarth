"""Tests for CURA-Med EAV controller module."""

import pytest
import uuid
from server.modules.eav.controller import EAVController
from server.schemas import (
    EvidenceFeatureVector,
    LocalEntailment,
    RetrievalQuality,
    Conflict,
    Provenance,
    QueryAmbiguity,
    SystemState,
    Verdict,
    EAVActionType,
)


class TestEAVController:
    def setup_method(self):
        self.controller = EAVController(action_budget=1)

    def test_no_action_for_singleton_supported(self):
        feature_vector = self._make_feature_vector()
        action = self.controller.decide(feature_vector, [Verdict.SUPPORTED])
        assert action is None

    def test_clarify_for_missing_entities(self):
        feature_vector = self._make_feature_vector(query_ambiguity=QueryAmbiguity(missing_entities=True))
        action = self.controller.decide(feature_vector, [Verdict.SUPPORTED, Verdict.INSUFFICIENT])
        assert action == EAVActionType.CLARIFY

    def test_clarify_for_underspecified_scope(self):
        feature_vector = self._make_feature_vector(query_ambiguity=QueryAmbiguity(underspecified_scope=True))
        action = self.controller.decide(feature_vector, [Verdict.SUPPORTED, Verdict.INSUFFICIENT])
        assert action == EAVActionType.CLARIFY

    def test_retrieve_for_low_top_score(self):
        feature_vector = self._make_feature_vector(retrieval_quality=RetrievalQuality(top_score=0.3))
        action = self.controller.decide(feature_vector, [Verdict.SUPPORTED, Verdict.INSUFFICIENT])
        assert action == EAVActionType.RETRIEVE

    def test_retrieve_for_low_claim_coverage(self):
        feature_vector = self._make_feature_vector(claim_coverage=0.2)
        action = self.controller.decide(feature_vector, [Verdict.SUPPORTED, Verdict.INSUFFICIENT])
        assert action == EAVActionType.RETRIEVE

    def test_retrieve_for_conflict(self):
        feature_vector = self._make_feature_vector(conflict=Conflict(support_refute_coexist=True))
        action = self.controller.decide(feature_vector, [Verdict.SUPPORTED, Verdict.INSUFFICIENT])
        assert action == EAVActionType.RETRIEVE

    def test_no_action_when_budget_exhausted(self):
        controller = EAVController(action_budget=0)
        feature_vector = self._make_feature_vector(retrieval_quality=RetrievalQuality(top_score=0.3))
        action = controller.decide(feature_vector, [Verdict.SUPPORTED, Verdict.INSUFFICIENT])
        assert action is None

    def test_record_action(self):
        action = self.controller.record_action(
            action_type=EAVActionType.CLARIFY,
            pre_set=[Verdict.SUPPORTED, Verdict.INSUFFICIENT],
            post_set=[Verdict.SUPPORTED],
        )
        assert action.action_type == EAVActionType.CLARIFY
        assert action.productive is True
        assert self.controller.actions_used == 1

    def test_record_action_not_productive(self):
        action = self.controller.record_action(
            action_type=EAVActionType.RETRIEVE,
            pre_set=[Verdict.SUPPORTED, Verdict.INSUFFICIENT],
            post_set=[Verdict.SUPPORTED, Verdict.INSUFFICIENT],
        )
        assert action.productive is False

    def test_reset_budget(self):
        self.controller.actions_used = 1
        self.controller.reset()
        assert self.controller.actions_used == 0

    def _make_feature_vector(
        self,
        local_entailment=None,
        claim_coverage=0.8,
        retrieval_quality=None,
        conflict=None,
        provenance=None,
        query_ambiguity=None,
        system_state=None,
    ):
        return EvidenceFeatureVector(
            claim_id=uuid.uuid4(),
            local_entailment=local_entailment or LocalEntailment(),
            claim_coverage=claim_coverage,
            retrieval_quality=retrieval_quality or RetrievalQuality(),
            conflict=conflict or Conflict(),
            provenance=provenance or Provenance(),
            query_ambiguity=query_ambiguity or QueryAmbiguity(),
            system_state=system_state or SystemState(),
        )
