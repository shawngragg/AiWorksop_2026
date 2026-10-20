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
