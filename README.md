# qs: a quick site deployer

`qs` deploys local WSGI sites to [Opalstack](https://www.opalstack.com/) from the
command line, with no need to touch the web control panel. It mirrors your
Opalstack account into a local MongoDB database, creates custom applications
through the Opalstack API, and ships tagged releases of your project up to the
server over SSH.

> Status: working but personal tooling — expect sharp edges.

## Requirements

- Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/)
- A local **MongoDB** instance (the tools use a database called `opalstack`)
- An Opalstack account and an API token

## Install

```sh
uv tool install -U .
```

This puts the four console commands below on your `PATH`. (The `.justfile`
builds and installs a wheel via `just install` if you prefer.)

## Configuration

Set via environment variables:

| Variable           | Used by            | Default                | Purpose                                   |
| ------------------ | ------------------ | ---------------------- | ----------------------------------------- |
| `OPALSTACK_TOKEN`  | `opalsync`, `new_app` | *(required)*        | Opalstack API token                       |
| `QS_SSH_USER`      | `deploy`           | current OS user        | SSH login used to reach the server        |
| `QS_SSH_KEY`       | `deploy`           | `~/.ssh/id_rsa`        | SSH private key file                      |
| `QS_MANAGER_NAME`  | `new_app`          | current OS user        | Opalstack OS user that owns the new app   |
| `QS_SERVER_NAME`   | `new_app`          | `opal5.opalstack.com`  | Web server to create the app on           |

## Commands

- **`opalsync`** — download your entire Opalstack account state (apps, servers,
  domains, …) into the local `opalstack` MongoDB database. Run this first, and
  again whenever the account changes on Opalstack's side.

- **`new_app <name>`** — create a new custom (`CUS`) application in your Opalstack
  account and record it locally. Custom apps get only a directory and a port;
  everything else is up to you.

- **`deploy <appname>`** — package the currently checked-out commit and deploy it
  to the named Opalstack app. The commit **must** carry a git tag whose version
  matches `uv version`; that version identifies the release. `qs` renders the
  uwsgi/start/stop scripts, builds a tarball, and installs and starts it on the
  server looked up from the app's record.

- **`create_wsgi <module> [port]`** — write a `wsgi.py` entry point for the given
  module. Normally invoked by `deploy`; occasionally handy on its own.

## Typical workflow

```sh
export OPALSTACK_TOKEN=…            # once per shell

opalsync                            # mirror account state locally
new_app mysite                      # create the app on Opalstack

# … develop, commit, then tag the release to match `uv version` …
git tag v$(uv version | awk '{print $2}')

deploy mysite                       # ship it
```

### Per-environment `.env`

Deployment-time settings that differ between your laptop and the server are kept
**on the server**. If a file `~/envs/<project_name>` exists in the SSH user's home
directory, `deploy` copies it to the deployed app's `.env`; otherwise it notes
that none was found.

## Development

```sh
uv sync            # install dev dependencies (pytest, mongomock, ruff)
uv run ruff check .
uv run pytest      # tests run against mongomock — no real MongoDB needed
```
