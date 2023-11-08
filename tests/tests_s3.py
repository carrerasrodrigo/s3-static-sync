import os
import unittest

from moto import mock_s3

from s3_static_sync.s3 import (check_key_exists, get_client, guess_mime_type,
    gzip_content, list_folder_s3,
    normalize_folder_name, upload_file)


class TestS3Utils(unittest.TestCase):
    @mock_s3
    def setUp(self):
        # Set up the mocked S3 environment
        self.bucket = 'test-bucket'

        # Create a test file
        self.test_file_name = 'test.txt'
        with open(self.test_file_name, 'w') as f:
            f.write('Hello, World!')

    def _mock_client(self):
        self.client = get_client('us-east-1')
        self.client.create_bucket(Bucket=self.bucket)

    def test_normalize_folder_name(self):
        self.assertEqual(normalize_folder_name('/folder/'), 'folder')
        self.assertEqual(normalize_folder_name('folder/'), 'folder')
        self.assertEqual(normalize_folder_name('/folder'), 'folder')
        self.assertEqual(normalize_folder_name('folder'), 'folder')

    def test_guess_mime_type(self):
        self.assertEqual(guess_mime_type('test.txt'), 'text/plain')
        self.assertEqual(guess_mime_type('test'), 'binary/octet-stream')

    @mock_s3
    def test_upload_file(self):
        self._mock_client()
        success, err = upload_file(self.client, self.test_file_name, self.bucket, 'folder/test.txt', 'private')
        self.assertTrue(success)
        self.assertIsNone(err)

    def test_gzip_content(self):
        original_content = b"Hello, World!"
        gzipped_content = gzip_content(original_content)
        self.assertNotEqual(original_content, gzipped_content)

    @mock_s3
    def test_check_key_exists(self):
        self._mock_client()
        self.client.put_object(Bucket=self.bucket, Key='test.txt', Body='content')
        self.assertTrue(check_key_exists(self.client, self.bucket, 'test.txt'))
        self.assertFalse(check_key_exists(self.client, self.bucket, 'nonexistent.txt'))

    @mock_s3
    def test_list_folder_s3(self):
        self._mock_client()
        self.client.put_object(Bucket=self.bucket, Key='folder/test.txt', Body='content')
        keys = list_folder_s3(self.client, self.bucket, 'folder/')
        self.assertIn('folder/test.txt', keys)

    def tearDown(self):
        # Clean up code
        os.remove(self.test_file_name)
