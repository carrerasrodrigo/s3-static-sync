import hashlib
import os


def scan_folder(folder_path, allow_extension=None, ignore_extension=None):
    root_absolute_path = os.path.abspath(folder_path)
    for root, dir_list, file_list in os.walk(root_absolute_path):
        for file_name in file_list:
            if allow_extension is not None and not file_name.endswith(tuple(allow_extension)):
                continue

            if ignore_extension is not None and file_name.endswith(tuple(ignore_extension)):
                continue

            absolute_file_path = os.path.join(root, file_name)
            parent_containing_folder = os.path.dirname(
                os.path.abspath(root_absolute_path))
            relative_path = absolute_file_path[len(parent_containing_folder) + 1:]
            yield absolute_file_path, relative_path

def get_md5_content(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def get_timestamp(file_path):
    return os.path.getmtime(file_path)


def get_file_size(file_path):
    return os.path.getsize(file_path)


def compose_file_name(folder_path, s3_folder_path, file_path,
        header_cache_control, header_expires_delta,use_gzip, use_content,
        use_size, use_timestamp):
    file_name = os.path.basename(file_path)
    file_name_root, file_ext = os.path.splitext(file_name)

    key = f'{header_cache_control}-{header_expires_delta}-{use_gzip}'

    if use_content:
        key += get_md5_content(file_path)

    if use_size:
        key += str(get_file_size(file_path))

    if use_timestamp:
        key += str(get_timestamp(file_path))

    file_hash = hashlib.md5(key.encode()).hexdigest()
    absolute_folder_path = os.path.abspath(folder_path)
    new_file_name = f'{file_name_root}-{file_hash}{file_ext}'
    new_file_path = os.path.join(os.path.dirname(file_path),
        new_file_name)[len(absolute_folder_path):]
    return f'{s3_folder_path}{new_file_path}'
