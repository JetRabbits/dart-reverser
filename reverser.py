import regex as re
import os
import argparse

pattern = b'package:(\w[0-9a-zA-Z-_/.]+)[^file:///]+file:///[A-Z]?:?/?([0-9a-zA-Z-_/.]+dart)..([^\x00]+)\x00'
package_group = 1
file_group = 2
content_group = 3


def run_app(kernel: str):
    with open(kernel, 'rb') as dart_kernel:
        read_buffer = b''
        files_section_is_found = False

        while chunk := dart_kernel.read(1024):
            read_buffer = read_buffer + chunk
            if re.search(b'\x11\x11\x11\x11\x11\x10\x0D', read_buffer) is not None:
                print('End file section')
                break
            if not files_section_is_found:
                files_section_is_found = re.search(pattern,
                                                   read_buffer) is not None
                # control OOM
                if not files_section_is_found and len(read_buffer) > 1024:
                    read_buffer = read_buffer[1024:]
            else:
                search_result = re.search(pattern,
                                          read_buffer)

                if search_result is not None:
                    resource_reference = search_result.group(file_group)
                    file_path = prepare_file_path(resource_reference)
                    # Пишем данные в файл
                    file_data = search_result.group(content_group)[:-1]
                    write_data_to_file(file_path, file_data)
                    read_buffer = read_buffer[search_result.regs[content_group][1]:]


def prepare_file_path(resource_string:bytearray):
    resource_path = os.path.normpath(resource_string.replace(b':', b'').decode())
    dir_path = os.path.join(os.path.curdir, 'extracted', os.path.dirname(resource_path))
    print(dir_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    file_path = os.path.join(dir_path, os.path.basename(resource_path))
    return file_path


def write_data_to_file(file_path: str, data: bytearray):
    with open(file_path, 'wb') as file:
        print('writing to file %s' % file_path)
        file.write(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='reverser', description="Dart kernel blob source files extractor")
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('kernel', type=argparse.FileType('rb'), default='kernel_blob.bin',
                        help='path to kernel_blob.bin')
    args = parser.parse_args()
    run_app(kernel=args.kernel.name)
