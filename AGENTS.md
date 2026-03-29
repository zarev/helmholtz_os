# Project Guidelines

## Validation

- For any bug or behavior that can be verified visually, use the screenshot workflow while fixing it instead of relying only on logs or assumptions.
- In this repository, prefer `ur3_pick_place_docker/scripts/capture_sim_screenshots.sh` to validate Gazebo or simulation-view changes as you iterate.
- For every bug fix or new feature, keep looking for a concrete validation method and continue working until the requested outcome has been validated.

## Repository Boundaries

- The nested PICK_AND_PLACE source tree is reference-only: you may inspect and rely on files under `ur3_pick_place_docker/ws/src/UR3_ROS2_PICK_AND_PLACE`, but you must never modify code inside that tree.
- When behavior changes are needed, implement them in repo-owned wrappers, configs, scripts, overlays, or model overrides outside the nested PICK_AND_PLACE tree.

## Working Style

- Prefer validation that matches the user-visible outcome: screenshots for visual behavior, runtime checks for live services, and targeted verification for each requested change.
- Do not stop after making code changes alone; stop only after the requested behavior has been checked with an explicit validation step.

## Commits

- Before creating a commit for the current work chunk, ask whether the user wants that chunk committed now.
- When creating a commit, use the initial problem prompt for that work chunk to shape the commit message.
- After creating a commit, always notify the user that the commit was made.