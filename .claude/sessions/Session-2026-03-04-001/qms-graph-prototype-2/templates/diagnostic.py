"""Diagnostic procedure template. Extends ProcedureBase with diagnosis steps."""

from graph import Template, Field
from templates.procedure_base import ProcedureBase


class Diagnostic(ProcedureBase):
    id = "diagnostic"
    name = "Diagnostic Procedure"
    description = "Systematic diagnosis: observe -> hypothesize -> test -> conclude"

    def define_procedure_body(self, g):
        g.node("observe",
               prompt="Observe and document the symptoms.",
               context="Gather all observable facts about the problem. Do not jump to conclusions.",
               evidence={
                   "symptoms": Field("text", required=True,
                                     hint="What symptoms are present?"),
                   "onset": Field("text", required=True,
                                  hint="When did the problem start?"),
                   "affected_systems": Field("text", required=False,
                                             hint="What systems or components are affected?"),
               })

        g.node("hypothesize",
               prompt="Form a hypothesis about the root cause.",
               context="Based on your observations, what do you think is causing the problem?",
               evidence={
                   "hypothesis": Field("text", required=True,
                                       hint="Your best explanation for the observed symptoms"),
                   "confidence": Field("enum", required=True,
                                       values=["low", "medium", "high"]),
                   "alternative_hypotheses": Field("text", required=False,
                                                   hint="Other possible explanations"),
               })

        g.node("test",
               prompt="Test your hypothesis.",
               context="Design and execute a test that would confirm or refute your hypothesis.",
               evidence={
                   "test_description": Field("text", required=True,
                                             hint="What test did you perform?"),
                   "test_result": Field("text", required=True,
                                        hint="What was the result?"),
                   "hypothesis_confirmed": Field("enum", required=True,
                                                 values=["yes", "no", "inconclusive"]),
               },
               retry={"when": "response.get('hypothesis_confirmed') != 'yes'",
                      "nodes": ["hypothesize", "test"]})

        # Extension point: subclasses can add steps after testing
        self.fill(g, "post_diagnosis")

        g.node("conclude",
               prompt="State your conclusion.",
               context="Based on all evidence gathered, what is the root cause?",
               evidence={
                   "root_cause": Field("text", required=True,
                                       hint="The identified root cause"),
                   "evidence_summary": Field("text", required=True,
                                             hint="Summary of supporting evidence"),
                   "recommended_action": Field("text", required=True,
                                               hint="What should be done next?"),
               })
