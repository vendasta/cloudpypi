import os
import sys
import unittest
from invoke import task, run


@task
def clean():
    """
    Clean files.
    """
    run("find . -iname *.pyc -exec rm -rf {} \;")


@task
def deploy():
    """
    Clean files.
    """
    run("appcfg.py update cloudpypi")


@task
def flake8():
    """
    Run flake8.
    """
    run("flake8")


@task
def fetch_deps():
    """
    Fetch dependencies and install to lib directory.
    """
    run("pip install -r requirements.txt -t ./cloudpypi/lib/")


@task
def test():
    """
    Run tests.
    """
    if not os.path.isdir('./cloudpypi/lib/'):
        fetch_deps()

    sys.path.append(os.environ['GAE_SDK_ROOT'])
    sys.path.append('./tests/lib/')
    sys.path.append('./cloudpypi/lib/')
    sys.path.append('./cloudpypi/')

    import dev_appserver
    dev_appserver.fix_sys_path()

    suite = unittest.loader.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(suite)
