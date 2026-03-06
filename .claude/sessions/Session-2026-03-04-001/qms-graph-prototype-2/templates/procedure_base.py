"""Base procedure template. All procedures share: start -> [body] -> verify -> close."""

from graph import Template, Field


class ProcedureBase(Template):
    id = "proc-base"
    name = "Base Procedure"
    description = "Abstract base for all procedure templates"
    abstract = True

    def define(self, g):
        g.node("start",
               prompt="Begin this procedure.",
               context="Review the objective and confirm you are ready to proceed.",
               evidence={
                   "objective": Field("text", required=True, hint="What is the goal?"),
                   "ready": Field("enum", required=True, values=["yes", "no"],
                                  hint="Are you ready to proceed?"),
               },
               gate="response.get('ready') == 'yes'")

        # Extension point: subclasses define the procedure body
        self.fill(g, "procedure_body")

        g.node("verify",
               prompt="Verify the results.",
               context="Check that all steps were completed successfully and evidence is complete.",
               evidence={
                   "all_steps_passed": Field("enum", required=True, values=["yes", "no"]),
                   "verification_notes": Field("text", required=False,
                                               hint="Any observations or concerns?"),
               },
               gate="response.get('all_steps_passed') == 'yes'")

        g.node("close",
               prompt="Close this procedure.",
               evidence={
                   "outcome": Field("enum", required=True, values=["pass", "fail"]),
                   "summary": Field("text", required=True,
                                    hint="Final summary of what was accomplished"),
               },
               terminal=True)
