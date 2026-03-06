"""Incident response template. Extends Diagnostic with escalation and containment."""

from graph import Template, Field
from templates.diagnostic import Diagnostic


class Incident(Diagnostic):
    id = "incident"
    name = "Incident Response"
    description = "Full incident response: triage -> diagnose -> contain -> remediate"

    def define(self, g):
        # Override start to add severity assessment
        g.node("start",
               prompt="Triage the incident.",
               context="Assess the severity and immediate impact of this incident.",
               evidence={
                   "objective": Field("text", required=True,
                                      hint="Brief description of the incident"),
                   "severity": Field("enum", required=True,
                                     values=["low", "medium", "high", "critical"],
                                     hint="How severe is this incident?"),
                   "active_impact": Field("enum", required=True,
                                          values=["yes", "no"],
                                          hint="Is there ongoing impact right now?"),
                   "ready": Field("enum", required=True, values=["yes", "no"]),
               },
               gate="response.get('ready') == 'yes'")

        # Inherited diagnosis steps (observe, hypothesize, test) come from Diagnostic
        self.fill(g, "procedure_body")

        g.node("verify",
               prompt="Verify the resolution.",
               context="Confirm the incident is fully resolved and services are restored.",
               evidence={
                   "all_steps_passed": Field("enum", required=True, values=["yes", "no"]),
                   "services_restored": Field("enum", required=True, values=["yes", "no"]),
                   "verification_notes": Field("text", required=False),
               },
               gate="response.get('all_steps_passed') == 'yes' and response.get('services_restored') == 'yes'")

        g.node("close",
               prompt="Close the incident.",
               evidence={
                   "outcome": Field("enum", required=True, values=["resolved", "mitigated", "unresolved"]),
                   "summary": Field("text", required=True),
                   "follow_up_needed": Field("enum", required=True, values=["yes", "no"],
                                             hint="Are follow-up actions needed?"),
               },
               terminal=True)

    def define_post_diagnosis(self, g):
        """Add containment and remediation after diagnosis."""
        g.node("contain",
               prompt="Contain the incident.",
               context="Take immediate action to stop ongoing damage or impact.",
               evidence={
                   "containment_action": Field("text", required=True,
                                               hint="What containment action was taken?"),
                   "impact_stopped": Field("enum", required=True, values=["yes", "no", "partial"]),
               })

        g.node("remediate",
               prompt="Remediate the root cause.",
               context="Apply a fix for the root cause identified during diagnosis.",
               evidence={
                   "fix_description": Field("text", required=True,
                                            hint="What fix was applied?"),
                   "fix_verified": Field("enum", required=True, values=["yes", "no"]),
                   "rollback_plan": Field("text", required=False,
                                          hint="How to roll back if the fix fails?"),
               })
