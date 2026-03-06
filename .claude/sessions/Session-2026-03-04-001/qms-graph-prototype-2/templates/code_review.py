"""Code review procedure template. Extends ProcedureBase with code review steps."""

from graph import Template, Field
from templates.procedure_base import ProcedureBase


class CodeReview(ProcedureBase):
    id = "code-review"
    name = "Code Review Procedure"
    description = "Structured code review: submit -> static analysis -> review -> feedback -> resolution"

    def define_procedure_body(self, g):
        g.node("submit_code",
               prompt="Submit code for review.",
               context="Identify the code change to be reviewed. Provide the branch, "
                       "commit range, or pull request reference.",
               evidence={
                   "branch_or_pr": Field("text", required=True,
                                         hint="Branch name, PR URL, or commit range"),
                   "change_summary": Field("text", required=True,
                                           hint="Brief summary of what the code change does"),
                   "files_changed": Field("integer", required=True,
                                          hint="Number of files changed"),
                   "lines_changed": Field("integer", required=False,
                                          hint="Approximate lines added/removed"),
               })

        g.node("static_analysis",
               prompt="Run static analysis on the submitted code.",
               context="Execute linting, type checking, and automated tests. "
                       "Report any findings before human review begins.",
               evidence={
                   "linting_result": Field("enum", required=True,
                                           values=["pass", "warnings", "errors"],
                                           hint="Result of lint/style checks"),
                   "type_check_result": Field("enum", required=True,
                                              values=["pass", "warnings", "errors"],
                                              hint="Result of type checking"),
                   "test_result": Field("enum", required=True,
                                        values=["pass", "fail", "skipped"],
                                        hint="Result of automated test suite"),
                   "findings_summary": Field("text", required=False,
                                             hint="Summary of any issues found by static analysis"),
               })

        # Extension point: subclasses can inject custom review steps
        # (e.g., security review, performance review, accessibility review)
        self.fill(g, "review_steps")

        g.node("review",
               prompt="Conduct the code review.",
               context="Examine the code for correctness, clarity, maintainability, "
                       "and adherence to project conventions. Consider edge cases, "
                       "error handling, and test coverage.",
               performer="reviewer",
               evidence={
                   "correctness": Field("enum", required=True,
                                        values=["good", "minor_issues", "major_issues"],
                                        hint="Is the code functionally correct?"),
                   "readability": Field("enum", required=True,
                                        values=["good", "acceptable", "poor"],
                                        hint="Is the code clear and well-documented?"),
                   "test_coverage": Field("enum", required=True,
                                          values=["sufficient", "insufficient", "none"],
                                          hint="Are there adequate tests?"),
                   "review_comments": Field("text", required=True,
                                            hint="Detailed review comments and suggestions"),
                   "review_verdict": Field("enum", required=True,
                                           values=["approve", "request_changes", "reject"],
                                           hint="Overall review verdict"),
               })

        g.node("feedback",
               prompt="Address review feedback.",
               context="Review the comments provided and determine which changes to make. "
                       "Respond to each comment with an action taken or rationale for not changing.",
               evidence={
                   "comments_addressed": Field("integer", required=True,
                                               hint="Number of review comments addressed"),
                   "comments_deferred": Field("integer", required=False,
                                              hint="Number of comments deferred to future work"),
                   "changes_made": Field("text", required=True,
                                         hint="Summary of changes made in response to review"),
               })

        g.node("resolution",
               prompt="Resolve the code review.",
               context="Confirm that all feedback has been addressed and the code "
                       "is ready to merge, or document why the review is being closed.",
               evidence={
                   "final_status": Field("enum", required=True,
                                         values=["merged", "closed", "deferred"],
                                         hint="Final disposition of the code change"),
                   "resolution_notes": Field("text", required=False,
                                             hint="Any additional notes on the resolution"),
               })
