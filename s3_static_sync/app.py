from . import static
from . import s3
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
def runner(bucket, bucket_region, local_folder, s3_folder, allow_extension,
        ignore_extension, acl,
        manifest_file, sync_strategy, header_cache_control,
        header_expires_delta, gzip, fail_on_error, dry_run, low_memory_mode):

    s3_client = s3.get_client(bucket_region)
    s3_folder = s3.normalize_folder_name(s3_folder)
    s3_folder_file_list = None
    manifest = {}

    if not low_memory_mode:
        click.echo(f'=> listing files from remote s3 bucket s3://{bucket}')
        s3_folder_file_list = s3.list_folder_s3(s3_client, bucket, s3_folder)

    for file_path in static.scan_folder(local_folder, allow_extension,
            ignore_extension):
        relative_file_path = os.path.join(
            file_path[0: len(local_folder)].split('/')[-1],
            file_path[len(local_folder) + 1:])

        _, s3_key = static.compose_file_name(
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
            manifest[relative_file_path] = s3_key
            click.echo(f'=> file exist, skip {relative_file_path}')
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
            click.echo(f'=> error uploading file, not adding to manifest '
                'file: {err}')
        else:
            click.echo(f'=> file uploaded {relative_file_path}')
            manifest[relative_file_path] = s3_key

    click.echo(f'=> writing manifest at {manifest_file}')
    with open(manifest_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(manifest))


if __name__ == '__main__':
    runner()
