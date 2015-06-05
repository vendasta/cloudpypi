"""
Manage PyPi packages backed by cloudstorage.
"""
import os
import sys
import re
import logging
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path[0:0] = [current_path, os.path.join(current_path, 'lib')]

import cloudstorage


_archive_suffix_re = re.compile(
    r"(\.zip|\.tar\.gz|\.tgz|\.tar\.bz3|-py[23]\.\d-.*|\.win-amd64-py[23]\.\d\..*|\.win32-py[23]\.\d\..*)$",  # noqa
    re.IGNORECASE)


wheel_file_re = re.compile(
    r"""^(?P<namever>(?P<name>.+?)-(?P<ver>\d.*?))
    ((-(?P<build>\d.*?))?-(?P<pyver>.+?)-(?P<abi>.+?)-(?P<plat>.+?)
    \.whl|\.dist-info)$""",
    re.VERBOSE)


def _compute_package_name_wheel(basename):
    m = wheel_file_re.match(basename)
    if not m:
        return None, None
    return m.group("name")


def compute_package_name(path):
    path = os.path.basename(path)
    if path.endswith(".whl"):
        return _compute_package_name_wheel(path)

    path = _archive_suffix_re.sub('', path)
    if '-' not in path:
        name, _ = path, ''
    elif path.count('-') == 1:
        name, _ = path.split('-', 1)
    elif '.' not in path:
        name, _ = path.rsplit('-', 1)
    else:
        parts = re.split(r'-(?=(?i)v?\d+[\.a-z])', path)
        name = '-'.join(parts[:-1])
    return name


def get_cloudstorage_bucket(bucket):
    assert "/" not in bucket
    return '/' + bucket


def get_cloudstorage_filename(bucket, filename):
    assert "/" not in filename
    return "%s/%s" % (get_cloudstorage_bucket(bucket), filename)


def exists(bucket, filename):
    """
    Return True if the filename exists in cloudstorage. False otherwise.
    """
    destination = get_cloudstorage_filename(bucket, filename)
    try:
        cloudstorage.stat(destination)
        return True
    except cloudstorage.NotFoundError:
        return False


def write(bucket, filename, data):
    """
    Write data to filename in the configured cloudstorage bucket.
    """
    destination = get_cloudstorage_filename(bucket, filename)
    cloudstorage_file = cloudstorage.open(destination,
                                          'w',
                                          content_type='application/x-gzip')
    cloudstorage_file.write(data)
    cloudstorage_file.close()
    logging.info("Stored package: %s", filename)


def read(bucket, filename):
    """
    Read and return data from filename.
    """
    filename = get_cloudstorage_filename(bucket, filename)
    gcs_file = cloudstorage.open(filename)
    data = gcs_file.read()
    gcs_file.close()
    return data


def list_packages(bucket, prefix=""):
    """
    Return all packages and their versions.
    """
    path_prefix = get_cloudstorage_filename(bucket, prefix)

    stats = cloudstorage.listbucket(path_prefix)
    if prefix:
        packages = [os.path.basename(s.filename)
                    for s in stats
                    if prefix == compute_package_name(s.filename)]
    else:
        packages = [os.path.basename(s.filename) for s in stats]
    logging.info("list_packages with prefix %s:\n%s", prefix, packages)
    return packages


def list_package_names(bucket, prefix=""):
    """
    Return the short name of all packages, collapsing versions together.
    """
    package_names = set()
    eggs = set()

    packages = [compute_package_name(package)
                for package in list_packages(bucket, prefix=prefix)]
    for package in packages:
        if package.endswith(".egg"):
            eggs.add(package)
        else:
            package_names.add(package)

    all_packages = package_names.union(eggs)
    logging.info("list_package_names with prefix %s:\n%s",
                 prefix, all_packages)
    return [os.path.basename(package) for package in all_packages]
