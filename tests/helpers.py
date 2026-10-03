"""Shared helpers for the kit's tests (standard library only).

    python3 -m unittest discover -s tests -v
"""
import importlib.util
import os
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(*parts):
    return os.path.join(KIT, *parts)


def run(script, *args, env=None, cwd=None, timeout=600):
    """Run a kit script (Python or Node) and return the CompletedProcess (text, captured)."""
    e = dict(os.environ)
    e.setdefault('PYTHONPYCACHEPREFIX', os.path.join(os.path.expanduser('~'), '.cache', 'kit-pyc'))
    if env:
        e.update(env)
    full = path(script)
    cmd = ([sys.executable, full] if script.endswith('.py') else ['node', full]) + [str(a) for a in args]
    return subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=cwd, timeout=timeout)


def load(script, name=None):
    """Import a kit script as a module (file names may contain dashes). The script must guard its main code."""
    full = path(script)
    spec = importlib.util.spec_from_file_location(name or os.path.basename(script).replace('-', '_')[:-3], full)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
