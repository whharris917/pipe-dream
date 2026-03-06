"""Safety incident template. Extends Incident with safety-specific triage,
regulatory reporting, and lessons learned."""

from graph import Template, Field
from templates.incident import Incident


class SafetyIncident(Incident):
    id = "safety-incident"
    name = "Safety Incident Response"
    description = ("Full safety incident response: safety triage -> diagnose -> "
                   "contain -> remediate -> regulatory report -> lessons learned")

    def define(self, g):
        # Override start with safety-specific triage fields
        g.node("start",
               prompt="Triage the safety incident.",
               context=("Assess the severity, immediate danger, and nature of the "
                        "safety incident. If there is immediate danger to personnel, "
                        "prioritize evacuation and first aid before proceeding."),
               evidence={
                   "objective": Field("text", required=True,
                                      hint="Brief description of the safety incident"),
                   "severity": Field("enum", required=True,
                                     values=["low", "medium", "high", "critical"],
                                     hint="How severe is this safety incident?"),
                   "injury_type": Field("enum", required=True,
                                        values=["none", "first_aid", "medical_treatment",
                                                "lost_time", "fatality"],
                                        hint="Classification of any injuries"),
                   "hazard_classification": Field("enum", required=True,
                                                  values=["biological", "chemical",
                                                          "electrical", "ergonomic",
                                                          "mechanical", "thermal",
                                                          "radiation", "other"],
                                                  hint="Type of hazard involved"),
                   "immediate_danger": Field("enum", required=True,
                                             values=["yes", "no"],
                                             hint="Is there immediate danger to personnel?"),
                   "active_impact": Field("enum", required=True,
                                          values=["yes", "no"],
                                          hint="Is there ongoing impact right now?"),
                   "area_secured": Field("enum", required=True,
                                         values=["yes", "no", "not_applicable"],
                                         hint="Has the affected area been secured?"),
                   "ready": Field("enum", required=True, values=["yes", "no"]),
               })

        # Inherited diagnosis steps (observe, hypothesize, test) + post_diagnosis
        # come from Diagnostic via fill dispatch
        self.fill(g, "procedure_body")

        g.node("verify",
               prompt="Verify the safety incident resolution.",
               context=("Confirm the incident is fully resolved, the area is safe, "
                        "and all affected personnel have received appropriate care."),
               evidence={
                   "all_steps_passed": Field("enum", required=True, values=["yes", "no"]),
                   "services_restored": Field("enum", required=True, values=["yes", "no"]),
                   "area_safe": Field("enum", required=True, values=["yes", "no"],
                                      hint="Is the affected area safe to re-enter?"),
                   "personnel_cleared": Field("enum", required=True, values=["yes", "no"],
                                              hint="Have all affected personnel been cleared?"),
                   "verification_notes": Field("text", required=False),
               })

        g.node("close",
               prompt="Close the safety incident.",
               evidence={
                   "outcome": Field("enum", required=True,
                                    values=["resolved", "mitigated", "unresolved"]),
                   "summary": Field("text", required=True),
                   "follow_up_needed": Field("enum", required=True, values=["yes", "no"],
                                             hint="Are follow-up actions needed?"),
                   "preventive_actions_identified": Field("enum", required=True,
                                                         values=["yes", "no"],
                                                         hint="Have preventive actions been identified?"),
               },
               terminal=True)

    def define_post_diagnosis(self, g):
        """Extend Incident's post-diagnosis with safety-specific steps.

        Chain: contain -> remediate -> (post_remediation fill) ->
               regulatory_report -> lessons_learned
        """
        # Inherit contain and remediate from Incident
        super().define_post_diagnosis(g)

        # Extension point for further subclasses
        self.fill(g, "post_remediation")

        # Safety-specific: regulatory reporting
        g.node("regulatory_report",
               prompt="Complete the regulatory report.",
               context=("Determine if this incident is reportable under applicable "
                        "regulations (e.g., OSHA, EPA, local authorities). Complete "
                        "and file all required reports within mandatory timeframes."),
               evidence={
                   "reportable": Field("enum", required=True,
                                       values=["yes", "no", "under_review"],
                                       hint="Is this incident reportable to regulators?"),
                   "regulatory_body": Field("text", required=False,
                                            hint="Which regulatory body, if applicable?"),
                   "report_filed": Field("enum", required=False,
                                         values=["yes", "no", "not_required"],
                                         hint="Has the report been filed?"),
                   "report_reference": Field("text", required=False,
                                             hint="Report reference number, if filed"),
                   "filing_deadline": Field("text", required=False,
                                            hint="Deadline for filing, if applicable"),
               })

        # Safety-specific: lessons learned
        g.node("lessons_learned",
               prompt="Document lessons learned from this safety incident.",
               context=("Capture what went wrong, what went right, and what changes "
                        "should be made to prevent recurrence. This feeds into the "
                        "organization's continuous improvement process."),
               evidence={
                   "what_went_wrong": Field("text", required=True,
                                            hint="Root causes and contributing factors"),
                   "what_went_right": Field("text", required=True,
                                            hint="Effective responses and controls"),
                   "process_changes": Field("text", required=True,
                                            hint="Recommended process or procedure changes"),
                   "training_needed": Field("enum", required=True,
                                            values=["yes", "no"],
                                            hint="Is additional training needed?"),
                   "training_description": Field("text", required=False,
                                                 hint="What training is needed, if any?"),
                   "equipment_changes": Field("enum", required=True,
                                              values=["yes", "no"],
                                              hint="Are equipment/PPE changes needed?"),
               })
