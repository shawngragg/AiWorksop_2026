# RefView Window/Level Display Transform

**Workshop sandbox:** RefView is fictional, created solely for this workshop, and not intended for clinical use.

## Team coordination

- We are working with two other team members, coordinating through the files in this shared project folder.
- Project artifacts will be updated frequently.
- We are not using source control at this point.
  - *Update:* the project now uses Git with a public GitHub repository,
    `shawngragg/AiWorksop_2026`. `main` is the integration branch and `gragg_dev_1`
    is the development branch.
- Before editing, re-read the relevant files to account for teammates' updates.
- Preserve unrelated changes and flag conflicting edits rather than overwrite them.

## Challenge

Design and implement a reusable component that converts CT-like pixel values into 8-bit grayscale display values using a window center and window width.

- **Input:** pixel value, window center, and window width.
- **Output:** an integer display value from 0 through 255.
- Values below the window appear black; values above it appear white; values inside are mapped proportionally.

## Deliverable

- Interface definition
- Implementation
- Automated unit tests
- Documented assumptions or unresolved questions

## Constraints

- The component will be called once for every pixel in an image.
- The result must always be an integer from 0 through 255.
- The same inputs must always produce the same output.
- Invalid inputs must be handled predictably.

## Acceptance criteria — fixed throughout the workshop

1. Correctly maps values below, inside, and above the specified window.
2. Always returns an integer in the range 0–255.
3. Produces deterministic results.
4. Defines predictable behavior for invalid window parameters.
5. Includes tests covering normal cases, boundaries, and invalid inputs.

## Your task

Use AI the way you normally do to design, implement, and test the component.

## Packet 1 implementation

The C++17 static library exposes `RefView::WindowLevelTransform` through
`AutoWindowProject.Library\WindowLevelTransform.h`. Construct it once per window,
then reuse its const `Map` method for each pixel:

```cpp
#include "WindowLevelTransform.h"

const RefView::WindowLevelTransform transform(50.0, 101.0);
const int display = transform.Map(50.0); // 129
```

The implementation follows Packet 1, page 1 of the D1E2 handout:

```text
lower = center - 0.5 - (width - 1) / 2
upper = center - 0.5 + (width - 1) / 2
pixel <= lower: 0
pixel > upper: 255
otherwise: ((pixel - (center - 0.5)) / (width - 1) + 0.5) * 255
```

Interior results are calculated as `(pixel - lower) * 255 / (width - 1)`, which equals
the formula above but keeps exact .5 results exact in floating point. They are rounded
to the nearest integer with halfway values rounded away from zero (`std::round`), then
clamped to [0, 255] before conversion to `int`.

### Assumptions and error policy

- Inputs use `double`; fractional pixels, centers, and widths are supported.
- Width must be finite and greater than 1, as required by D1E2.
- Additional workshop decisions: center and pixel must also be finite.
  NaN and either infinity are rejected, not mapped to a grayscale value.
- Windows whose calculated bounds overflow or collapse to the same `double`
  are rejected. Distinct finite bounds are required; there is no arbitrary
  minimum width above 1.
- Invalid construction or mapping throws `std::invalid_argument` with a
  diagnostic message. The caller must handle the error explicitly; no substitute
  window or display value is returned.
- Mapping does not mutate the transform or allocate memory on its valid path.
  Window constants are calculated at construction. No numerical performance
  target was supplied, so no throughput guarantee is claimed.
- This implements only Packet 1. The Win32 application remains blank; image
  loading, automatic window selection, and clinical validation are out of scope.

### Automated checks

`AutoWindowProject.Tests\Tests.cpp` uses Visual Studio's native C++ test framework.
Its tests cover the handout's exact worked-example outputs
`0, 0, 1, 129, 254, 255, 255`, boundaries and adjacent representable values,
fractional inputs, negative centers, rounding, widths just above 1, extreme finite
values, range, monotonicity, determinism, and the error policy above.

Build the solution in Visual Studio 2022 using Debug or Release x64, then run all
tests through Test Explorer. Both configurations use the same test cases.

### Test images

`TestImages\` contains 11 deterministic, synthetic 512 × 512 CT-like images:
uint16 little-endian raw files with stored = HU + 1024 and padding 65535, each with
JSON metadata and an 8-bit PNG preview. They cover ordinary images, the Packet 2
phantoms, and the Packet 3 challenging cases. See `TestImages\README.md`.

## Workshop stages

| Handout | Packet 1 change | Status |
|---|---|---|
| D1E1 — Use AI the way you normally do | Original challenge and acceptance criteria | Implemented |
| D1E2 — Context changes everything | Exact formula, width > 1, explicit error, worked example | Implemented and tested |
| D1E3 — Stop asking AI to do everything at once | Decompose; list prioritized questions before changing code | Questions resolved against the facilitator edition; no code change needed |
| D1E4 — Make AI challenge its own work | Independent review with counterexamples | Rounding defect fixed and regression-tested; see D1E4 review record |

The acceptance criteria are unchanged at every stage.

## D1E3 open questions

Per D1E3, the implementation will not change until the highest-impact questions
are resolved. "Current assumption" describes how the code behaves today.

### Essential (could change interface, outputs, or tests)

| # | Question | Current assumption | Affects |
|---|---|---|---|
| Q1 | Are pixel values already in HU, or must the component apply rescale slope/intercept to stored values? What is the pixel type (int16, uint16, real)? | Caller passes HU as `double` | Interface, test images, per-pixel cost |
| Q2 | How should exact .5 results round (half up, half to even, half away from zero)? | Half away from zero (`std::round`) | Exact outputs at ties; rounding test |
| Q3 | The worked example says "approximately". Are exact values required, or is ±1 acceptable? | Exact match required | Test oracle for the worked example |
| Q4 | What form should the "explicit error" for invalid width take: exception, error code/status, or optional result? | `std::invalid_argument` at construction | Interface and caller contract; invalid-input tests |
| Q5 | Are non-integer centers and widths valid (for example, width 1.5)? | Any finite value > 1 is valid | Validation; fractional-width tests |
| Q6 | How should a non-finite pixel (NaN or ±∞) be handled? | Throws `std::invalid_argument` | Per-pixel error path; invalid-pixel tests |

### Optional design choices

| # | Question | Current assumption | Affects |
|---|---|---|---|
| Q7 | Is there a performance target, such as time per 512 × 512 image? Is a whole-buffer API wanted? | None; per-pixel `Map` | Interface; performance test |
| Q8 | Should output be `uint8_t` rather than `int`? | `int` in [0, 255] | Interface |
| Q9 | Are there practical limits on center and width (for example, the 16-bit range), or should any finite value be accepted? | Any finite value whose bounds stay distinct | Validation; extreme-value tests |
| Q10 | Must the transform be thread-safe for concurrent per-pixel use? | Yes (`Map` is `const` with no shared state) | Documentation; concurrency test |

### Facilitator answer sheet

Tick one option per question; ★ marks the current behavior.

- **Q1 – Pixel input:** ☐ HU as real number ★ · ☐ HU as signed 16-bit integer · ☐ Stored uint16; component applies rescale slope/intercept · ☐ Other: ____
- **Q2 – Rounding of .5:** ☐ Half up · ☐ Half to even · ☑ Half away from zero ★ (confirmed by the facilitator edition) · ☐ Truncate (floor) · ☐ Other: ____
- **Q3 – Worked-example precision:** ☐ Exact values required ★ · ☐ ±1 tolerance acceptable · ☐ Other: ____
- **Q4 – Error mechanism:** ☐ Exception at construction ★ · ☐ Error code/status return · ☐ Optional/expected result · ☐ Any explicit form · ☐ Other: ____
- **Q5 – Fractional center/width:** ☑ Any finite value, width > 1 ★ (confirmed) · ☐ Integers only · ☐ Other: ____
- **Q6 – Non-finite pixel:** ☑ Explicit error ★ (confirmed) · ☐ NaN → 0, ±∞ saturate · ☐ Not applicable (integer pixels) · ☐ Other: ____
- **Q7 – Performance/API:** ☐ No target, per-pixel only ★ · ☐ Target: ____ ms per 512 × 512 image · ☐ Add whole-buffer API · ☐ Other: ____
- **Q8 – Output type:** ☐ `int` in [0, 255] ★ · ☐ `uint8_t` · ☐ Other: ____
- **Q9 – Center/width limits:** ☐ Any finite value with distinct bounds ★ · ☐ Limited to range: ____ · ☐ Other: ____
- **Q10 – Thread safety:** ☐ Required (already true) ★ · ☐ Not required · ☐ Other: ____

### Recommended answers (from handout hints)

These answers come from the D1E1, D1E2 and D1E3 handouts, including the Packet 2 and Packet 3 pages. D1E3 says to ask the facilitator only for information we *genuinely* need. Q1 and Q2 are the high-impact unknowns to ask about. The other questions are either answered by the handouts or are low-impact design choices the team can decide and record. See **Question status** below for which answers are confirmed by the handouts and which are our assumptions.

| # | Recommended answer | Handout hint / rationale | Ask facilitator? | Code change if accepted |
|---|---|---|---|---|
| Q1 | The caller passes HU-like values as `double`. Rescale (slope/intercept) is the caller's job. | D1E1 says "CT-like pixel values", and the D1E2 formula uses `x` in the same units as `c` and `w`. Packet 2 talks about images in HU (0, −100, +100 HU inserts). Packet 3 bases the window on the *image-value* histogram, so the window and pixels share units. Keeping rescale out of the component keeps it one responsibility. | **Yes.** The stored-value format is not stated anywhere. | None |
| Q2 | Round half away from zero (`std::round`). For in-window values (≥ 0) this is the same as half up. **Confirmed by the facilitator edition.** | D1E2 says "nearest integer" but not how ties break. The worked example has no ties (1.275, 128.775, 253.725), so it can't tell rounding modes apart. Acceptance criterion 3 (determinism) only needs a fixed, documented rule. | **Yes.** It's a genuine ambiguity, though low impact (±1 only at exact ties). | None; already tested |
| Q3 | Exact integers. "Approximately" refers to the unrounded values. | The raw values 1.275, 128.775 and 253.725 round to 1, 129 and 254. The rows not marked "approximately" (−100, −1, 100, 500) are clamped values. Exact tests are what make determinism (AC 3) checkable. | No | None; the worked-example test already asserts exact values |
| Q4 | An exception from the constructor is acceptable; any explicit, documented error works. | D1E2: invalid widths "must produce an explicit error rather than silently substituting another value". Packet 3's "fall back to a predefined default" belongs to **Auto-Window** (the caller), not the transform. The transform must not substitute values itself. The `large_air` test image (p05 = p95, width 0) exercises exactly this split. | No | None |
| Q5 | Accept any finite center and any finite width > 1, fractions included. | D1E2's only rule is "w must be greater than 1". Packet 3 derives center and width from the p5/p95 bounds, which naturally gives fractional values (for example, `c = (p5 + p95) / 2`). | No | None |
| Q6 | Explicit error (keep the current behavior). | AC 4 and the D1E1 constraint require predictable invalid-input handling. Packet 3 lists "corrupted or missing pixel data". Silently mapping NaN to 0 would be the kind of substitution D1E2 forbids. | Optional. The team can decide, but it is not specified. | None |
| Q7 | No separate target for the transform. Treat Packet 3's **200 ms per 512 × 512 image** as the outer budget for the whole pipeline. An optional whole-buffer `MapImage` helper would also work. | D1E1: "called once for every pixel". Packet 3 gives 200 ms on the reference workstation for Auto-Window. The transform should take a small fraction of that. | No (optional) | Optional: buffer API plus a timing test (for example, < 20 ms per 512 × 512 in Release) |
| Q8 | Keep `int` in the range 0–255. | D1E1: "an integer display value from 0 through 255". `int` meets this, and the range is already tested. `uint8_t` is a style choice, not a requirement. | No | None |
| Q9 | Any finite value whose lower and upper bounds stay distinct. | No limits are given anywhere. The test images use HU −1024 to 3071, well inside `double` precision. | No | None |
| Q10 | Thread-safe (already true). | Per-pixel use and the 200 ms budget make parallel use likely. `Map` is `const` and has no shared state. | No | Optional: document it in the header |

**Summary:** if the facilitator confirms the recommended answers to Q1 and Q2, the current interface, implementation and tests already meet the fixed acceptance criteria. The only possible refinements are the optional Q7 buffer API with a timing test and the Q10 header note.

### Question status

Updated 2026-10-20 after reviewing `Discover_the_Gap_Facilitator_Handouts-D1E3.pdf`, the Facilitator Edition of the D1E3 handouts (marked *"Do not distribute to participants"*). Its Packet 1 table lists the clarifications the facilitator releases when a team asks the matching question.

Status key:
- ✅ **Answered**: the handouts or the facilitator clarifications state it.
- 🟡 **Partially answered**: part is specified, and the rest is our assumption.
- ❌ **Open**: no source answers it; the current behavior is our assumption.

| # | Topic | Status | Source and what it says | Our assumption for the unspecified part | Current code complies? |
|---|---|---|---|---|---|
| Q1 | Pixel input units/type | 🟡 Partially answered | Facilitator: *"Pixel value, center, and width may be integer or floating point."* Nothing says whether pixels are HU or stored values. | Values are HU-like and in the same units as center/width; the caller applies any rescale. Integer inputs convert implicitly to `double` (exact for all 16/32-bit integers). | ✅ Yes |
| Q2 | Rounding of exact .5 | ✅ Answered | Facilitator: *"Round half away from zero."* | None | ✅ Yes. `std::round` rounds half away from zero. |
| Q3 | Exact vs. approximate worked example | 🟡 Partially answered | The "nearest integer" rule (D1E2) plus the confirmed rounding rule (Q2) fully determine 1, 129, 254 (raw values 1.275, 128.775, 253.725). No one says whether ±1 is acceptable. | "Approximately" refers to the unrounded value; tests require exact integers | ✅ Yes |
| Q4 | Error mechanism | 🟡 Partially answered | D1E2: invalid width → *"explicit error rather than silently substituting another value"*. Facilitator: *"Width must be greater than 1"* (width exactly 1 is invalid). The form of the error is not given. | `std::invalid_argument` thrown by the constructor | ✅ Yes |
| Q5 | Fractional center/width | ✅ Answered | Facilitator: inputs *"may be integer or floating point"*, and width must be > 1. | None | ✅ Yes |
| Q6 | Non-finite pixel (NaN/±∞) | ✅ Answered | Facilitator: *"Invalid input; return an explicit error."* | Same exception mechanism as Q4 | ✅ Yes |
| Q7 | Performance target / buffer API | ❌ Open | No transform target. The 200 ms per 512 × 512 image figure is for Auto-Window (Packet 3). | No target; per-pixel `Map` only | n/a |
| Q8 | Output type | ✅ Answered | D1E1: *"an integer display value from 0 through 255"*. | None (`int` is a style choice) | ✅ Yes |
| Q9 | Limits on center/width | ❌ Open | No limits besides width > 1. | Any finite value whose computed bounds stay distinct; otherwise throws | n/a |
| Q10 | Thread safety | ❌ Open | Not mentioned. | `Map` is `const` with no shared state, so it is thread-safe | n/a |

#### Additional facilitator clarifications (questions we had not asked)

| # | Question | Clarification | Current code complies? |
|---|---|---|---|
| Q11 | Can output exceed 0–255 internally? | *"Clamp after calculation and rounding."* | ✅ Yes. `std::clamp(std::round(display), 0, 255)`. |
| Q12 | Is display inversion required? | *"No. Low values are black; high values are white."* | ✅ Yes. Values ≤ lower → 0, > upper → 255. |

#### Still open: no answer found in the handouts or the facilitator edition

| # | Priority | Why it is still open |
|---|---|---|
| Q1 (units part) | Essential (low risk) | HU vs. stored values with rescale is never stated. Our separation (caller rescales) is consistent with the D1E2 formula. |
| Q3 (tolerance part) | Low | The rules make exact values deterministic, so ±1 tolerance only matters if the facilitator expects it. |
| Q4 (error form) | Low | Any explicit error meets the spec; we chose an exception. |
| Q7 | Optional | Matters only if the transform has its own performance requirement or buffer API. |
| Q9 | Optional | Only affects extreme parameter values. |
| Q10 | Optional | Matters only if callers run the transform in parallel. |

#### Implemented on assumptions (not clearly specified)

The current code depends on these team decisions. If a later clarification contradicts one, the affected code and tests must change.

- **Q1:** pixel values are in the same (HU-like) units as center and width; the component does not rescale. Integer inputs pass through `double`.
- **Q3:** the worked example is checked with exact values, with no ±1 tolerance.
- **Q4:** the explicit error is `std::invalid_argument` from the constructor.
- **Q6 (mechanism):** a non-finite pixel throws `std::invalid_argument` from `Map`. That it must be an explicit error is confirmed.
- **Q7:** no performance target; per-pixel API only.
- **Q9:** any finite center/width is accepted as long as the computed bounds stay distinct.
- **Q10:** thread-safe by design; not explicitly tested.

**Conclusion:** every released facilitator clarification (Q2, Q5, Q6, width = 1, Q11, Q12) already matches the implementation and tests. No code change is required. Remaining refinements are optional: add integer-input test cases (Q1/Q5), document thread safety (Q10), and an optional buffer API with a timing test (Q7).

### Clarification log

| # | Answer (source) | Decision | Code/test change |
|---|---|---|---|
| Q1 | Inputs may be integer or floating point (Facilitator D1E3). Units not specified. | Keep the `double` interface; integers convert implicitly. Caller rescales stored values. | None required. Optional: test with integer-typed inputs. |
| Q2 | Round half away from zero (Facilitator D1E3) | Keep `std::round` | None. Optional: rename `RoundsNearestAndMidpointUpward` to say "AwayFromZero". |
| Q3 | Not specified | Exact values, following "nearest integer" plus Q2 | None |
| Q4 | Explicit error (D1E2); width must be > 1 (Facilitator D1E3); form not specified | Keep `std::invalid_argument` from the constructor | None; `RejectsInvalidWidths` covers width 1 |
| Q5 | Integer or floating point allowed (Facilitator D1E3) | Accept fractional center/width > 1 | None; `FractionalCenterAndWidth` covers it |
| Q6 | NaN/∞ is invalid input; return an explicit error (Facilitator D1E3) | Keep throwing `std::invalid_argument` | None; `RejectsNonFiniteCentersAndPixels` covers it |
| Q7 | Not specified | No target for the transform | None |
| Q8 | Integer 0–255 (D1E1) | Keep `int` | None |
| Q9 | Not specified | Any finite value with distinct bounds | None |
| Q10 | Not specified | Thread-safe by design | Optional: document it in the header |
| Q11 | Clamp after calculation and rounding (Facilitator D1E3) | Matches current order | None |
| Q12 | No inversion; low = black, high = white (Facilitator D1E3) | Matches current mapping | None |

## D1E4 review record

| Finding | Decision | Evidence |
|---|---|---|
| Exact .5 results sometimes rounded down (for example center 0.5, width 256, pixel -127: exact 0.5 → returned 0; 39 of 255 ties affected) | **Accepted, fixed.** Interior value now computed from the lower bound, multiplying before dividing (divide first only if the product could overflow). | `EveryExactHalfRoundsAwayFromZero` checks all 255 ties and neighbors ±0.001 |
| Rounding test only covered the easily represented 127.5 midpoint | **Accepted, fixed.** | Same test |
| Finite windows whose bounds collapse in `double` (for example center 1e16, width 2) are rejected | **Open question.** Kept as documented error policy pending clarification. | `RejectsOverflowingAndCollapsedBounds` |
| `pixel > upper` should be `>=` | **Rejected.** D1E2 specifies `x > upper`; at `x == upper` the formula yields exactly 255, so the result is the same. | `ExactBoundariesAndAdjacentValues` |
