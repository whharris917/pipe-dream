# Experiment Protocol Report: LFU-Aging vs LRU Cache Performance

## 1. Protocol Completion

**Status: COMPLETED** -- All 26 steps traversed successfully (start, hypothesis, design, pre-check, 10x run-trial, 10x more-trials, analyze, conclusion).

The workflow engine guided the experiment through the full scientific method pipeline without errors. Batching worked for the first three steps (research question, hypothesis, design), but the trial loop required individual step submission due to the conditional branching at `more-trials`.

---

## 2. Experimental Design

### Research Question
Does LFU-Aging achieve a higher cache hit rate than LRU for a web application database query layer, given identical cache capacity (10,000 entries) and production-representative workloads?

### Hypotheses
- **H0:** Mean hit rate of LFU-Aging <= Mean hit rate of LRU
- **H1:** Mean hit rate of LFU-Aging > Mean hit rate of LRU
- **Alpha:** 0.05 (one-sided test)
- **Minimum practical effect size:** 5 percentage points
- **Success threshold:** LFU-Aging >= 80% hit rate AND statistically significant

### Design
- **Workload:** 7 days of production query logs, split into 10 non-overlapping 1M-query segments
- **Control:** LRU, 10K entries, doubly-linked-list + hashmap
- **Treatment:** LFU-Aging, 10K entries, frequency counters with aging factor 0.5 per 100K accesses
- **Warm-up:** 10K queries discarded, measurement over 990K queries per trial
- **Confounds addressed:** Same hardware, same backing data structure, temporal variance captured across days, JIT pre-warming

---

## 3. Results and Statistical Analysis

### Raw Trial Data

| Trial | LRU Hit Rate | LFU-Aging Hit Rate | LRU p99 Latency | LFU-Aging p99 Latency |
|-------|-------------|-------------------|-----------------|---------------------|
| 1     | 71.4%       | 80.2%             | 43ms            | 36ms                |
| 2     | 72.8%       | 82.1%             | 41ms            | 34ms                |
| 3     | 70.9%       | 79.8%             | 44ms            | 37ms                |
| 4     | 73.1%       | 81.9%             | 42ms            | 35ms                |
| 5     | 72.3%       | 82.5%             | 41ms            | 34ms                |
| 6     | 71.7%       | 80.7%             | 43ms            | 36ms                |
| 7     | 73.5%       | 83.1%             | 40ms            | 33ms                |
| 8     | 71.2%       | 79.5%             | 44ms            | 37ms                |
| 9     | 72.6%       | 81.4%             | 42ms            | 35ms                |
| 10    | 71.8%       | 81.8%             | 43ms            | 34ms                |

### Statistical Summary

| Metric | LRU (Control) | LFU-Aging (Treatment) |
|--------|--------------|----------------------|
| Mean   | 72.13%       | 81.30%               |
| SD     | 0.86%        | 1.20%                |

### Inferential Statistics

- **Test:** Paired t-test, one-sided (treatment > control)
- **t-statistic:** 48.47
- **Degrees of freedom:** 9
- **p-value:** 1.70e-12
- **95% CI for difference:** [8.74%, 9.60%]
- **Mean difference:** 9.17 percentage points
- **Cohen's d:** 8.76 (extremely large effect)

### Verdict
- **Reject H0** -- LFU-Aging significantly outperforms LRU (p < 0.001)
- **Practical significance:** YES -- 9.17pp exceeds the 5pp minimum threshold
- **Success threshold met:** YES -- treatment mean (81.30%) exceeds 80%
- **Note:** Did NOT reach the team's optimistic 85% projection

### Recommendation
**Adopt LFU-Aging**, but calibrate expectations to ~81% hit rate rather than 85%. The 9pp improvement is consistent, robust across traffic patterns, and translates to ~17% p99 latency reduction.

### Limitations
1. Only 7 days of traffic tested (no seasonal/campaign coverage)
2. Single cache size (10K entries) -- relative advantage may differ at other sizes
3. Aging parameter (0.5/100K) not optimized -- tuning could improve results
4. Single application workload -- scan-heavy workloads could favor LRU
5. Memory overhead of per-entry frequency counters not measured
6. Simulated environment -- production concurrency effects not captured

---

## 4. Usability Issues with the Workflow Engine

### Issues Encountered

1. **JSON quoting in shell is painful.** Submitting complex JSON via `--response '<json>'` on the command line requires careful escaping. The workaround of writing to a temp file and using `$(cat file)` works but adds friction. A `--response-file` flag would be a major quality-of-life improvement.

2. **Trial loops are verbose.** The run-trial -> more-trials -> run-trial cycle means 20 engine invocations for 10 trials. This is correct for the general case (you might decide to stop early or add trials), but for pre-planned trial counts, a batch mode for the loop would be nice.

3. **No way to review accumulated evidence.** After submitting 10 trials, I wanted to review all my data before analysis. The engine has no `evidence` or `history` command to dump what was collected. I had to track my own data externally.

4. **Lookahead is helpful.** The engine showing upcoming batchable nodes is genuinely useful -- it let me plan ahead and batch the first 3 steps together.

5. **Conditional edges work correctly.** The pre-check -> not-ready conditional routing and the more-trials -> run-trial loop both behaved as expected.

---

## 5. Did the Structured Workflow Improve or Degrade Quality?

**Net positive, with caveats.**

**Improvements:**
- The protocol forced me to articulate the research question, hypotheses, and controlled variables BEFORE generating any data. This is exactly the right order -- it prevents post-hoc rationalization and HARKing (Hypothesizing After Results are Known).
- The pre-check gate is valuable. In a real experiment, forgetting to validate instrumentation before running trials is a common and expensive mistake.
- The explicit separation of analysis from conclusion forced me to present the numbers before interpreting them, reducing narrative bias.
- The evidence schema acted as a checklist ensuring I did not skip key elements (e.g., confidence intervals, effect size, limitations).

**Degradations:**
- The trial loop felt mechanical. In a real experiment, you would observe emerging patterns between trials and potentially adjust. The rigid structure does not accommodate adaptive designs.
- The protocol does not have a "data review" step between trials and analysis. This is where you would normally eyeball the data for outliers, check distributional assumptions, and decide if a parametric test is appropriate.
- The one-size-fits-all evidence schema for `run-trial` does not accommodate trial-specific metrics that might emerge (e.g., I wanted to note that weekend vs weekday patterns showed different magnitudes of improvement).

**Overall:** The structure improved rigor at the cost of some flexibility. For a standardized experiment where the protocol is known in advance, this is a good trade. For exploratory research, it would be too constraining.

---

## 6. Rating: 7/10

**What earned points:**
- Clean scientific method scaffolding that enforces good practices
- Batching support for independent steps saves time
- Conditional routing handles decision points correctly
- The evidence schema acts as both a checklist and a data contract
- Terminal node concept provides clear completion signal

**What cost points:**
- Shell-based JSON submission is clunky (-1)
- No built-in evidence review/export (-1)
- Trial loops are repetitive without a loop primitive (-1)

The engine is well-suited for structured, repeatable protocols. It successfully imposed discipline on the experimental process without being so rigid that it prevented good work. The main improvements would be operational (better CLI ergonomics, evidence review) rather than architectural.
