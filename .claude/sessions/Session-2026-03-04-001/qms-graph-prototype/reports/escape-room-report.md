# Escape Room Report: The Locked Laboratory

## 1. Completion Status

Successfully completed the escape room. All 10 steps traversed, final state: **complete**.

---

## 2. Puzzle Answers (with work shown)

### Room 1: The Locked Laboratory (4-digit door code)

- **Circled elements:** Helium (2), Nitrogen (7), Oxygen (8)
- **Sum of atomic numbers:** 2 + 7 + 8 = 17
- **Clock hour:** 3 (clock showing 3:14)
- **Formula:** DOOR = SUM * CLOCK_HOUR = 17 * 3 = 51
- **Door code:** 0051

### Room 2: The Hallway (three riddles)

- **Door A (Biology):** "Cities but no houses, forests but no trees, water but no fish" = **Map** (starts with M)
- **Door B (Chemistry):** "The more you take, the more you leave behind" = **Footsteps** (starts with F)
- **Door C (Physics):** "Speak without a mouth, hear without ears, come alive with wind" = **Echo** (starts with E)
- **Alphabetical order of first letters:** E < F < M
- **Visit order:** Physics (E), Chemistry (F), Biology (M)
- **First lab:** Physics

### Room 3: Physics Lab (circuit puzzle)

- **Circuit:** 12V battery, R1=3 ohms and R2=6 ohms in series
- **Total resistance:** R_total = 3 + 6 = 9 ohms
- **Current:** I = V/R = 12/9 = 4/3 = 1.33A
- **Voltage drop across R2:** V_R2 = I * R2 = (4/3) * 6 = 8V
- **Exit code:** "18" (current ~1, voltage drop 8, concatenated)
- **Key found:** GREEN

**Note:** The puzzle says "current (whole number)" but 12/9 is not a whole number. This is a design issue (see section 4).

### Room 4: Chemistry Lab (balance equation)

- **Equation:** _Fe + _O2 -> _Fe2O3
- **Balanced:** 4Fe + 3O2 -> 2Fe2O3
  - Fe: 4 on left, 2*2=4 on right
  - O: 3*2=6 on left, 2*3=6 on right
- **Safe code:** "432" (coefficients concatenated)
- **Key found:** BLUE
- **Note found:** "Multiply the first room's door code by 2 for the final room"

### Room 5: Biology Lab (DNA puzzle)

- **Given strand:** A-T-G-C-C-A-T-G
- **Complementary strand:** T-A-C-G-G-T-A-C
  - A pairs with T, T pairs with A, G pairs with C, C pairs with G
- **Hydrogen bonds per pair:**
  - A-T: 2, T-A: 2, G-C: 3, C-G: 3, C-G: 3, A-T: 2, T-A: 2, G-C: 3
- **Total hydrogen bonds:** 2+2+3+3+3+2+2+3 = **20**
- **Key found:** RED

### Room 6: The Final Door

- **Keys collected:** RED (biology), GREEN (physics), BLUE (chemistry)
- **Rainbow order (ROY G BIV):** Red, Orange, Yellow, Green, Blue, Indigo, Violet
- **Key insertion order:** RED, GREEN, BLUE
- **Original door code:** 0051 (= 51)
- **Final code:** 51 * 2 = **102**

---

## 3. Usability Issues with the Workflow Engine

1. **No validation feedback on answers.** The engine accepts any response and advances regardless of correctness. There is no way to know if an answer was right or wrong. For a puzzle/escape room, this significantly reduces engagement -- you never get the satisfaction of a "correct!" or the challenge of a "try again."

2. **The `next-lab` routing node adds friction.** Having to manually declare which labs are completed and which to visit next feels like bookkeeping, not puzzle-solving. The engine could track visited nodes automatically and present only unvisited options.

3. **The `batchable: false` on lookahead nodes is restrictive.** The hallway-to-first-lab transition could have been batchable since the riddle answers directly determine the routing. Instead it requires two round-trips.

4. **No way to review previous responses.** If you forget a clue from an earlier room (like the door code), you cannot look back at your prior submissions. The `status` command only shows the current node.

5. **Ticket file path uses backslashes on Windows.** The engine returns `".tickets\\escape-001.json"` which works but is inconsistent with the Unix-style paths used in the CLI examples.

---

## 4. Suggestions for Improvement

### Engine Improvements

1. **Add answer validation.** Define expected answers in the YAML (or a separate answer key) and provide pass/fail feedback. Optionally allow retries on failure.

2. **Track visited nodes automatically.** For graphs with hub-and-spoke patterns (like the next-lab router), the engine should know which branches have been visited and present that as context.

3. **Add a `history` command** that shows all previous responses in the ticket, so the solver can review earlier clues.

4. **Support conditional hints.** If a solver gets stuck, the engine could reveal progressive hints based on attempt count.

5. **Normalize path separators** in output to match the platform or always use forward slashes.

### Puzzle Design Improvements

1. **Fix the physics puzzle numbers.** R1=4 and R2=8 with V=12 would give I=1A and V_R2=8V -- clean whole numbers that match the "whole number" hint. Alternatively, R1=2 and R2=4 with V=12 gives I=2A and V_R2=8V (matching the example in the prompt).

2. **The first room's "what they BUILD" notebook hint is a red herring.** The notebook says "the sequence is not the atomic numbers themselves, but what they BUILD when combined in order" -- but then the whiteboard formula just uses SUM of atomic numbers. The notebook hint suggests something more complex (like molecular formulas or compound atomic numbers) that is never used. Either remove the misleading notebook entry or make it relevant.

3. **Add more cross-room dependencies.** The chemistry lab note about "multiply by 2" is a good example. More of these inter-room connections would make the puzzle feel more integrated.

4. **The riddle answers determining visit order is clever but under-utilized.** The visit order has no actual impact on the puzzle outcomes -- you get the same keys regardless. Making the order matter (e.g., a clue in one lab is only useful if you have already visited another) would add depth.

---

## 5. Rating: 7/10

**What worked well:**
- The multi-domain structure (physics, chemistry, biology, riddles) provides variety
- The cross-room callback (remembering the door code for the final room) is a satisfying mechanic
- The graph topology with the hub-and-spoke lab pattern is a good test of the engine's routing capabilities
- The puzzles are solvable and appropriately scoped for a prototype demonstration

**What held it back:**
- No answer validation means no feedback loop -- the core escape room tension of "did I get it right?" is absent
- The physics puzzle has a numerical error (non-integer current despite "whole number" hint)
- The misleading notebook clue in room 1 creates unnecessary confusion
- The `next-lab` bookkeeping steps feel like engine overhead rather than puzzle content (3 of the 10 steps are just routing)

For a prototype demonstrating the workflow engine's capabilities, this is solid work. The branching logic, conditional routing, and state accumulation across nodes all function correctly. The escape room scenario is a creative way to exercise the engine's features.
