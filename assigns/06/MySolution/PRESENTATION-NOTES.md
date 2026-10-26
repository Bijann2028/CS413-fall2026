# Presentation notes and rehearsal plan

Use [PRESENTATION.pdf](PRESENTATION.pdf) for the recording. The editable slide
source is [presentation/slides.html](presentation/slides.html). These notes
are a speaking draft: understand the examples and put explanations into your
own words. They do not claim that a presentation has already been recorded.

The target schedule is **18 minutes 5 seconds**, leaving room inside the
required 15-20 minute interval. The times below are rehearsal targets, not a
measured recording duration. Pause to point at rules, trace reductions, and
explain the saved results. Rehearse with a timer and adjust your pace rather
than assuming that reading these notes guarantees a particular duration.

## Slide 1 — 0:00-0:40 — Introduction

My project compiles extended LAMBDA into pure lambda-calculus. The source has
features we normally treat as built-in, including arithmetic, booleans, pairs,
local bindings, and recursion. The target has only variables, single-parameter
functions, and application. I will explain how those features are represented,
why evaluation strategy matters, and how the tests compare the compiled
behavior with expected results. The pipeline has three stages: compile source
syntax, reduce the generated pure term, and observe the data result. The
compiler itself never calculates the program's answer.

**Cue:** Point to the three stages before advancing.

## Slide 2 — 0:40-1:35 — Language contract

The source uses the course's Assignment 5 AST and visitor interface. Numbers
are natural numbers, so subtraction is truncated: two minus five returns zero.
Despite the name D0Eif0, its condition is a boolean rather than a numeric zero
test. Boolean conjunction and disjunction short-circuit. The target is a
separate AST with exactly three constructors. There is no target integer node
and no target arithmetic primitive. Every encoding name shown later is only
an abbreviation for a larger pure term. Unsupported literals and operators
are rejected throughout the source tree, including code that would not run.

**Cue:** Contrast a source integer constructor with the target's three forms.

## Slide 3 — 1:35-2:35 — Architecture

The compiler is a visitor whose methods translate source constructors locally.
It depends on target syntax and Church builders, but has no dependency on the
evaluator. One evaluation machine accepts both source and target ASTs. Its
common application frames evaluate a function, then its argument, then apply
the function. Source-only frames implement source data operations. The target
path uses only substitution and pure syntax. Observers construct additional
pure terms and send them through this same machine. This makes it possible to
compare source results, explicit expected answers, and compiled observations
without introducing a separate source interpreter or target arithmetic engine.

The module boundaries also make failures easier to locate. An incorrect free
variable set is a scope problem; a pure term with the wrong observed value
points toward translation or encodings; an exhausted observation can be
distinguished from an exhausted execution.

**Cue:** Trace both source and compiled target into the same evaluator.

## Slide 4 — 2:35-3:40 — Church representations

A Church boolean chooses between two arguments. True returns the first, and
false returns the second. A Church numeral specifies how many times to apply
a supplied step function to a starting value. For two, the body applies the
step twice. A pair accepts a selector and supplies its two stored values to
that selector. First and second projection can therefore use true and false
as selectors. Multi-argument notation on the slides is shorthand for nested
single-argument lambdas. The actual compiler expands every one of these
representations into Var, Lam, and App nodes; the reducer has no knowledge of
their meaning as data.

**Cue:** Trace the two applications in the numeral, then the pair selector.

## Slide 5 — 3:40-4:40 — Evaluation strategy

Call-by-value means an application must evaluate both its function and its
argument before substitution. Evaluation is left-to-right, so the function
position is evaluated first. A target value is a lambda abstraction. Weak
evaluation means that reaching a lambda is enough: its body is not normalized
before returning it. This matters for both recursion and Church numerals,
because a returned lambda may contain work that only happens when it is
applied later. The machine uses an explicit continuation stack to enforce
the order. Tests record actual beta steps to verify the traversal, and check
that there is no reduction under lambdas or eta reduction.

**Cue:** Walk through function, argument, and contraction as separate stages.

## Slide 6 — 4:40-5:35 — Budgets

The target budget counts beta-value contractions, rather than tree visits or
alpha-renamings. The identity function alone is already a value, so it completes
with a budget of zero. Identity applied to identity needs one contraction.
With zero available steps, that application exhausts its budget; with one, it
completes successfully. The check occurs immediately before a contraction, so
a value reached on the final allowed step is accepted. Execution and
observation budgets are separate. An exhausted run only says that the
available budget was insufficient. It cannot establish that every larger
budget would also be insufficient, so it is not proof of nontermination.

An administrative action, such as moving from the function to the argument
position, consumes no beta step. This keeps the reported budget independent
of how many bookkeeping transitions the implementation uses internally.

**Cue:** Read all three boundary rows, emphasizing completion at one step.

## Slide 7 — 5:35-6:40 — Scope and freshness

Substituting y for x in lambda y dot x cannot produce lambda y dot y: that
would capture the inserted free variable. The binder must first receive a
fresh name. The target substitution implementation tracks scoped renamings
and does not recursively substitute inside the inserted replacement. Compiler
thunk names are also fresh against source names and the surrounding translated
terms. A local naming supply chooses deterministic suffixes, so repeated calls
produce the same output. Source binding rules remain intact: a let binds only
its body, and coincident fix binders make the parameter shadow the function
name. Free-variable preservation is tested directly on open terms.

For example, let x equal x in x has one free x: the initializer's occurrence.
Treating the initializer as inside the let's scope would incorrectly remove
that name and change the program's meaning.

**Cue:** Explain why the y in the correct result remains free.

## Slide 8 — 6:40-7:35 — Local translation rules

Variables, lambdas, and applications keep their basic structure. A let becomes
an application of a lambda to the initializer. The initializer is outside the
new lambda's scope, while the body is inside it. Strict target application
then forces the initializer before the body can run, preserving source
semantics. Translation is compositional: each rule combines translations of
its children. There is no evaluation or constant folding during compilation.
Both branches of a conditional and unapplied function bodies are still
translated, so an unsupported form there is rejected. Even the divergent
LOOP example compiles immediately because the compiler only builds syntax.

**Cue:** Point out the initializer's position outside the let lambda.

## Slide 9 — 7:35-8:40 — Delayed branches

Directly passing translated branches to a Church boolean would be wrong under
call-by-value: both branch expressions would run before selection. Instead,
each branch is wrapped in a lambda with a fresh unused parameter. Those
lambdas are already values, so selection can happen without executing their
bodies. The boolean returns one thunk, and applying the identity value forces
only that thunk. Source and and or use the same mechanism. False and LOOP
returns false, while true or LOOP returns true. This does not make target
application lazy. It expresses selective evaluation explicitly using ordinary
strict function application and lambda values.

**Cue:** Trace the true case: select the first thunk, then force it with I.

## Slide 10 — 8:40-9:45 — Predecessor

Predecessor uses a pair as iteration state. The starting state is zero, zero.
Each step replaces previous and current with current and current plus one.
After one step the pair is zero, one; after two it is one, two; after three
it is two, three. The first component is therefore the predecessor, with
zero handled naturally by performing no transitions. Subtraction applies
predecessor repeatedly, which makes it truncate at zero. The state pair,
successor, iteration, and projection all execute as Church terms. Python does
not calculate their answers in the target path. The larger encoding was
chosen because this invariant is straightforward to explain and test.

For two minus five, the first two predecessor applications reach zero. The
remaining three leave zero unchanged. This explains truncated subtraction
without adding a special Python zero case to the target reducer.

**Cue:** Follow the state arrows and explain the zero-iteration case.

## Slide 11 — 9:45-10:35 — Comparisons

Comparisons are composed from smaller closed combinators. A natural m is less
than or equal to n exactly when truncated m minus n is zero. Reversing operands
gives greater-than-or-equal; negation gives the strict comparisons. Equality
combines both less-than-or-equal directions. The library also supplies boolean
value combinators. Those accept already evaluated values, so they are distinct
from source-level short-circuit compilation. Tests cover all nine numeric
operators on a small operand grid, including equality and both comparison
outcomes. Boolean tests cover complete truth tables. This checks the encoding
library independently before using it through the source compiler.

**Cue:** Use m=2, n=3 to explain LE and why LT reverses the LE arguments.

## Slide 12 — 10:35-11:45 — Recursion

The compiler translates a recursive function using the specified Z combinator.
Ordinary Y is unsuitable because strict application keeps unfolding its
self-application before producing a usable function value. Z places that
self-application behind an extra lambda parameter. The recursive argument
therefore counts as a value, and unfolds when called. A source fix becomes Z
applied to a function that binds the recursive name and then the ordinary
parameter. If those names coincide, the inner parameter binder shadows the
outer recursive name, matching the source rule. A separate test evaluates a
recursive function to a lambda without calling it, ensuring evaluation does
not enter its body prematurely.

The distinction is visible even for a recursive function whose body would
loop forever when called. Constructing that function must still return a
value. Recursion is activated by application, not by normalizing its body
during function creation.

**Cue:** Point to lambda v in Z and the two binders in the translation rule.

## Slide 13 — 11:45-12:50 — Observation

A computed numeral may be a lambda with unevaluated applications inside, so
matching its syntax against a fully expanded numeral would be insufficient.
Natural observation instead applies it to STEP and BASE. The shared evaluator
then constructs an inert finite spine whose nodes Python can count without
performing arithmetic or reducing under lambdas. Boolean observation selects
between two distinct closed marker values. Pair observation evaluates
projections and observes the components recursively. The caller supplies the
expected kind because Church zero and false share a representation. One
aggregate observation budget covers all nested projection and observation
work. Malformed shapes and exhaustion are reported separately from successful
decoded data.

For a nested pair, the observer first selects an outer component and then
repeats the process using that component's expected kind. All of those
reductions share the same observation allowance rather than silently
resetting a budget for every component.

**Cue:** Explain what Python inspects after reduction, and what it never executes.

## Slide 14 — 12:50-13:45 — Arithmetic walkthrough

This example builds the source AST for two plus three times four. Compilation
places the translated subexpressions inside expanded addition and
multiplication combinators. The pure output is saved in arithmetic.lambda.txt,
so the diagram's abbreviations can be inspected in full. The shared source
evaluation returns fourteen, agreeing with the explicit expected answer. Target
execution takes four beta steps to return a lambda value. Observation then
needs another twenty-five steps to obtain the natural fourteen. The small
execution count is explained by weak evaluation: some arithmetic work remains
beneath the result's lambdas and occurs only when the observer applies them.
The two counts and budgets are deliberately reported separately.

**Cue:** Show the arithmetic entry in results/summary.json if demonstrating live.

## Slide 15 — 13:45-14:50 — Recursive walkthrough

Factorial of four uses a zero equality test, a delayed conditional, multiplication,
and a recursive call on the predecessor. It completes in four hundred
seventy-one execution steps and two hundred eighteen observation steps,
producing twenty-four. Fibonacci of five takes one thousand seven hundred
ninety-four execution steps and forty-five observation steps, producing five.
Its base cases are zero and one. Both results agree with explicit answers and
the shared source path. The compiler does not run either recursive function;
it expands Z and the relevant encodings. These are measured counts for this
implementation, not prescribed counts or a general runtime guarantee.

The arithmetic executes through expanded pure terms even though their full
text is too large for a useful slide. The saved factorial and Fibonacci
target files make that representation inspectable alongside the concise
source functions shown here.

**Cue:** Walk factorial through 4 → 3 → 2 → 1 → 0, then identify the base branch.

## Slide 16 — 14:50-15:40 — Strictness checks

The contrasting examples show why selective evaluation must be precise. A
conditional skips an unselected loop, and the short-circuit operators skip
their right operands when appropriate. But an ordinary application evaluates
its argument even if the function ignores that argument. A let initializer
also runs even when its name is unused. Pairs evaluate both components before
construction, so projecting the first component cannot avoid a loop in the
second. These cases exhaust bounded target execution. They distinguish the
required call-by-value semantics from an implementation that accidentally
behaves lazily. The divergent source path is not run without a bound in the
demonstration collection.

**Cue:** Compare the skipped conditional with the ignored function argument.

## Slide 17 — 15:40-16:35 — Test evidence

The suite has forty-nine unittest methods with additional parameterized cases.
The important evidence is the requirement mapping, rather than the count.
Tests cover capture hazards, shadowing, free-variable preservation, zero and
last-step budgets, traversal order, immutability, every operator, and strict
versus skipped divergence. Tests also replace evaluator entry points with
failures during compilation and prohibit source arithmetic during target
execution. The submitted AST is an unchanged copy of the course file, and an
isolation test loads it without Assignment 5 being present. All fourteen
required demonstrations pass. TESTING.md identifies which checks address each
acceptance obligation and records the measured outcomes.

**Cue:** Identify one semantic test and one structural test as different evidence.

## Slide 18 — 16:35-17:35 — Correctness and limitations

The intended correctness claim is restricted to closed, well-typed programs
returning natural, boolean, or finite data-pair results with enough resources.
The reasoning follows the local translation rules: application preserves
evaluation order, let preserves scope, thunks preserve branch choice, and Z
delays recursive calls appropriately. Capture avoidance supports all of the
binding arguments. Finite tests give evidence, but do not prove the claim for
every possible program. Substitution can grow terms, and some source and
nested-pair traversals still use Python recursion. Observers are not universal
validators of arbitrary untyped terms. These limits are documented rather
than hidden by precomputed answers or host-language shortcuts.

**Cue:** State the claim's result types and sufficient-resource assumption explicitly.

## Slide 19 — 17:35-18:05 — Reproduction and attribution

Both commands run from assigns/06 using Python 3.12 or later, without runtime
dependencies. The test command runs the specification checks. The demo saves
pure terms, counts, outcomes, and expected answers. DESIGN.md explains the
translation and correctness argument. The assignment supplies the language
contract and required representations; reused Assignment 5 scope visitors
and AI assistance are attributed. Those files make the implementation and its
results reproducible and inspectable.

**Cue:** Finish by showing where the saved terms and design explanation live.

## Recording and submission checks

1. Rehearse the full explanation and confirm it lasts **15-20 minutes**. Do not
   infer duration from the page count or these planned timestamps.
2. Use a recording tool that captures the slides, your microphone, and your
   webcam simultaneously. Keep your face visible. A small lower-right inset
   fits the empty corner of these slides; check it does not cover content.
3. Record a short sample first. Play it back and confirm that narration is
   audible, slides are legible, and your face remains visible when changing
   slides or showing results.
4. Record the full presentation. Include the factorial or Fibonacci walkthrough
   and representative compilation/execution results, not just the architecture.
5. Play the final file from beginning to end, check its actual duration, and
   save it under `MySolution/`, for example as `PRESENTATION.mp4`.
6. Add the actual video filename to README.md. If an upload limit requires a
   link instead, add the real accessible recording link and verify that the
   instructor can view it without requesting permission.

Do not submit a placeholder recording or claim that recording/access checks
have passed before performing them. PDF slides are already generated; the
personal recording is the remaining presentation deliverable.
