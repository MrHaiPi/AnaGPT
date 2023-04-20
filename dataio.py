import os


def copy_dir(src_path, target_path):
    try:
        if os.path.isdir(src_path) and os.path.isdir(target_path):
            filelist_src = os.listdir(src_path)
            for file in filelist_src:
                path = os.path.join(os.path.abspath(src_path), file)
                if os.path.isdir(path):
                    path1 = os.path.join(os.path.abspath(target_path), file)
                    if not os.path.exists(path1):
                        os.mkdir(path1)
                    copy_dir(path, path1)
                else:
                    with open(path, 'r', encoding="utf-8") as read_stream:
                        contents = read_stream.read()
                        path1 = os.path.join(target_path, file)
                        with open(path1, 'w', encoding="utf-8") as write_stream:
                            write_stream.write(contents)
        return True
    except Exception as e:
        print(e)
        return False
