import json
import os
import unittest
from unittest.mock import patch

import boto3
from click.testing import CliRunner
from moto import mock_s3

from s3_static_sync.app import runner


class TestRunnerCommand(unittest.TestCase):

    @mock_s3
    def setUp(self):
        self.runner = CliRunner()
        self.mock_bucket = 'mock-bucket'
        self.mock_region = 'us-east-1'
        self.mock_local_folder = '/tmp/mock_local_folder'
        self.mock_s3_folder = 'mock_s3_folder'

        if not os.path.exists(self.mock_local_folder):
            os.makedirs(self.mock_local_folder)

        self.test_file_path = os.path.join(self.mock_local_folder, 'test.txt')
        with open(self.test_file_path, 'w') as f:
            f.write('Hello, World!')

    @mock_s3
    def test_runner_without_low_memory(self):
        self.s3 = boto3.resource('s3', region_name=self.mock_region)
        self.s3.create_bucket(Bucket=self.mock_bucket)

        result = self.runner.invoke(runner, [
            '--bucket', self.mock_bucket,
            '--bucket-region', self.mock_region,
            '--local-folder', self.mock_local_folder,
            '--s3-folder', self.mock_s3_folder,
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('file uploaded mock_local_folder/test.txt', result.output)

        result = self.runner.invoke(runner, [
            '--bucket', self.mock_bucket,
            '--bucket-region', self.mock_region,
            '--local-folder', self.mock_local_folder,
            '--s3-folder', self.mock_s3_folder,
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('file exist', result.output)

    @mock_s3
    def test_runner_with_low_memory(self):
        self.s3 = boto3.resource('s3', region_name=self.mock_region)
        self.s3.create_bucket(Bucket=self.mock_bucket)

        result = self.runner.invoke(runner, [
            '--bucket', self.mock_bucket,
            '--bucket-region', self.mock_region,
            '--local-folder', self.mock_local_folder,
            '--s3-folder', self.mock_s3_folder,
            '--low-memory-mode',
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('file uploaded mock_local_folder/test.txt', result.output)

        result = self.runner.invoke(runner, [
            '--bucket', self.mock_bucket,
            '--bucket-region', self.mock_region,
            '--local-folder', self.mock_local_folder,
            '--s3-folder', self.mock_s3_folder,
            '--low-memory-mode',
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('file exist', result.output)

    @mock_s3
    def test_runner_gzip(self):
        self.s3 = boto3.resource('s3', region_name=self.mock_region)
        self.s3.create_bucket(Bucket=self.mock_bucket)

        with patch('s3_static_sync.s3.gzip_content', return_value='xx') as fn:
            result = self.runner.invoke(runner, [
                '--bucket', self.mock_bucket,
                '--bucket-region', self.mock_region,
                '--local-folder', self.mock_local_folder,
                '--s3-folder', self.mock_s3_folder,
                '--gzip',
            ])
            self.assertTrue(fn.called)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('file uploaded mock_local_folder/test.txt', result.output)

    @mock_s3
    def test_runner_manifest(self):
        self.s3 = boto3.resource('s3', region_name=self.mock_region)
        self.s3.create_bucket(Bucket=self.mock_bucket)

        result = self.runner.invoke(runner, [
            '--bucket', self.mock_bucket,
            '--bucket-region', self.mock_region,
            '--local-folder', self.mock_local_folder,
            '--s3-folder', self.mock_s3_folder,
            '--manifest-file', 'x.json'
        ])
        self.assertEqual(result.exit_code, 0)
        with open('x.json') as f:
            self.assertEqual(json.loads(f.read())['mock_local_folder/test.txt'],
                'mock_s3_folder/test-01a5f7b30cd86a9b2d70f80d2649ceac.txt')
        os.remove('x.json')

    @mock_s3
    def test_runner_sync_strategy(self):
        self.s3 = boto3.resource('s3', region_name=self.mock_region)
        self.s3.create_bucket(Bucket=self.mock_bucket)

        with patch('s3_static_sync.static.get_md5_content', return_value='x') as fn:
            with patch('s3_static_sync.static.get_timestamp', return_value='x') as fn2:
                with patch('s3_static_sync.static.get_file_size', return_value='x') as fn3:
                    result = self.runner.invoke(runner, [
                        '--bucket', self.mock_bucket,
                        '--bucket-region', self.mock_region,
                        '--local-folder', self.mock_local_folder,
                        '--s3-folder', self.mock_s3_folder,
                        '-ss', 'content',
                        '-ss', 'timestamp',
                        '-ss', 'size'
                    ])
                    self.assertTrue(fn.called)
                    self.assertTrue(fn2.called)
                    self.assertTrue(fn3.called)
        self.assertEqual(result.exit_code, 0)

    @mock_s3
    def test_runner_dry_run(self):
        # Setup mock S3
        self.s3 = boto3.resource('s3', region_name=self.mock_region)
        self.s3.create_bucket(Bucket=self.mock_bucket)

        result = self.runner.invoke(runner, [
            '--bucket', self.mock_bucket,
            '--bucket-region', self.mock_region,
            '--local-folder', self.mock_local_folder,
            '--s3-folder', self.mock_s3_folder,
            '--dry-run'
        ])
        self.assertEqual(result.exit_code, 0)

    def tearDown(self):
        os.remove(self.test_file_path)
        if os.path.exists(self.mock_local_folder):
            os.rmdir(self.mock_local_folder)
