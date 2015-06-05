import unittest
import mock

import cloudstorage

from package_api import compute_package_name, get_cloudstorage_bucket, \
    get_cloudstorage_filename, exists, list_packages, list_package_names


test_files = [
    ("pytz-2012b.tar.bz2", "pytz"),
    ("pytz-2012b.tgz", "pytz"),
    ("pytz-2012b.ZIP", "pytz"),
    ("gevent-1.0b1.win32-py2.6.exe", "gevent"),
    ("gevent-1.0b1.win32-py2.7.msi", "gevent"),
    ("greenlet-0.3.4-py3.1-win-amd64.egg", "greenlet"),
    ("greenlet-0.3.4.win-amd64-py3.2.exe", "greenlet"),
    ("greenlet-0.3.4-py3.2-win32.egg", "greenlet"),
    ("greenlet-0.3.4-py2.7-linux-x86_64.egg", "greenlet"),
    ("pep8-0.6.0.zip", "pep8"),
    ("pytz-2012b.zip", "pytz"),
    ("ABC12-34_V1X-1.2.3.zip", "ABC12-34_V1X"),
    ("A100-200-XYZ-1.2.3.zip", "A100-200-XYZ"),
    ("flup-1.0.3.dev-20110405.tar.gz", "flup"),
    ("package-1.0.0-alpha.1.zip", "package"),
    ("package-1.3.7+build.11.e0f985a.zip", "package"),
    ("package-v1.8.1.301.ga0df26f.zip", "package"),
    ("package-2013.02.17.dev123.zip", "package"),
    ("package-20000101.zip", "package"),
    ("flup-123-1.0.3.dev-20110405.tar.gz", "flup-123"),
    ("package-123-1.0.0-alpha.1.zip", "package-123"),
    ("package-123-1.3.7+build.11.e0f985a.zip", "package-123"),
    ("package-123-v1.8.1.301.ga0df26f.zip", "package-123"),
    ("package-123-2013.02.17.dev123.zip", "package-123"),
    ("package-123-20000101.zip", "package-123"),
    ("pyelasticsearch-0.5-brainbot-1-20130712.zip", "pyelasticsearch"),
    ("pywin32-217-cp27-none-win32.whl", "pywin32"),
    ("pywin32-217-55-cp27-none-win32.whl", "pywin32"),
    ("pywin32-217.1-cp27-none-win32.whl", "pywin32"),
    ("package.zip", "package"),
]


class MockCloudstorageFile(object):

    def __init__(self, filename):
        self.filename = filename


class ComputePackageNameTests(unittest.TestCase):

    def test_computes_package_name(self):
        for file_result in test_files:
            self.assertEquals(compute_package_name(file_result[0]), file_result[1])


class GetCloudStorageBucketTests(unittest.TestCase):

    def test_prepends_dir_marker(self):
        self.assertEquals(get_cloudstorage_bucket('packages'), '/packages')

    def test_raises_if_dir_marker(self):
        with self.assertRaises(AssertionError):
            get_cloudstorage_bucket('/packages')


class GetCloudStorageFilenameTests(unittest.TestCase):

    def test_joins_to_bucket(self):
        self.assertEquals(get_cloudstorage_filename('packages', 'pytz-2012b.tar.bz2'), '/packages/pytz-2012b.tar.bz2')

    def test_raises_if_dir_marker(self):
        with self.assertRaises(AssertionError):
            get_cloudstorage_filename('packages', 'p/ytz-2012b.tar.bz2')


class ExistsTests(unittest.TestCase):

    def test_returns_True_if_exists(self):
        with mock.patch('cloudstorage.stat') as stat_method:
            stat_method.return_value = True
            self.assertTrue(exists('packages', 'pytz-2012b.tar.bz2'))

    def test_returns_False_if_not_exists(self):
        with mock.patch('cloudstorage.stat') as stat_method:
            stat_method.side_effect = cloudstorage.NotFoundError
            self.assertFalse(exists('packages', 'not-a-package.tar.bz2'))


class ListPackagesTests(unittest.TestCase):

    def test_returns_list_of_filenames(self):
        with mock.patch('cloudstorage.listbucket') as list_method:
            list_method.return_value = [MockCloudstorageFile(_file[0]) for _file in test_files]
            files = list_packages('packages')

            for _file in test_files:
                self.assertTrue(_file[0] in files)


class ListPackageNamesTests(unittest.TestCase):

    def test_returns_list_of_filenames(self):
        with mock.patch('cloudstorage.listbucket') as list_method:
            list_method.return_value = [MockCloudstorageFile(_file[0]) for _file in test_files]
            files = list_package_names('packages', )

            for _file in test_files:
                self.assertTrue(_file[1] in files)
