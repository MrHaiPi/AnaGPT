# -*- coding:utf-8 -*-
import os.path
from models.chat_gpt.chat_gpt import chat_gpt

MODEL_LIST = \
            {
                'gpt-3.5-turbo (chatGPT API, EN/CN...)': "chat_gpt('gpt-3.5-turbo')",
                'gpt-4 (chatGPT API, EN/CN...)': "my_chat_gpt('gpt-4')",

                'chinese-alpaca-7b-int4 (llama.cpp CPU 6G RAM, EN/CN)': "chinese_alpaca('chinese-alpaca-7b-int4')",
                'chinese-alpaca-13b-int4 (llama.cpp CPU 10G RAM, EN/CN)': "chinese_alpaca('chinese-alpaca-13b-int4')",

                'vicuna-7b-int4 (llama.cpp CPU 6G RAM, EN/poor CN)': "vicuna('vicuna-7b-int4')",
                'vicuna-13b-int4 (llama.cpp CPU 10G RAM, EN/poor CN)': "vicuna('vicuna-13b-int4')",

                'chinese-chat-llama-7b-int4 (llama.cpp CPU 6G RAM, EN/CN)': "chinese_chat_llama('chinese-chat-llama-7b-int4')",

                'chatglm-6b-int4 (CPU 6G RAM, EN/CN)': "chatglm('chatglm-6b-int4', device='cpu')",
                'chatglm-6b-int4 (GPU 6G VRAM, EN/CN)': "chatglm('chatglm-6b-int4', device='cuda')",

                'gpt-for-all-int4 (llama.cpp CPU 6G RAM, EN)': "gpt_for_all('gpt-for-all-int4')",
            }


class GPT:
    def __init__(self, model_name=list(MODEL_LIST.keys())[0]):
        self.name = model_name
        self.model = None
        self.tokenizer = None
        self.windows_length = int(1024 * 10)

        self.predict = eval('self.' + MODEL_LIST[model_name])

    def load_model(self, model_path, device):
        from transformers import AutoTokenizer, AutoModel
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = None
        if device == 'cpu':
            model = AutoModel.from_pretrained(model_path, trust_remote_code=True).float()
            model = model.quantize(bits=4, kernel_file=os.path.join(model_path, 'quantization_kernels_parallel.so'))
        elif device == 'cuda' or device == 'gpu':
            model = AutoModel.from_pretrained(model_path, trust_remote_code=True).half().cuda()
        model = model.eval()

        self.model = model
        self.tokenizer = tokenizer

    def load_ggml_model(self, model_path):
        from llama_cpp import Llama

        self.model = Llama(model_path=model_path,
                           n_ctx=self.windows_length,
                           use_mlock=False)

    def predict(self, prompt, system_prompt='', temperature=0.8, stream=True, chatbot=[], history=[]):
        system_prompt = "Below is an instruction/prompt that describes a task. Write a response that appropriately " \
                        "completes the request. \n" + system_prompt

        system_prompt += '\n'

        statusDisplay = ''

        user_state = "Human:"
        bot_state = "Assistant:"
        history.append(prompt)
        history.append('')
        chatbot.append((prompt, ''))

        all_prompt = system_prompt
        for i, message in enumerate(history):
            if i % 2 == 0:
                all_prompt += user_state + message
            else:
                all_prompt += bot_state + message

        stop_string_list = [user_state, bot_state, user_state[:-1] + '：', bot_state[:-1] + '：', '###', 'User:', 'User：']

        if not self.tokenizer:
            flow = self.model(all_prompt, temperature=temperature, max_tokens=1024,
                              stop=stop_string_list,
                              echo=True, stream=stream)
            response = ''
            for chunks in flow:
                ans = chunks['choices'][0]['text']
                response += ans
                chatbot[0] = (chatbot[0][0], response)
                history[-1] = chatbot[0][-1]
                yield chatbot, history, statusDisplay
        else:
            history_temp = []
            for response, history_temp in self.model.stream_chat(self.tokenizer, all_prompt, max_length=self.windows_length,
                                                                 temperature=temperature,
                                                                 history=history_temp):
                if response in stop_string_list:
                    chatbot[0] = (chatbot[0][0], '\n')
                    break
                else:
                    chatbot[0] = (chatbot[0][0], response)

                history[-1] = chatbot[0][-1]
                yield chatbot, history, statusDisplay

    def chat_gpt(self, model_name):
        return chat_gpt(model_name).predict

    def chinese_alpaca(self, model_name):
        path = os.path.join('models', 'chinese_alpaca', model_name, 'ggml-model-q4_0.bin')
        self.load_ggml_model(path)
        return self.predict

    def vicuna(self, model_name):
        path = os.path.join('models', 'vicuna', model_name, 'ggml-vicuna-4bit-rev1.bin')
        self.load_ggml_model(path)
        return self.predict

    def chinese_chat_llama(self, model_name):
        path = os.path.join('models', 'chinese_chat_llama', model_name, 'chatllama-ggml-q4_0.bin')
        self.load_ggml_model(path)
        return self.predict

    def chatglm(self, model_name, device):
        path = os.path.join('models', 'chatglm', model_name)
        self.load_model(path, device)
        return self.predict

    def gpt_for_all(self, model_name):
        path = os.path.join('models', 'gpt_for_all', model_name, 'ggml-gpt4all-q4_0.bin')
        self.load_ggml_model(path)
        return self.predict



