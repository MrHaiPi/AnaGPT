import threading
import time

import keyboard
from colorama import init, Fore

init()  # init colorama

class MultiInputInCmd:
    def __init__(self, prompt):
        self.message = []
        self.count_time = 0
        self.can_process = False

        self.enter_speed_threshold = 10  # times/s
        self.enter_speed = 1

        self.wait_time = 0.25

        self.stop_event = threading.Event()
        self.input_thread = threading.Thread(target=self.input_text, args=(prompt,))
        self.kill_thread = threading.Thread(target=self.kill_input_text)

    def start(self):
        self.input_thread.start()
        self.kill_thread.start()

    def input_text(self, prompt):
        i = 0
        while not self.stop_event.is_set():
            start = time.time()

            if i == 0:
                print(prompt, end='')

            # Modify terminal text color
            content = input(Fore.GREEN)

            # Record the number of times the enter key is pressed within one second, which is used to distinguish
            # whether it is caused by the user pressing or the pasted multi-line text
            self.enter_speed = 1 / (time.time() - start + 0.00001)

            # Restore terminal text color
            print(Fore.RESET, end='')

            i += 1

            self.message.append(content)

    def kill_input_text(self):

        while not self.stop_event.is_set():

            if self.message and self.enter_speed < self.enter_speed_threshold:
                time.sleep(0.01)
                self.count_time += 0.01

                if self.count_time > self.wait_time:
                    self.stop_event.set()

                    # Release the thread blocked by the "input()" function in input_text
                    keyboard.press_and_release('enter')

                    # this operation must behind the Release operation
                    self.can_process = True
            else:
                time.sleep(0.001)

    def run(self):
        self.start()
        while True:
            time.sleep(0.1)
            if self.can_process:
                break

        return self.message


if __name__ == "__main__":
    while True:
        multi_input = MultiInputInCmd("输入：")
        print(multi_input.run())

