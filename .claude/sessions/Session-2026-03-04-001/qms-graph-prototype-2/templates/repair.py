"""Repair procedure template. Extends ProcedureBase with repair steps."""

from graph import Template, Field
from templates.procedure_base import ProcedureBase


class Repair(ProcedureBase):
    id = "repair"
    name = "Repair Procedure"
    description = "Systematic repair: assess -> plan -> execute -> test"

    def define_procedure_body(self, g):
        g.node("assess",
               prompt="Assess the damage or defect.",
               context="Document what is broken, its severity, and any safety concerns.",
               evidence={
                   "defect_description": Field("text", required=True,
                                               hint="What is broken or defective?"),
                   "severity": Field("enum", required=True,
                                     values=["minor", "moderate", "severe", "critical"]),
                   "safety_risk": Field("enum", required=True, values=["yes", "no"],
                                        hint="Does this pose a safety risk?"),
               })

        g.node("plan",
               prompt="Plan the repair.",
               context="Describe what needs to be done, tools/materials required, and estimated effort.",
               evidence={
                   "repair_plan": Field("text", required=True,
                                        hint="Step-by-step repair plan"),
                   "materials_needed": Field("text", required=False,
                                             hint="Tools and materials required"),
                   "estimated_duration": Field("text", required=False,
                                               hint="How long will this take?"),
               })

        # Extension point: subclasses can add custom repair steps
        self.fill(g, "repair_steps")

        g.node("execute",
               prompt="Execute the repair.",
               context="Perform the repair as planned. Document any deviations from the plan.",
               evidence={
                   "work_performed": Field("text", required=True,
                                           hint="What was actually done?"),
                   "deviations": Field("text", required=False,
                                       hint="Any deviations from the plan?"),
                   "repair_outcome": Field("enum", required=True,
                                           values=["success", "partial", "failed"]),
               })

        g.node("test-repair",
               prompt="Test the repair.",
               context="Verify that the repair resolved the original defect.",
               evidence={
                   "test_method": Field("text", required=True,
                                        hint="How did you verify the repair?"),
                   "test_result": Field("enum", required=True,
                                        values=["pass", "fail"]),
               })
