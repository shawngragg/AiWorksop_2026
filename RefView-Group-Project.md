# RefView Window/Level Display Transform

**Workshop sandbox:** RefView is fictional, created solely for this workshop, and not intended for clinical use.

## Team coordination

- We are working with two other team members, coordinating through the files in this shared project folder.
- Project artifacts will be updated frequently.
- We are not using source control at this point.
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

Interior results are rounded to the nearest integer with halfway values rounded
upward, then clamped to [0, 255] before conversion to `int`.

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
