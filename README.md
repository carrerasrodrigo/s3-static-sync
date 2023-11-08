# S3 Static Sync Tool

S3 Static Sync is a command-line tool designed to synchronize files from a local directory to an AWS S3 bucket with various customization options for file handling and upload preferences.

## Features

- Synchronization of a local directory with an S3 bucket.
- Selection of files to upload based on file extensions.
- Support for Access Control Lists (ACL) on S3.
- Customizable sync strategies with MD5 content, file size, and timestamps.
- Manifest file generation for tracking uploaded files.
- Options for gzip compression and dry-run mode.

## Requirements

- Python 3.7 or later.
- AWS CLI configured with appropriate permissions.
- `boto3` library for AWS operations.
- `click` library for CLI operations.

## Installation

Before using the S3 Static Sync tool, ensure you have Python and pip installed on your system. Install the necessary dependencies by running:

```
pip install git+https://github.com/carrerasrodrigo/s3-static-sync.git#egg=s3_static_sync
```

## Usage

To use the S3 Static Sync tool, you can invoke the script from the command line with the required options.

### Basic Command Structure

```
s3_static_sync [OPTIONS]
```

### Options

- `--local-folder, -fl` **(Required)**: Specify the local folder to sync.
- `--s3-folder, -fs3` **(Required)**: Set the S3 folder to upload synced files.
- `--allow-extension, -ea`: Allow only files with this extension. Example: `.js`.
- `--ignore-extension, -ei`: Ignore files with this extension. Example: `.ignore`.
- `--acl`: S3 ACL to apply to uploaded files. Defaults to 'private'.
- `--bucket` **(Required)**: S3 bucket to upload files.
- `--bucket-region` **(Required)**: S3 bucket region.
- `--sync-strategy, -ss`: Sync strategy to compose file name. Options: `content`, `timestamp`, `size`. Can be used multiple times.
- `--manifest-file`: File to write the manifest. Defaults to `manifest.json`.
- `--header-cache-control`: Header Cache-Control to apply to uploaded files.
- `--header-expires-delta`: Header Expires to apply to uploaded files in seconds.
- `--gzip`: Gzip content before upload.
- `--fail-on-error`: Fail on error during upload.
- `--dry-run`: Perform a trial run with no changes made.
- `--low-memory-mode`: Optimize memory usage for large sync operations.

### Examples

**Basic Sync:**

```
s3_static_sync -fl ./local-dir -fs3 s3-folder --bucket mybucket --bucket-region us-east-1
```

**Allow Specific Extensions:**

```
s3_static_sync -fl ./local-dir -fs3 s3-folder --bucket mybucket --bucket-region us-east-1 -ea .js -ea .css
```

**Ignore Specific Extensions:**

```
s3_static_sync -fl ./local-dir -fs3 s3-folder --bucket mybucket --bucket-region us-east-1 -ei .log
```

**Using ACL and Cache-Control:**

```
s3_static_sync -fl ./local-dir -fs3 s3-folder --acl public-read --bucket mybucket --bucket-region us-east-1 --header-cache-control max-age=3600
```

**Dry Run:**

```
s3_static_sync -fl ./local-dir -fs3 s3-folder --bucket mybucket --bucket-region us-east-1 --dry-run
```

### Test:
```
    python -m pytest tests/*
```
