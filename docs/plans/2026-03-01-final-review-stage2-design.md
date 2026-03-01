# Final Review Stage Renaming And Full Visibility Design

## Goal

Keep algorithmic flow unchanged while changing user-facing stages to only Stage 1 and Stage 2. Stage 2 (the former final review step) must show all files and allow users to select any file, including files filtered by Stage 1 and files matched by ignore rules.

## Confirmed Product Decisions

1. User-facing stages become:
   - Stage 1: Suffix Screening
   - Stage 2: Final Review and Backup
2. Existing internal path-tiering logic remains in the pipeline but is no longer shown as a user stage.
3. Final review must show all scanned files from source roots, including:
   - internally recommended files (previous Stage 2 candidates)
   - files filtered by Stage 1 suffix whitelist
   - files filtered by ignore rules
4. Users can manually include any displayed file in final selection.
5. Naming must be consistent after refactor; avoid mixed stage2/stage3 naming in code.

## Architecture

### Pipeline data views

- `internal_tiering_view`: same behavior as current Stage 2 candidate generation.
- `final_review_view`: all files under source roots for user selection.

Internal tiering still computes tier/risk recommendations for recommended candidates. Final review merges recommendation data onto the full file list.

### Selection precedence

Final user selection has highest priority:

- user-selected paths are copied
- unselected paths are not copied

This includes paths previously filtered by ignore rules or Stage 1.

## Naming Refactor

Use role-based names in code:

- `stage3_review` module -> `final_review`
- `run_stage3_review` -> `run_final_review`
- `PathReviewRow` -> `FinalReviewRow`
- `_build_stage2_rows` -> `_build_internal_tiering_rows`
- `stage3_review_fn` argument -> `final_review_fn`

User-visible labels:

- remove "Stage 2: Path Tiering" from user-facing logs
- rename former "Stage 3" display to "Stage 2"

## Behavior Preservation

- Internal tiering heuristics and AI scoring remain unchanged.
- Dry-run and local fallback behavior remain unchanged.
- AI directory DFS default preselection applies to internal tiering candidates only.

## Error Handling

- If internal recommendation metadata is unavailable for a file in final review, render it with neutral defaults and allow manual selection.
- Resume checkpoints keep working with renamed review stage fields; include migration fallback for previous checkpoint keys where needed.

## Testing Strategy

1. Pipeline tests
   - user-facing stage logs show Stage 1 and Stage 2 only
   - final review receives all files (including ignored and Stage1-filtered)
   - copying respects final selection even for previously filtered files
2. Final review tests
   - all rows are visible/selectable
   - default selection remains high-value recommended files
   - low-value filtering behavior remains for internal low-value recommendations
3. CLI tests
   - non-interactive final selection wiring uses renamed final-review types/functions
4. Regression
   - full pytest suite

## Documentation Scope

Update:

- `README.md`
- `README.zh-CN.md`
- `docs/architecture.md`
- `docs/architecture.zh-CN.md`

to reflect user-visible stage model (Stage 1 + Stage 2) and full-visibility final review behavior.
