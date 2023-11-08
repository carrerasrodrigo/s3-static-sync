import hashlib
import os


def scan_folder(folder_path, allow_extension=None, ignore_extension=None):
    for root, dir_list, file_list in os.walk(folder_path):
        for file_name in file_list:
            if allow_extension is not None and not file_name.endswith(tuple(allow_extension)):
                continue

            if ignore_extension is not None and file_name.endswith(tuple(ignore_extension)):
                continue
            yield os.path.join(root, file_name)


def get_md5_content(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def get_timestamp(file_path):
    return os.path.getmtime(file_path)


def get_file_size(file_path):
    return os.path.getsize(file_path)


def compose_file_name(folder_path, s3_folder_path,
        file_path,
        header_cache_control,
        header_expires_delta,
        use_gzip, use_content, use_size, use_timestamp):

    root, file_ext = os.path.splitext(file_path)
    file_name = root.split('/')[-1]

    key = f'{header_cache_control}-{header_expires_delta}-{use_gzip}'

    if use_content:
        key += get_md5_content(file_path)

    if use_size:
        key += str(get_file_size(file_path))

    if use_timestamp:
        key += str(get_timestamp(file_path))

    file_hash = hashlib.md5(key.encode()).hexdigest()
    new_file_name = f'{file_name}-{file_hash}{file_ext}'
    new_file_path = os.path.join(os.path.dirname(file_path),
        new_file_name)[len(folder_path):]
    return new_file_name, f'{s3_folder_path}{new_file_path}'
