from . import static
from . import s3
from .log import log
import click
import json
import os

SYNC_TAG = [
    'content',
    'timestamp',
    'size'
]

ACL_CHOICE = [
    'private',
    'public-read',
    'public-read-write',
    'authenticated-read',
    'aws-exec-read',
    'bucket-owner-read',
    'bucket-owner-full-control'
]

@click.command()
@click.option('--local-folder', '-fl', required=True,
    help='Local folder to sync')
@click.option('--s3-folder', '-fs3', required=True,
    help='S3 folder to upload synced files')
@click.option('--allow-extension', '-ea', default=None,
    help='Allow only files with this extension. Example: .js')
@click.option('--ignore-extension', '-ei', default=None,
    help='Ignore files with this extension. Example: .ignore')
@click.option('--acl', type=click.Choice(ACL_CHOICE, case_sensitive=True),
    default=ACL_CHOICE[0],
    show_default=True,
    help='S3 ACL to apply to uploaded files')
@click.option('--bucket', required=True,
    help='S3 bucket to upload files')
@click.option('--bucket-region', required=True,
    help='S3 bucket region')
@click.option('--sync-strategy', '-ss',
    type=click.Choice(SYNC_TAG, case_sensitive=True),
    default=[SYNC_TAG[0]],
    show_default=True,
    multiple=True,
    help='Sync strategy to compose file name. Can be used multiple times')
@click.option('--manifest-file', default='manifest.json',
    help='Path of the manifest file that will be created',
    show_default=True)
@click.option('--header-cache-control', default=None,
    help='Header Cache-Control to apply to uploaded files. Ex: max-age=3600')
@click.option('--header-expires-delta', default=None, type=int,
    help='Time in seconds used in the header Expires, this will be applied to the uploaded files. Ex: 3600')
@click.option('--gzip', is_flag=True,
    help='Gzip content before upload')
@click.option('--fail-on-error', is_flag=True,
    help='Fail on error')
@click.option('--dry-run', is_flag=True,
    help='Dry run')
@click.option('--low-memory-mode', is_flag=True,
    help='When this flag is set, the script will check on every file if it exists on S3 before uploading it. '
    'If not present, the script will do one request to obtain the files contained in a folder '
    'and keep the list in memory. Enable this flag only if you have many files and '
    'you need a low memory footprint.')
@click.option('--verbose-level', '-v',
    type=click.Choice(['0', '1', '2']),
    default='2',
    help='Verbose level. 0: no output, 1: only resume, 2: full verbose')
def runner(bucket, bucket_region, local_folder, s3_folder, allow_extension,
        ignore_extension, acl, manifest_file, sync_strategy,
        header_cache_control, header_expires_delta, gzip, fail_on_error,
        dry_run, low_memory_mode, verbose_level):

    s3_client = s3.get_client(bucket_region)
    s3_folder = s3.normalize_folder_name(s3_folder)
    s3_folder_file_list = None
    manifest = {}
    summary = dict(total=0, skipped=0, uploaded=0, error=0)

    if not low_memory_mode:
        log(f'=> listing files from remote s3 bucket s3://{bucket}',
            verbose_level, 2)
        s3_folder_file_list = list(
            s3.list_folder_s3(s3_client, bucket, s3_folder))

    for file_path, manifest_path in static.scan_folder(local_folder,
            allow_extension, ignore_extension):
        summary['total'] += 1

        s3_key = static.compose_file_name(
            local_folder,
            s3_folder,
            file_path,
            header_cache_control=header_cache_control,
            header_expires_delta=header_expires_delta,
            use_gzip=gzip,
            use_content='content' in sync_strategy,
            use_size='size' in sync_strategy,
            use_timestamp='timestamp' in sync_strategy)

        if (s3_folder_file_list is not None and s3_key in s3_folder_file_list) or \
                (s3_folder_file_list is None and s3.check_key_exists(s3_client, bucket, s3_key)):
            manifest[manifest_path] = s3_key
            log(f'=> file exist, skip {manifest_path}', verbose_level, 2)
            summary['skipped'] += 1
            continue

        if not dry_run:
            success, err = s3.upload_file(s3_client, file_path, bucket,
                s3_key, acl,
                header_cache_control=header_cache_control,
                header_expires_delta=header_expires_delta,
                gzip=gzip)
        else:
            success, err = True, None

        if not success:
            if fail_on_error:
                raise Exception(err)
            log(f'=> error uploading file, not adding to manifest '
                'file: {err}', verbose_level, 2)
            summary['error'] += 1
        else:
            click.echo(f'=> file uploaded {manifest_path}')
            manifest[manifest_path] = s3_key
            summary['uploaded'] += 1

    log(f'=> writing manifest at {manifest_file}', verbose_level, 2)
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(manifest, indent=2))

    summary_text = (
        f'\n=> Resume\n'
        f'==> Total   : {summary["total"]}\n'
        f'==> Uploaded: {summary["uploaded"]}\n'
        f'==> Skipped : {summary["skipped"]}\n'
        f'==> Error   : {summary["error"]}'
    )
    log(summary_text, verbose_level, 1)


if __name__ == '__main__':
    runner()
