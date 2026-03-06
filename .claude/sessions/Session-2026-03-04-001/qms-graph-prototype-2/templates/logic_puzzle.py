"""Standalone logic puzzle template. No inheritance — demonstrates basic template."""

from graph import Template, Field


class LogicPuzzle(Template):
    id = "puzzle"
    name = "Logic Puzzle"
    description = "A deductive reasoning puzzle with clues and solution"

    def define(self, g):
        g.node("setup",
               prompt="Read the puzzle.",
               context="""Five people live in five consecutive houses. Each person has a
different nationality, drinks a different beverage, and owns a different pet.

Clues:
1. The Brit lives in the red house.
2. The Swede keeps dogs.
3. The Dane drinks tea.
4. The green house is immediately to the left of the white house.
5. The green house owner drinks coffee.
6. The person who smokes Pall Mall keeps birds.
7. The owner of the yellow house smokes Dunhill.
8. The person in the center house drinks milk.
9. The Norwegian lives in the first house.
10. The Blend smoker lives next to the cat owner.
11. The horse owner lives next to the Dunhill smoker.
12. The Bluemaster smoker drinks beer.
13. The German smokes Prince.
14. The Norwegian lives next to the blue house.
15. The Blend smoker has a neighbor who drinks water.

Question: Who owns the fish?""",
               evidence={
                   "understood": Field("enum", required=True, values=["yes"],
                                       hint="Confirm you have read the puzzle"),
               })

        g.node("work",
               prompt="Work through the puzzle step by step.",
               context="Use deductive reasoning. Show your work.",
               evidence={
                   "reasoning": Field("text", required=True,
                                      hint="Your step-by-step deduction"),
               })

        g.node("solve",
               prompt="State your answer.",
               evidence={
                   "fish_owner": Field("text", required=True,
                                       hint="Who owns the fish?"),
                   "house_assignments": Field("text", required=True,
                                              hint="Full assignment of all houses"),
                   "confidence": Field("enum", required=True,
                                       values=["certain", "likely", "unsure"]),
               },
               terminal=True)
