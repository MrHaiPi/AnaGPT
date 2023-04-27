import importlib

def get_conf(*args):
    # 建议您复制一个config_private.py放自己的秘密, 如API和代理网址, 避免不小心传github被别人看到
    res = []
    for arg in args:
        try: r = getattr(importlib.import_module('models.chat_gpt.config_private'), arg)
        except: r = getattr(importlib.import_module('models.chat_gpt.config'), arg)
        res.append(r)
        # 在读取API_KEY时，检查一下是不是忘了改config
        if arg == 'API_KEY' and len(r) != 51:
            assert False, "正确的API_KEY密钥是51位，请在config文件中修改API密钥, 添加海外代理之后再运行。" + \
                        "（如果您刚更新过代码，请确保旧版config_private文件中没有遗留任何新增键值）"
    return res


def write_results_to_file(history, file_name=None):
    """
        将对话记录history以Markdown格式写入文件中。如果没有指定文件名，则使用当前时间生成文件名。
    """
    import os, time
    if file_name is None:
        # file_name = time.strftime("chatGPT分析报告%Y-%m-%d-%H-%M-%S", time.localtime()) + '.md'
        file_name = 'chatGPT分析报告' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.md'
    os.makedirs('./gpt_log/', exist_ok=True)
    with open(f'./gpt_log/{file_name}', 'w', encoding = 'utf8') as f:
        f.write('# chat_gpt 分析报告\n')
        for i, content in enumerate(history):
            if i%2==0: f.write('## ')
            f.write(content)
            f.write('\n\n')
    res = '以上材料已经被写入' + os.path.abspath(f'./gpt_log/{file_name}')
    print(res)
    return res


def regular_txt_to_markdown(text):
    """
        将普通文本转换为Markdown格式的文本。
    """
    text = text.replace('\n', '\n\n')
    text = text.replace('\n\n\n', '\n\n')
    text = text.replace('\n\n\n', '\n\n')
    return text