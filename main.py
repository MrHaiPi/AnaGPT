import os
from ana_gpt import Anagpt

if __name__ == '__main__':
    version = '1.0'

    file_name = os.path.join(os.getcwd(), 'version')
    if os.path.exists(file_name):
        f = open(file_name, 'r', encoding="utf-8")
        content = f.read()
        f.close()
        start_index = content.find('version') + len('version') + 3
        end_index = content.find('version') + len('version') + 6
        version = content[start_index:end_index]
    else:
        print('Warning: No version file is found!')
    new_gpt = Anagpt(version)
    new_gpt.chat()

