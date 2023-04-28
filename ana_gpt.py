import ast
import atexit
import csv
import gc
import json
import os
import platform
import re
import shutil
import signal
import sys
import threading
import time
from io import StringIO
from subprocess import run

import keyboard
import requests
import win32api
import win32con
from win32com import client

from chat_files import get_chat_files_content
from dataio import copy_dir
import gpt
from models.chat_gpt.toolbox import get_conf
from gpt import GPT
from multi_input import MultiInputInCmd


class Anagpt:
    def __init__(self, version):
        self.envs_root_path = os.path.join(os.getcwd(), 'envs')
        if not os.path.exists(self.envs_root_path):
            os.makedirs(self.envs_root_path)
        self.pkgs_root_path = os.path.join(os.getcwd(), 'pkgs')
        if not os.path.exists(self.pkgs_root_path):
            os.makedirs(self.pkgs_root_path)
        self.sys_root_path = os.path.join(os.getcwd(), 'system')
        if not os.path.exists(self.sys_root_path):
            os.makedirs(self.sys_root_path)
        self.history_root_path = os.path.join(os.getcwd(), 'history')
        if not os.path.exists(self.history_root_path):
            os.makedirs(self.history_root_path)
        self.files_root_path = os.path.join(os.getcwd(), 'files')
        if not os.path.exists(self.files_root_path):
            os.makedirs(self.files_root_path)

        self.version = 'AnaGPT ' + version
        self.base_env_name = 'base'
        self.history = []
        self.history_name = None
        self.chat_history_list = []
        self.cur_env_name = self.base_env_name
        self.system_prompt = None
        self.chat_model = GPT()
        self.cancel_output = False

        self.load_last_model_env_name_content()
        self.load_chat_history_list()
        self.commands, self.keyboards = self.get_all_command_keyboards()
        self.register_fun()

        self.clear_screen_and_history()

    def get_all_command_keyboards(self):
        def show_env_list():
            self.show_env_list()
            print('')

        def show_env_list_des():
            self.show_env_list(is_describe=True)
            print('')

        def create_new_env(cmd):
            parameters = cmd.split(' ')
            env_name = parameters[3]
            if '-clone' in parameters:
                clone_env_name = parameters[5]
                self.create_new_env(env_name, clone_env_name)
            else:
                self.create_new_env(env_name)
            print('')

        def activate_env(cmd):
            parameter = cmd.split(' ')[-1]
            self.activate_env(parameter)
            print('')

        def deactivate_env():
            self.deactivate_env()

        def confirm_and_remove_env(cmd):
            parameter = cmd.split(' ')[-1]
            confirm = input('Are you sure? y/n:')
            if confirm == 'y' or confirm == 'Y' or confirm == 'yes' or confirm == 'yes':
                self.remove_env(parameter)
            else:
                self.show_cmd_canceled_mess(cmd)
            print('')

        def show_cur_env_pkg_list():
            self.show_cur_env_pkg_list()
            print('')

        def clear_screen_and_history():
            self.clear_screen_and_history()

        def show_help_content():
            content = self.get_function_body(__file__, 'get_all_command_keyboards')
            prompt = "Understand the given information aboved and then answer the question:" \
                     "'What commands and keyboards can users enter or push'. \n " \
                     "You should explain the functions and list all of the commands and keyboards one by one. " \
                     "Please note that you must understand all the content before answering the question, and " \
                     "cannot just only focus on the commands and keyboards variables. " \
                     "For all the commands containing '*', you should also clarify their specific meanings and " \
                     "provide examples for use just behind the explanation of the commands"
            message = content + f'\n' + prompt

            self.chat_flow(message=message,
                           history=[],
                           system_prompt='',
                           temperature=0.1)

        def show_named_help_content(cmd):
            help_content = self.get_function_body(__file__, 'get_all_command_keyboards')

            parameter = cmd.split(' ')[3:]

            prompt = "\n Please provide instructions on how to use the {} command based on the above content.".format(parameter)
            message = '"' + help_content + '"' + prompt

            self.chat_flow(message=message,
                           history=[],
                           system_prompt='',
                           temperature=0.1)

        def show_version():
            self.show_version()
            print('')

        def install_package(cmd):
            parameters = cmd.split(' ')

            # download form source url if there is no -c command
            if '-c' not in parameters:
                pkg_name = parameters[parameters.index('-n') + 1]
                dir_path = self.pkgs_root_path
                files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
                         and not f.startswith('.') and not f.endswith('~')]
                if pkg_name not in files:
                    print('not find "{}" pkg from {}'.format(pkg_name, dir_path))
                else:
                    f = open(os.path.join(dir_path, pkg_name), "r", encoding="utf-8")
                    pkg_content = f.read()
                    f.close()
                    self.create_new_pkg(pkg_name, pkg_content)

            # customize the content of pkgs
            elif '-c' in parameters:
                pkg_name = parameters[parameters.index('-n') + 1]
                pkg_content = parameters[parameters.index('-c') + 1]

                self.create_new_pkg(pkg_name, pkg_content)
            else:
                self.show_cmd_not_supported_mess(cmd)
            print('')

        def confirm_and_remove_pkg(cmd):
            parameters = cmd.split(' ')
            pkg_name = parameters[-1]

            dir_path = os.path.join(self.envs_root_path, self.cur_env_name)
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
                     and not f.startswith('.') and not f.endswith('~')]

            if pkg_name not in files:
                print('"' + pkg_name + '"' + 'is not in the current environment!')
            else:
                confirm = input('Are you sure? y/n:')
                if confirm == 'y' or confirm == 'Y' or confirm == 'yes' or confirm == 'yes':
                    print(self.remove_pkg(pkg_name))
                    self.activate_env(self.cur_env_name)
                else:
                    self.show_cmd_canceled_mess(cmd)
            print('')

        def update_local_pkgs():
            self.update_local_pkgs()
            print('')

        def show_local_pkgs_list(cmd):
            parameters = cmd.split(' ')

            if '-des' in parameters:
                pkg_name_to_des = parameters[-1]
                self.show_local_pkgs_list(pkg_name_to_des)
            else:
                self.show_local_pkgs_list()

            print('')
            print('Try "gpt install -n pkg_name" to install you favorite pkg in the current environment.')
            print('')

        def show_chat_history_list():
            self.show_chat_history_list()
            print('')

        def recover_chat_history():
            print('Which history do you want to recover:')
            self.show_chat_history_list()
            select_history_index = 0
            while True:
                try:
                    select_history_index = int(input('Input the index:')) - 1
                except Exception as e:
                    print(e)
                    continue
                if select_history_index < len(self.chat_history_list) and select_history_index >= 0:
                    break

            self.load_chat_history(self.chat_history_list[select_history_index])
            self.show_chat_history()
            print('')

        def confirm_and_remove_history(cmd):
            parameters = cmd.split(' ')

            confirm = input('Are you sure? y/n:')
            if confirm == 'y' or confirm == 'Y' or confirm == 'yes' or confirm == 'yes':
                history_name = parameters[-1]
                self.remove_history(history_name)
            else:
                self.show_cmd_canceled_mess(cmd)
            print('')

        def confirm_and_remove_all_history(cmd):
            confirm = input('Are you sure? y/n:')
            if confirm == 'y' or confirm == 'Y' or confirm == 'yes' or confirm == 'yes':
                for history_name in self.chat_history_list:
                    self.remove_history(history_name)
            else:
                self.show_cmd_canceled_mess(cmd)
            print('')

        def chat_based_given_files(cmd):
            parameters = cmd.split(' ')

            if '-p' not in parameters:
                message = ''.join(parameters[2:])
                files_path = self.files_root_path
                files_content = get_chat_files_content(files_path)
            elif '-p' in parameters:
                message = ''.join(parameters[4:])
                files_path = ''.join(parameters[3])
                files_content = get_chat_files_content(files_path)
            else:
                self.show_cmd_not_supported_mess(cmd)
                print('')
                return

            prompt = \
                "We have provided context information below: \n" \
                "---------------------\n" \
                "{}\n" \
                "---------------------\n" \
                "Given this information, Please answer my question in the same language that I used to ask you.\n" \
                "Please answer the question: {}\n"

            ans = []
            for content in files_content:
                message = prompt.format(content, message)

                ans.append(self.chat_flow(message=message,
                                          history=self.history,
                                          system_prompt=self.system_prompt,
                                          temperature=0.8,
                                          is_print=False))

            ans = ''.join(ans)
            message = prompt.format(ans, message)

            self.chat_flow(message=message,
                           history=self.history,
                           system_prompt=self.system_prompt,
                           temperature=0.8,
                           is_print=True)

        def edit_cur_env_pkg_content():
            dir_path = os.path.join(self.envs_root_path, self.cur_env_name)
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
                     and not f.startswith('.') and not f.endswith('~')]

            print('Which pkg do you want to edit:\n')
            self.show_cur_env_pkg_list()
            print('')

            while True:
                try:
                    select_pkg_index = int(input('Input the index:')) - 1
                except Exception as e:
                    print(e)
                    continue
                if select_pkg_index < len(files) and select_pkg_index >= 0:
                    break

            select_pkg_name = files[select_pkg_index]
            state = self.run_cmd('vim ' + os.path.join(dir_path, select_pkg_name))
            if state.returncode != 0:
                print('You should install the vim command, check here: https://github.com/vim/vim-win32-installer/releases')
            print('')

        def create_shortcut():
            if platform.system() == "Windows":
                self.create_shortcut()
                print('Successfully!')
            else:
                print('{} system is not supported!'.format(platform.system()))
            print('')

        def show_chat_model_list():
            self.show_chat_model_list()
            print('')

        def change_chat_model():
            print('Which chat model do you want to change:\n')
            show_chat_model_list()

            model_list_dic = gpt.MODEL_LIST

            select_index = 0
            while True:
                try:
                    select_index = int(input('Input the index:')) - 1
                except Exception as e:
                    print(e)
                    continue
                if select_index < len(model_list_dic) and select_index >= 0:
                    break
            model_name = list(model_list_dic.keys())[select_index]
            self.change_chat_model(model_name)
            self.clear_screen_and_history()

        commands = {

            # handle system
            'gpt -version': lambda cmd: show_version(),

            # handle env
            'gpt env list': lambda cmd: show_env_list(),
            'gpt env list -des': lambda cmd: show_env_list_des(),
            'gpt create -n *': lambda cmd: create_new_env(cmd),
            'gpt activate *': lambda cmd: activate_env(cmd),
            'gpt deactivate': lambda cmd: deactivate_env(),
            'gpt remove -n *': lambda cmd: confirm_and_remove_env(cmd),

            # help
            'gpt help': lambda cmd: show_help_content(),
            'gpt help -n *': lambda cmd: show_named_help_content(cmd),

            # handle installed package
            'gpt install -n *': lambda cmd: install_package(cmd),
            'gpt uninstall -n *': lambda cmd: confirm_and_remove_pkg(cmd),
            'gpt list': lambda cmd: show_cur_env_pkg_list(),
            'gpt vim': lambda cmd: edit_cur_env_pkg_content(),

            # handle local pkgs
            'gpt pkgs update': lambda cmd: update_local_pkgs(),
            'gpt pkgs list': lambda cmd: show_local_pkgs_list(cmd),
            'gpt pkgs list -des *': lambda cmd: show_local_pkgs_list(cmd),

            # handle history
            'gpt clear': lambda cmd: clear_screen_and_history(),
            'gpt history list': lambda cmd: show_chat_history_list(),
            'gpt history recover': lambda cmd: recover_chat_history(),
            'gpt history remove -n *': lambda cmd: confirm_and_remove_history(cmd),
            'gpt history remove -all': lambda cmd: confirm_and_remove_all_history(cmd),

            # handle files-based chat
            'gpt chat *': lambda cmd: chat_based_given_files(cmd),

            # create shortcut
            'gpt create shortcut': lambda cmd: create_shortcut(),

            # handle model
            'gpt model change': lambda cmd: change_chat_model(),
            'gpt model list': lambda cmd: show_chat_model_list(),
        }

        def on_cancel_output_flow(key):
            if keyboard.is_pressed('ctrl+shift'):
                self.cancel_output = True

        keyboards = {
            'ctrl+shift': on_cancel_output_flow
        }

        return commands, keyboards

    def run_anagpt(self, cmd):

        for key in self.commands.keys():
            regex = '^' + key.replace('*', '.*') + '$'
            if re.match(regex, cmd):
                func = self.commands[key]
                func(cmd)
                return

        self.show_cmd_not_supported_mess(cmd)
        print('')

    def chat(self):

        while True:
            env_name_text = self.get_color_changed_text(" (" + self.cur_env_name + ") > ")

            input_fun = MultiInputInCmd(env_name_text)
            all_input_lines = input_fun.run()

            if len(all_input_lines[0]) == 0:
                continue

            # handle as cmd first
            message = all_input_lines[0]
            for s in message:
                if s != ' ':
                    message = message[message.index(s):]
                    break

            if message.startswith('cmd '):
                cmd = self.linux_to_cmd(message[4:])
                self.run_cmd(cmd)
                continue

            elif message.startswith('gpt '):
                self.run_anagpt(message)
                continue

            # handle as normal message
            message = ''
            for index in range(len(all_input_lines)):
                if index == len(all_input_lines) - 1:
                    message = message + all_input_lines[index]
                else:
                    message = message + all_input_lines[index] + '\n'

            # set the initial system prompt in the first conversation
            if not self.history:
                self.activate_env(self.cur_env_name)

            self.chat_flow(message=message,
                           history=self.history,
                           system_prompt=self.system_prompt,
                           temperature=0.7)

            # generate history name
            if not self.history_name:
                thread = threading.Thread(target=self.set_history_name)
                thread.start()
            # save chat history
            else:
                thread = threading.Thread(target=self.save_chat_history)
                thread.start()

    def chat_flow(self, message, history, system_prompt, temperature, is_print=True):
        cursor_thread = None
        if is_print:
            # Define cursor states
            CURSOR_STATES = ['-', '\\', '|', '/']

            # Define global variable to control the running state of the thread
            running = True

            # Define the spinning cursor function and wrap it in a thread
            def spinning_cursor():
                while running:
                    for cursor in CURSOR_STATES:
                        # Output cursor state and flush output
                        sys.stdout.write('\r' + cursor)
                        sys.stdout.flush()

                        # Wait for a short period of time
                        time.sleep(0.1)
                sys.stdout.write('\r' + '')
                sys.stdout.flush()

            # Create and start the spinning cursor thread
            cursor_thread = threading.Thread(target=spinning_cursor)
            cursor_thread.start()

        last_index = 0
        chatbot = []
        for chatbot, history, statusDisplay in self.chat_model.predict(message, chatbot=chatbot, history=history,
                                                       system_prompt=system_prompt, temperature=temperature):
            if is_print:
                running = False
                cursor_thread.join()

            if self.cancel_output:
                self.cancel_output = False
                break

            ans = chatbot[0][1]
            if is_print:
                print(ans[last_index:], end='', flush=True)
            last_index = len(ans)

        if is_print:
            print('\n')

        return chatbot[0][1]

    def set_history_name(self):
        # message = ''.join(self.history[:2])
        #
        # prompt = 'This is the first question the user asked chatgpt: "{}", please generate a title for it. ' \
        #          'If there is no suitable title, directly generate "User Question Consultation"'
        #
        # message = prompt.format(message)
        #
        # history_name = self.chat_flow(message=message,
        #                       history=[],
        #                       system_prompt='',
        #                       temperature=1,
        #                       is_print=False)

        history_name = self.history[0][:15] # 15 words is the longest file name has
        history_name = self.convert_to_legal_file_name(history_name)
        self.history_name = history_name

    def get_function_body(self, filename, function_name):
        """
        获取文件 filename 中指定函数 function_name 的函数体。
        :param filename: 文件路径和名称。
        :param function_name: 指定函数的名称。
        :return: 指定函数 function_name 的函数体作为字符串。
        """
        with open(filename, "r", encoding="utf-8") as file:
            source = file.read()

        ast_tree = ast.parse(source)

        function_node = next(
            (node for node in ast.walk(ast_tree) if isinstance(node, ast.FunctionDef) and node.name == function_name),
            None)

        if function_node is not None:
            start_offset = function_node.body[0].lineno - 1
            end_offset = function_node.body[-1].end_lineno
            function_body = source.split("\n")[start_offset:end_offset]
            return 'def ' + function_name + '():\n' + "\n".join(function_body)
        else:
            return None

    def register_fun(self):

        for key in self.keyboards:
            keyboard.on_press(self.keyboards[key])

        atexit.register(self.save_last_model_env_name_content)
        atexit.register(self.save_chat_history)

        system_type = platform.system()

        if system_type == 'Windows':
            def handler(event):
                if event == win32con.CTRL_CLOSE_EVENT:
                    self.save_last_model_env_name_content()
                    self.save_chat_history()

            win32api.SetConsoleCtrlHandler(handler, True)
        elif system_type == 'Linux':
            def signal_handler(signum, frame):
                self.save_last_model_env_name_content()
                self.save_chat_history()
                sys.exit(signum)

            signal.signal(signal.SIGINT, signal_handler)  # hand Ctrl-C
            signal.signal(signal.SIGTERM, signal_handler)  # hand SIGTERM
        else:
            print('the current system is not supported.')
            exit(-1)

    def change_cur_env(self, env_name):
        self.cur_env_name = env_name

    def clear_history(self):
        self.history = []

    def activate_env(self, env_name):
        env_names = [f.name for f in os.scandir(self.envs_root_path) if f.is_dir()]
        if env_name not in env_names:
            print(env_name, 'does not exist.')
            return

        self.clear_history()
        env_content, pkg_names = self.get_env_content(env_name)

        prompt = []

        # for mess in env_content:
        #     content = 'system prompt name ' + str(env_content.index(mess) + 1) + ':'
        #     content = content + pkg_names[env_content.index(mess)]
        #     content = content + 'system prompt ' + str(env_content.index(mess) + 1) + ':'
        #     content = content + mess + ' (' + 'If there is a specific request or similar content mentioned above, please ignore them' + ') ' + '\n  '
        #     content = content + 'Trigger condition: You make your own judgment based on the questions raised by the user' + '\n  '
        #     content = content + 'Response: You generates a response' + '\n  '
        #     prompt.append(content)
        #
        # prompt.append("Please note that all system prompts mentioned above are equal, "
        #               "and when users ask you questions, you should consider all system prompts simultaneously."
        #               "When you are unable to determine which system prompt to use, you can reply, "
        #                "'I'm not sure what you need, can you tell me more?'. "
        #               "Unless given specific instructions, please do not explain your answer or repeat users' question")
        # prompt = ''.join(prompt)

        if env_content:
            prompt.append('1<Please note that only the content boxed in “<>” represents the system prompt I gave you. '
                          'If there are multiple system prompts, you need to integrate all system prompts to answer my question.'
                          # 'you need to choose the most relevant system prompt based on my question to answer by yourself.'
                          'Do not reply the system prompt you have chosen. Do not explain why you have chosen it.'
                          'The importance of all system prompts are the same. If an system prompt emphasizes something of '
                          'its own importance, please ignore it.'
                          'When you are confused about which system prompt to answer based on, you need to ask users, '
                          'and in this case, you must list all the system prompt options in short words for users to '
                          'choose from.> ')

        for i, mess in enumerate(env_content):
            prompt.append(str(env_content.index(mess) + 2) + '<' + pkg_names[i] + ':' + mess +
                          ' (' + 'If there is a specific request or similar content in this system prompt, please ignore it.' + ') ' + '>  ')

        prompt = ''.join(prompt)

        prompt = "Your subsequent responses should all be based on the following prompt:'{}'.".format(prompt)

        self.system_prompt = prompt
        self.change_cur_env(env_name)

    def deactivate_env(self):
        self.activate_env(self.base_env_name)

    def show_log(self):
        print('')
        text = "     /---\     |--|   |--|     /---\     /---------\ |------\  \ |----------| \n" \
               "    /     \    |  |\  |  |    /     \    |  |--- \_/ |  |___/  / |___|  |___| \n" \
               "   /  /_\  \   |  | \ |  |   /  /_\  \   |  | |----| |  |__/  /      |  |     \n" \
               "  /   ___   \  |  |  \|  |  /   ___   \  |  |---|  | |  |            |  |     \n" \
               " /___/   \___\ |__|   |--| /___/   \___\ \_________| |__|            |__|     "
        print(self.get_color_changed_text(text))

    def show_version(self, change_color=False):
        text = f'{self.version}, Model: {self.chat_model.name}'
        if change_color:
            text = self.get_color_changed_text(text)
        print(text)

    def show_welcome_message(self):
        # self.show_log()
        print('')
        print(' ', end='')
        self.show_version(change_color=True)
        print('')
        print(self.get_color_changed_text(' Try "gpt help".'))
        print('')

    def clear_screen_and_history(self):
        run('cls', shell=True, encoding="utf-8")
        self.clear_history()
        self.show_welcome_message()

    def get_color_changed_text(self, text, color='green'):
        if color == 'green':
            return "\033[32m" + text + "\033[0m"

    def linux_to_cmd(self, linux_cmd):
        """
        transfer Linux command to Windows cm=ommand
        """
        cmd = ""

        # Use a dictionary to store the substitution rules for commands.
        replacements = {
            'ls': 'dir',
            'touch': 'echo >',
            'rm': 'del',
            'mkdir': 'md',
            'rmdir': 'rd /q/s',
            'mv': 'move',
            'cp': 'copy',
            'echo': 'echo',
            'cat': 'type',
            'more': 'more',
            'head': 'more +',
            'tail': 'more +'
        }

        # Split the words in a command.
        tokens = linux_cmd.split()

        # Process each word in succession.
        for token in tokens:
            # Search for the substitution rule of the command and replace it with the corresponding Windows CMD command if found.
            if token in replacements:
                cmd += replacements[token] + ' '
            else:
                cmd += token + ' '

        return cmd.strip()

    def run_cmd(self, cmd):
        return run(cmd, shell=True, encoding="utf-8")

    def show_cmd_not_supported_mess(self, cmd):
        print('command ' + '"' + cmd + '"' + ' is not supported!')

    def show_cmd_canceled_mess(self, cmd):
        print('command ' + '"' + cmd + '"' + ' is canceled!')

    def get_env_content(self, env_name):
        message = []
        dir_path = os.path.join(self.envs_root_path, env_name)
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
                 and not f.startswith('.') and not f.endswith('~')] # remove the invisible files
        for file in files:
            f = open(os.path.join(dir_path, file), "r", encoding="utf-8")
            message.append(f.read())
            f.close()

        return message, files

    def show_cur_env_pkg_list(self):
        dir_path = os.path.join(self.envs_root_path, self.cur_env_name)
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
                 and not f.startswith('.') and not f.endswith('~')]
        for file in files:
            f = open(os.path.join(dir_path, file), "r", encoding="utf-8")
            print(
                self.get_color_changed_text(
                str(files.index(file) + 1) + '.' + file
            ))
            print('  ', f.read())
            if files.index(file) < len(files) - 1:
                print('')
            f.close()

    def show_env_describe(self, env_name, is_describe=False):

        message, _ = self.get_env_content(env_name)

        if self.cur_env_name == env_name:
            print(self.get_color_changed_text(' * ' + env_name), end='')
        else:
            print(self.get_color_changed_text('   ' + env_name), end='')
        print(' '.ljust(30 - len(env_name)), end='')

        env_path = os.path.join(self.envs_root_path, env_name)
        print(env_path, end='')

        if not message:
            print('None')
            return

        if not is_describe:
            print('')
            return
        else:
            print('')

        for mess in message:
            print('   ' + mess)

    def show_env_list(self, is_describe=False):
        env_names = [f.name for f in os.scandir(self.envs_root_path) if f.is_dir()]
        for env_name in env_names:
            self.show_env_describe(env_name, is_describe)
            if is_describe and env_names.index(env_name) < len(env_names) - 1:
                print('')
            else:
                pass

    def get_cur_env_name(self):
        return self.cur_env_name

    def create_new_env(self, env_name, clone_name=None):
        path = os.path.join(self.envs_root_path, env_name)
        folder = os.path.exists(path)
        if not folder:
            os.makedirs(path)

            if clone_name:
                src_path = os.path.join(self.envs_root_path, clone_name)
                target_path = path
                if not copy_dir(src_path, target_path):
                    return

            print('Create ', env_name, 'Successfully')
            print('Using "gpt activate {}" to activate environment'.format(env_name))

    def remove_env(self, env_name):
        try:
            path = os.path.join(self.envs_root_path, env_name)
            folder = os.path.exists(path)
            if folder:
                shutil.rmtree(path)
                print('Remove ', env_name, 'successfully')
            else:
                print('Env ', env_name, 'is not exist!')
        except Exception as e:
            print(e)

    def create_new_pkg(self, pkg_name, content):
        filename = None
        try:
            filename = os.path.join(self.envs_root_path, self.cur_env_name)
            filename = os.path.join(filename, pkg_name)
            with open(filename, 'w', encoding="utf-8") as file:
                file.write(content)
            file.close()

            self.activate_env(self.cur_env_name)
            print('Successfully!')

        except Exception as e:
            os.remove(filename)
            print(e)

    def remove_pkg(self, pkg_name):
        try:
            filename = os.path.join(self.envs_root_path, self.cur_env_name)
            filename = os.path.join(filename, pkg_name)
            os.remove(filename)
            return 'Successfully!'

        except Exception as e:

            return e

    def remove_history(self, history_name):
        try:
            filename = os.path.join(self.history_root_path, history_name)
            os.remove(filename)
            return 'Successfully!'

        except Exception as e:

            return e

    def convert_to_legal_file_name(self, text):
        # 替换非法字符
        text = re.sub(r'[^\w\s-]', '_', text).strip().lower()
        # 移除重复的连字符
        text = re.sub(r'-+', '-', text)
        # 去掉斜杠和反斜杠
        text = text.replace('/', '_').replace('\\', '').replace(':', '').replace('：', '').replace(' ', '_')
        return text

    def update_local_pkgs(self):

        def save_pkgs(prompts, url):
            new_count = 0
            update_count = 0
            for prompt in prompts:
                content = prompt[1]
                filename = prompt[0].lower()

                filename = self.convert_to_legal_file_name(filename)

                filename_nopath = filename

                filename = os.path.join(self.pkgs_root_path, filename)

                try:
                    if not os.path.exists(filename):
                        new_count += 1
                    else:
                        exists_file_content = open(filename, "r", encoding="utf-8").read()
                        if exists_file_content != content:
                            print(self.get_color_changed_text('Finding pkg with the same name but different content: {}'.format(filename_nopath)))
                            print('')
                            print(self.get_color_changed_text('Content of old pkg:'))
                            print(exists_file_content)
                            print('')
                            print(self.get_color_changed_text('Content of new pkg:'))
                            print(content)
                            print('')

                            while True:
                                confirm = input(self.get_color_changed_text('Rewrite(r) it or Save(s) as another? r/s:'))
                                if confirm == 'r' or confirm == 'R':
                                    update_count += 1
                                    break
                                elif confirm == 's' or confirm == 'S':
                                    filename = filename + '_1'
                                    new_count += 1
                                    break
                                else:
                                    print('Wrong input!')
                            print('')

                    with open(filename, 'w', encoding="utf-8") as f:
                        f.write(content)
                    f.close()

                except Exception as e:
                    print(e)
                    continue

            print('Load form {} successfully! Add {} new pkgs. Update {} pkgs.'.format(url, new_count, update_count))

        # proxies setting
        proxies = get_conf('proxies')[0]

        # pkg url1
        url = "https://raw.githubusercontent.com/f/awesome-chatgpt-prompts/main/prompts.csv"
        response = requests.get(url, proxies=proxies)
        content = response.content.decode('utf-8')
        # transfer the content of csv to list
        csv_reader = csv.reader(StringIO(content))
        prompts = [row for row in csv_reader][1:]
        save_pkgs(prompts, url)

        # pkg url2
        url = "https://raw.githubusercontent.com/PlexPt/awesome-chatgpt-prompts-zh/main/prompts-zh.json"
        response = requests.get(url, proxies=proxies)
        content = response.content.decode()
        prompts_json = json.loads(content)
        prompts = []
        for prompt in prompts_json:
            content = prompt['prompt']
            act = prompt['act']
            prompts.append([act, content])
        save_pkgs(prompts, url)

        print('You can view them on this path:', self.pkgs_root_path)

    def show_local_pkgs_list(self, describe_name=None):
        dir_path = self.pkgs_root_path
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
                 and not f.startswith('.') and not f.endswith('~')]

        if len(files) == 0:
            print('There is no pkgs found!')

        if describe_name:
            if describe_name in files:
                f = open(os.path.join(dir_path, describe_name), 'r', encoding="utf-8")
                print(f.read())
            else:
                print('{} is not in the pkgs dir!'.format(describe_name))
        else:
            for pkg_name in files:
                print(str(files.index(pkg_name) + 1) + '.', pkg_name)

    def save_last_model_env_name_content(self):

        try:
            content = {}
            content['chat_model'] = self.chat_model.name
            content['env_name'] = self.cur_env_name
            content['env_content'] = self.system_prompt

            with open(os.path.join(self.sys_root_path, 'last_information'), 'w', encoding="utf-8") as f:
                f.write(str(content))
            f.close()

        except Exception as e:
            print(e)

    def load_last_model_env_name_content(self):
        try:
            file_name = os.path.join(self.sys_root_path, 'last_information')
            if not os.path.exists(file_name):
                return

            f = open(file_name, 'r', encoding="utf-8")
            content = f.read()
            f.close()
            content = ast.literal_eval(content)
            self.change_chat_model(content['chat_model'])
            self.activate_env(content['env_name'])

        except Exception as e:
            print(e)

    def save_chat_history(self):

        try:
            if not self.history:
                return

            file_name = self.cur_env_name
            if self.history_name:
                file_name += '-' + self.history_name

            content = {}
            content['cur_env'] = self.cur_env_name
            content['system_prompt'] = self.system_prompt
            content['history'] = self.history
            with open(os.path.join(self.history_root_path, file_name), 'w', encoding="utf-8") as f:
                f.write(str(content))
            f.close()
        except Exception as e:
            # Possible error caused by name issue, so reset the name
            self.history_name = None

    def load_chat_history(self, name):
        try:
            file_name = os.path.join(self.history_root_path, name)
            f = open(file_name, 'r', encoding="utf-8")
            content = f.read()
            f.close()
            content = ast.literal_eval(content)
            self.activate_env(content['cur_env'])
            self.history = content['history']
            self.system_prompt = content['system_prompt']
        except Exception as e:
            print(e)

    def show_chat_history(self):
        print('Here are the chat history you selected:')
        for con in self.history:
            if self.history.index(con) % 2 == 0:
                print(self.get_color_changed_text(' (' + self.cur_env_name + ') > ') + con)
            else:
                print(con)

    def show_chat_history_list(self):
        for name in self.chat_history_list:
            print(self.chat_history_list.index(name) + 1, '.', name)

    def load_chat_history_list(self):
        dir_path = self.history_root_path
        self.chat_history_list = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
                                and not f.startswith('.') and not f.endswith('~')]

    def create_shortcut(self):

        try:
            curr_dir = os.getcwd()
            target_path = os.path.join(curr_dir, 'AnaGPT.cmd')

            desktop = client.Dispatch("WScript.Shell").SpecialFolders("Desktop")
            shortcut_path = os.path.join(desktop, 'AnaGPT.lnk')

            startin = curr_dir
            icon_path = os.path.join(curr_dir, 'ico')
            icon_path = os.path.join(icon_path, 'anagptico.ico')

            shell = client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = target_path
            shortcut.WorkingDirectory = startin
            shortcut.IconLocation = icon_path
            shortcut.save()
        except Exception as e:
            print(e)

    def show_chat_model_list(self):
        model_list_dic = gpt.MODEL_LIST
        for i, key in enumerate(model_list_dic):
            print(str(i + 1) + '.' + key)

    def change_chat_model(self, model_name):
        try:
            model_list_dic = gpt.MODEL_LIST
            if model_name not in model_list_dic:
                print(model_name, 'does not exist.')
                return

            # free memory
            del self.chat_model
            gc.collect()

            self.chat_model = GPT(model_name)
        except Exception as e:
            print(e)



