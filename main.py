import ast
import os
from ana_gpt import Anagpt

if __name__ == '__main__':
    version = '1.0'

    file_name = os.path.join(os.getcwd(), 'version')
    if os.path.exists(file_name):
        f = open(file_name, 'r', encoding="utf-8")
        content = f.read()
        content = ast.literal_eval(content)
        f.close()
        version = content['version']
    else:
        print('Warning: No version file is found!')

    new_gpt = Anagpt(str(version))
    new_gpt.chat()

