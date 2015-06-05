# CloudPyPI - minimal PyPI server for use with pip/easy_install

[![Build Status](https://travis-ci.org/vendasta/cloudpypi.svg)](https://travis-ci.org/vendasta/cloudpypi)

CloudPyPI is a minimal PyPI compatible server hosted on Google App Engine with
packages served from Cloud Storage. CloudPyPI includes an authentication
and authorization framework for securing your private packages. Any packages not
found on your CloudPyPI instance are automatically retrieved from PyPI itself.

Credit to [pypiserver](https://github.com/pypiserver/pypiserver) for the intial
file system implementation.

## Limitations

These are known limitations. Pull requests welcome.

- CloudPyPI does not implement the XMLRPC interface: pip search will not work.
- CloudPyPI does not implement the json based '/pypi' interface.

## Usage

For CloudPyPI to function, you must create a `packages` directory in Google
Cloud Storage to hold your eggs and wheels. The name of this directory is
configurable using the `self.bucket` parameter in `main.py`.

### Deploying the App

Deploy the app with appcfg.py.

```bash
appcfg.py update cloudpypi
```

### Creating a User

To use CloudPyPI you must create a user. Navigate to your app and create a user,
specifying a username and password.

### Configuring pip

To use CloudPyPI with pip, you will need to tell it where to find your server
and what your authorization credentials are. Create the file
`$HOME/.pip/pip.conf` specifying your username, password and the location of
your server. Use the /simple/ index.

```
[global]
index-url = https://<username>:<password>@cloudpypi.appspot.com/simple/
```

You should now be able to publish packages to CloudPyPI and install packages
from CloudPyPI.

## Development

Using virtualenv is recommended for development.

```bash
virtualenv .
source ./bin/activate
```

### Development Dependencies

We use flake8 for checking both PEP-8 and common Python errors and invoke for
continuous integration.

```bash
pip install -U flake8
pip install -U invoke
```

You can list available build tasks with `inv -l`.

### Running Tests

```bash
inv test
```

### Linting

```bash
inv flake8
```

### Publishing to PyPI
You need pip, setuptools and wheel to publish to PyPI.

```
inv publish
```
