# Project instructions

- Never install Python (or other) packages directly onto the local machine/laptop (e.g. `pip install`, `pip install --break-system-packages`, or creating throwaway venvs to test a package). This machine is the user's local laptop, not a disposable sandbox.
- If a new dependency needs to be verified, do it inside the project's Docker setup (`docker-compose`/`Dockerfile`) or by reasoning from documentation/source instead of installing it locally to experiment.
