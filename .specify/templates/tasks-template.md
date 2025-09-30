# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting, video processing libraries
   → Tests: contract tests, integration tests, video quality tests, translation tests
   → Core: models, services, CLI commands, video processors, translation engines
   → Integration: DB, middleware, logging, video streaming pipelines
   → Polish: unit tests, performance, docs, video analysis validation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 3.1: Setup
- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools
- [ ] T004 [P] Install video processing libraries (opencv-python, ffmpeg-python, etc.)
- [ ] T005 [P] Setup video format detection and audio extraction utilities
- [ ] T006 [P] Install translation libraries (transformers, torch, etc.)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T007 [P] Video format detection test in tests/contract/test_video_formats.py
- [ ] T008 [P] Video-to-audio extraction test in tests/contract/test_video_extraction.py
- [ ] T009 [P] Translation accuracy test in tests/integration/test_translation.py
- [ ] T010 [P] Real-time streaming test in tests/integration/test_realtime_streaming.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T011 [P] Video processor model in src/models/video_processor.py
- [ ] T012 [P] Translation service in src/services/translation.py
- [ ] T013 [P] CLI --extract-audio in src/cli/video_commands.py
- [ ] T014 [P] CLI --translate-stream in src/cli/video_commands.py
- [ ] T015 Video format detection and audio extraction
- [ ] T016 Real-time streaming pipeline
- [ ] T017 Error handling and logging

## Phase 3.4: Integration
- [ ] T018 Connect translation results to storage
- [ ] T019 Real-time video streaming pipeline
- [ ] T020 Video processing metrics logging
- [ ] T021 Memory management for continuous video processing

## Phase 3.5: Polish
- [ ] T022 [P] Unit tests for video validation in tests/unit/test_video_validation.py
- [ ] T023 Performance tests (1.5x real-time processing)
- [ ] T024 [P] Update docs/video-api.md
- [ ] T025 Translation quality benchmarks
- [ ] T026 Run video-testing.md

## Dependencies
- Tests (T007-T010) before implementation (T011-T017)
- T011 blocks T012, T018
- T015 blocks T019
- Implementation before polish (T022-T026)

## Parallel Example
```
# Launch T007-T010 together:
Task: "Video format detection test in tests/contract/test_video_formats.py"
Task: "Video-to-audio extraction test in tests/contract/test_video_extraction.py"
Task: "Translation accuracy test in tests/integration/test_translation.py"
Task: "Real-time streaming test in tests/integration/test_realtime_streaming.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task