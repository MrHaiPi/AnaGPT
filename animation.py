
# Define cursor states
import sys
import time


class Thinking:
    def __init__(self):
        self.cursor_states = ['-', '\\', '|', '/']
        self.running = True

    # Define the spinning cursor function and wrap it in a thread
    def spinning_cursor(self):
        while self.running:
            for cursor in self.cursor_states:
                # Output cursor state and flush output
                sys.stdout.write('\r' + cursor)
                sys.stdout.flush()

                # Wait for a short period of time
                time.sleep(0.1)
        sys.stdout.write('\r' + '')
        sys.stdout.flush()

    def stop(self):
        self.running = False


class FilesLoading:
    def __init__(self):
        self.cursor_states = ['files loading -', 'files loading \\', 'files loading |', 'files loading /']
        self.running = True

    # Define the spinning cursor function and wrap it in a thread
    def spinning_cursor(self):
        while self.running:
            for cursor in self.cursor_states:
                # Output cursor state and flush output
                sys.stdout.write('\r' + cursor)
                sys.stdout.flush()

                # Wait for a short period of time
                time.sleep(0.1)

        sys.stdout.write(' done \n')
        sys.stdout.flush()

    def stop(self):
        self.running = False


class FilesAnalyzing:
    def __init__(self):
        self.cursor_states = ['files analyzing -', 'files analyzing \\', 'files analyzing |', 'files analyzing /']
        self.running = True

    # Define the spinning cursor function and wrap it in a thread
    def spinning_cursor(self):
        while self.running:
            for cursor in self.cursor_states:
                # Output cursor state and flush output
                sys.stdout.write('\r' + cursor)
                sys.stdout.flush()

                # Wait for a short period of time
                time.sleep(0.1)

        sys.stdout.write(' done \n')
        sys.stdout.flush()

    def stop(self):
        self.running = False