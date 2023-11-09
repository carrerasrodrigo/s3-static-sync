import hashlib
import os
import unittest

from s3_static_sync.static import (compose_file_name, get_file_size, get_md5_content,
    get_timestamp, scan_folder)


class TestFileUtils(unittest.TestCase):
    def setUp(self):
        # Setup code if necessary, like creating a test directory and files
        os.makedirs('test_folder', exist_ok=True)
        with open('test_folder/test_file.txt', 'w') as f:
            f.write('Hello, World!')

        with open('test_folder/test_file.jpg', 'w') as f:
            f.write('Hello, World!')
        self.folder_path = os.path.abspath('test_folder')
        self.test_file_path = os.path.join(self.folder_path, 'test_file.txt')
        self.test_file_path2 = os.path.join(self.folder_path, 'test_file.jpg')

    def test_scan_folder(self):
        # Test that scanning the folder returns the correct files
        file_list = list(scan_folder(self.folder_path))

        item = list(filter(lambda x: x[0].endswith('test_file.txt'),
            file_list))[0]

        self.assertEqual(len(file_list), 2)
        self.assertIn(self.test_file_path, item)
        self.assertEqual(item[0], os.path.abspath(self.test_file_path))

        file_list = list(scan_folder('test_folder'))
        self.assertEqual(len(file_list), 2)
        self.assertIn(self.test_file_path, item)
        self.assertEqual(item[0], os.path.abspath(self.test_file_path))

    def test_scan_folder_with_allow_extension(self):
        # Test that only file_list with allowed extensions are returned
        file_list = list(scan_folder(self.folder_path,
            allow_extension=['.txt']))
        self.assertEqual(len(list(filter(lambda x: x[0].endswith(self.test_file_path),
            file_list))), 1)
        self.assertEqual(len(list(filter(lambda x: x[0].endswith(self.test_file_path2),
            file_list))), 0)

    def test_scan_folder_with_ignore_extension(self):
        # Test that file_list with ignored extensions are not returned
        file_list = list(scan_folder(self.folder_path,
            ignore_extension=['.txt']))
        self.assertEqual(len(list(filter(lambda x: x[0].endswith(self.test_file_path),
            file_list))), 0)

    def test_get_md5_content(self):
        # Test that MD5 hash is correct
        md5_hash = get_md5_content(self.test_file_path)
        self.assertEqual(md5_hash, hashlib.md5(b'Hello, World!').hexdigest())

    def test_get_timestamp(self):
        # Test that the timestamp is correct
        timestamp = get_timestamp(self.test_file_path)
        self.assertTrue(isinstance(timestamp, float))

    def test_get_file_size(self):
        # Test that the file size is correct
        size = get_file_size(self.test_file_path)
        self.assertEqual(size, 13)

    def test_compose_file_name(self):
        # Test that the composed file name is correct
        composed_path = compose_file_name(
            folder_path=self.folder_path,
            s3_folder_path='s3_folder_path',
            file_path=self.test_file_path,
            header_cache_control='max-age=3600',
            header_expires_delta='3600',
            use_gzip=False,
            use_content=True,
            use_size=True,
            use_timestamp=True
        )
        self.assertTrue(composed_path.startswith('s3_folder_path'))

    def tearDown(self):
        # Clean up code, remove test directory and file_list after tests
        os.remove(self.test_file_path)
        os.remove(self.test_file_path2)
        os.rmdir(self.folder_path)
