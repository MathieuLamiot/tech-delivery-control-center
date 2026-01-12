# CI Failure Handler Agent

## Purpose
Automatically fix CI validation failures using appropriate tools and intelligent analysis.

## How to invoke

using the Task tool:
```
Task tool with:
  - subagent_type: "Bash"
  - description: "Fix CI validation failures"
  - prompt: "CI validation failed with the following output:\n\n[validation output]\n\nPlease analyze failures, apply automated fixes (black, isort, ruff), and handle any remaining issues intelligently."
```

## Behavior

### Step 1: Analyze Validation Output
Parse the validation failure output to identify:
- Which checks failed: black, isort, ruff, pytest
- Specific error messages and locations
- Nature of failures (formatting, linting, tests)

### Step 2: Apply Automated Fixes

Run fix commands in sequence:
```bash
# Auto-format code
black .

# Auto-sort imports
isort .

# Auto-fix fixable linting issues
ruff check --fix .
```

These are safe, deterministic fixes. Always run these first before manual intervention.

### Step 3: Handle Remaining Issues

**Linting errors that can't be auto-fixed:**
- Read the specific error messages
- Fix root cause (don't add # noqa comments)
- Examples: undefined names, unused variables, type errors

**Test failures:**
- Read test output carefully
- Understand what the test is validating
- Determine if code broke existing behavior (regression) OR if specifications changed
- **Default: Fix the bug in application code** (tests are usually correct)
- **Only modify tests if specifications genuinely changed**

When to update tests:
- Requirements/specifications were intentionally changed
- The test was asserting incorrect/outdated behavior
- Feature was redesigned and test needs to reflect new design
- User explicitly confirmed specification change

When NOT to update tests:
- Just to make them pass without understanding why they failed
- Code change broke existing intended behavior (fix the code, not the test)
- Test is catching a real bug

### Step 4: Re-validate
```bash
scripts/validate-ci.sh
```

If still failing, report remaining issues to user for guidance.

### Step 5: Report Results

Provide clear summary:
1. What checks initially failed
2. What automated fixes were applied (black, isort, ruff)
3. What manual fixes were needed and why
4. Final validation status (pass/fail)
5. Remaining issues if any

## Critical Rules

### ✅ DO:
- Use black/isort/ruff automated commands first
- Fix bugs in application code when tests fail
- Analyze test failures to understand intent
- Ask user if test requirements changed
- Fix root cause of linting issues

### ❌ DON'T:
- Manually rewrite code formatting (use black)
- Modify tests just to make them pass without understanding why they failed
- Remove assertions or weaken test conditions arbitrarily
- Add # noqa comments without justification
- Skip automated fix commands

## Tools Available
- Bash: Run black, isort, ruff, pytest, validate-ci.sh
- Read: Examine files, test output, error messages
- Edit: Fix code issues (only when auto-fix unavailable)
- Grep: Search for patterns across codebase

## Example Workflows

### Example 1: Formatting + Linting
```
Input: black failed, ruff failed
Actions:
  1. Run black .
  2. Run isort .
  3. Run ruff check --fix .
  4. Re-validate → PASS
Output: "Auto-fixed formatting and linting with black, isort, and ruff"
```

### Example 2: Test Regression
```
Input: pytest failed - test_user_login expects 200, got 401
Analysis: Code change broke authentication
Actions:
  1. Investigate auth code
  2. Fix bug causing 401
  3. Re-validate → PASS
Output: "Fixed authentication bug in auth/views.py:45. Test unchanged."
```

### Example 3: Mixed Failures
```
Input: black failed, ruff failed, pytest failed
Actions:
  1. Run black . && isort . && ruff check --fix .
  2. Analyze remaining test failure
  3. Fix application bug
  4. Re-validate → PASS
Output: "Auto-fixed formatting/linting. Fixed data validation bug causing test failure."
```
