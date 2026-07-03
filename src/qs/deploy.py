"""
deploy.py: Build and deploy a versioned application to Opalstack.
"""
import getpass
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fabric import Connection
from fabric.transfer import Transfer
from jinja2 import Environment, PackageLoader
from mongoengine import connect

from .create_wsgi import create_wsgi
from .models import App, Server
from .version import __version__

logging.basicConfig(level=logging.INFO)

# Configuration via environment variables with sensible defaults.
SSH_USER = os.environ.get("QS_SSH_USER", getpass.getuser())
SSH_KEY = os.environ.get("QS_SSH_KEY", os.path.expanduser("~/.ssh/id_rsa"))

# Scripts rendered locally from templates and shipped to the server.
RENDERED_TEMPLATES = ("kill", "start", "stop", "uwsgi.ini")
# Everything bundled into the deployment tarball, at its root. The generated
# files come from the build directory; the project files from the cwd.
GENERATED_FILES = ("kill", "stop", "start", "uwsgi.ini", "wsgi.py")
PROJECT_FILES = ("src", "pyproject.toml", "README.md")


def _git_version() -> str:
    """Return the release tag on HEAD with its leading ``v`` stripped.

    Exits if HEAD carries no tag. (This can misbehave when a commit has
    several tags, since their outputs are concatenated.)
    """
    result = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"],
        capture_output=True, text=True,
    )
    version = result.stdout.strip()[1:]
    if not version:
        sys.exit("Unable to find any tag for current commit")
    return version


def _get_app(app_name: str) -> App:
    """Fetch the app record, exiting with guidance if it is unusable."""
    try:
        app = App.objects.get(name=app_name)
    except App.DoesNotExist:
        sys.exit(f"Application {app_name!r} not found: do you need to run opalsync?")
    if not app.port:
        sys.exit("App has no port number: do you need to run opalsync?")
    return app


def _get_server(app: App, app_name: str) -> Server:
    """Fetch the server the app is hosted on, or exit."""
    try:
        return Server.objects.get(id=app.server)
    except Server.DoesNotExist:
        sys.exit(f"App {app_name} has no server: cannot proceed.")


def _project_names(version: str) -> tuple[str, str]:
    """Return ``(project_name, module_name)``, checking uv agrees with git.

    The module name is the project name with hyphens turned into
    underscores so that it can be imported.
    """
    proj_name, uv_version = subprocess.run(
        ["uv", "version"], capture_output=True, text=True,
    ).stdout.split()
    if uv_version != version:
        sys.exit(f"`uv version` ({uv_version}) and `git tag` ({version}) "
                 "disagree on version")
    return proj_name, proj_name.replace("-", "_")


def _render_build_files(build_dir: Path, app: App, version: str, mod_name: str) -> None:
    """Render the start/stop/kill/uwsgi scripts and wsgi.py into build_dir."""
    jenv = Environment(loader=PackageLoader("qs", "templates"), autoescape=False)
    for filename in RENDERED_TEMPLATES:
        content = jenv.get_template(filename).render(
            PROJECT=app.name, PORT_NO=app.port, VERSION=version,
            HOME_DIR=f"/home/{SSH_USER}",
        )
        (build_dir / filename).write_text(content)
    create_wsgi(name=mod_name, port=app.port, path=build_dir / "wsgi.py")


def _build_tarball(c, build_dir: Path, proj_name: str, version: str) -> Path:
    """Bundle the generated files (from build_dir) and the project files
    (from the current directory) into a single tarball inside build_dir.

    ``gtar -C`` switches directory for the file arguments that follow, so
    the two sets are pulled from different locations yet all land at the
    archive root, exactly as the server expects on extraction.
    """
    tarball = build_dir / f"{proj_name}-{version}.tgz"
    generated = " ".join(GENERATED_FILES)
    project = " ".join(PROJECT_FILES)
    c.local(
        f"(gtar cf {tarball} --no-xattrs "
        f"-C {build_dir} {generated} "
        f"-C {os.getcwd()} {project})"
    )
    return tarball


def _install_remote(c, app: App, server: Server, proj_name: str,
                    version: str, tarball: Path) -> None:
    """Wipe and reinstall the app on the server, then start it."""
    def remote(cmd):
        "Run a single remote command."
        return c.run(cmd)

    # Confirm the target directory exists before running anything
    # destructive in it: a missing or renamed app dir must abort loudly
    # rather than letting `rm -rf` run in an unexpected working directory.
    app_dir = f"apps/{app.name}"
    if not c.run(f"test -d {app_dir}", warn=True).ok:
        sys.exit(f"Remote app directory {app_dir!r} not found on {server.hostname}: "
                 "cannot deploy.")

    # Stop and wipe any existing app, then recreate the skeleton.
    # XXX Note that these should really be app-specfic.
    #     Back when the app saved its own versions things
    #     were different! Unlikely to hurt in the meantime.
    with c.cd(app_dir):
        remote("if [ -e stop ] ; then ./stop || echo 'No stop file' ; fi")
        remote("rm -rf .venv *")
        remote("mkdir -p dist tmp")
    Transfer(c).put(str(tarball), f"{app_dir}/dist/{proj_name}-{version}.tgz")

    # Now install it server-side!
    with c.cd(app_dir):
        remote(f"tar xvf dist/{proj_name}-{version}.tgz")
        remote("chmod +x start stop kill")
        remote("uv sync")
        remote(f"if [ -e ~/envs/{proj_name} ] ; then "
               f"(cp ~/envs/{proj_name} .env && "
               f"echo >&2 'Env file for project {proj_name} copied'); "
               f"else echo >&2 'No env file for project {proj_name}' ; fi")
        remote("./start")


def deploy(app_name: str):
    """
    Identify the tag for the current commit and deploy it to the server.

    This was relatively easy when only using one server, but now we need to
    deal with multiple servers.
    """
    connect("opalstack")

    version = _git_version()
    app = _get_app(app_name)
    server = _get_server(app, app_name)
    proj_name, mod_name = _project_names(version)

    # Create server connection
    c = Connection(
        host=server.hostname,
        user=SSH_USER,
        connect_kwargs={
            "key_filename": SSH_KEY,
        },
    )
    print(f"qs{__version__} delivering {app_name} v{version}")

    # Render and bundle everything under a throwaway build directory so the
    # project root is never polluted with generated deployment files.
    with tempfile.TemporaryDirectory() as tmp:
        build_dir = Path(tmp)
        _render_build_files(build_dir, app, version, mod_name)
        tarball = _build_tarball(c, build_dir, proj_name, version)
        _install_remote(c, app, server, proj_name, version, tarball)


def deploy_cli():
    args = sys.argv[1:]
    if len(args) != 1:
        sys.exit(f"""\
Usage: {os.path.basename(sys.argv[0])} appname

This delivers the currently checked-out version of the current directory's
application to the named Opalstack app using its version number as
identification.""")
    app_name = args[0]
    deploy(app_name)

if __name__ == '__main__':
    deploy_cli()
