import os

import PyPDF2
import docx


def get_chat_files_content(folder_path, segment_length=3000):
    try:

        # 存储所有文件的文本内容
        all_content = []

        # 遍历文件夹中的所有文件
        for file_name in os.listdir(folder_path):
            # 如果文件是文本文件
            if file_name.endswith('.txt'):
                with open(os.path.join(folder_path, file_name), 'r', encoding="utf-8") as f:
                    content = f.read()
                    # 将文本内容按照分段长度进行分段
                    segments = [content[i:i+segment_length] for i in range(0, len(content), segment_length)]
                    all_content += segments
            # 如果文件是Word文档
            elif file_name.endswith('.docx'):
                doc = docx.Document(os.path.join(folder_path, file_name))
                content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                # 将文本内容按照分段长度进行分段
                segments = [content[i:i+segment_length] for i in range(0, len(content), segment_length)]
                all_content += segments
            # 如果文件是PDF文件
            elif file_name.endswith('.pdf'):
                with open(os.path.join(folder_path, file_name), 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    content = '\n'.join([reader.pages[i].extract_text() for i in range(len(reader.pages))])
                    # 将文本内容按照分段长度进行分段
                    segments = [content[i:i+segment_length] for i in range(0, len(content), segment_length)]
                    all_content += segments

        return all_content
    except Exception as e:
        print(e)
        return None
