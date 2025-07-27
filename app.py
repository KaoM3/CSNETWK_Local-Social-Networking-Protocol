from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window, HSplit
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout import Dimension, WindowAlign, ScrollablePane
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import Frame
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import Completer, Completion
from custom_types.user_id import UserID
from custom_types.token import Token
import router
import keyword
import log

options = None
msg_types = []

INFO_BUFFER = Buffer(read_only=True)
INFO_WINDOW = Window(content=BufferControl(INFO_BUFFER, focusable=True), align=WindowAlign.CENTER)
INFO_FRAME = Frame(
  body=INFO_WINDOW,
  title="INFO_PANEL",
  style="#52f9ff"
)

class MyCustomCompleter(Completer):
  def __init__(self, words):
    self.words = words

  def get_completions(self, document, complete_event):
    word = document.get_word_before_cursor()
    for w in self.words:
      if w.startswith(word):
        yield Completion(w, start_position=-len(word))

INPUT_BUFFER = Buffer(completer=MyCustomCompleter(msg_types), complete_while_typing=True)
INPUT_WINDOW = Window(content=BufferControl(INPUT_BUFFER, focusable=True), height=Dimension.exact(1))
INPUT_FRAME = Frame(
  body=INPUT_WINDOW,
  title="INPUT_PANEL",
  style="#52f9ff"
)

LOG_BUFFER = Buffer(read_only=True)
LOG_WINDOW = Window(content=BufferControl(LOG_BUFFER, focusable=True), wrap_lines=True)
LOG_FRAME = Frame(
  body=LOG_WINDOW,
  title="LOG_PANEL",
  style="#dfff2b"
)

ROOT_CONTAINER = VSplit(
  children=[
    HSplit(
      children=[
        INFO_FRAME,
        INPUT_FRAME
      ]
    ),
    LOG_FRAME
  ],
)

layout = Layout(ROOT_CONTAINER)
kb = KeyBindings()

@kb.add('enter')
def accept(event):
  if event.app.layout.current_window is INPUT_WINDOW:
    text = INPUT_BUFFER.text
    print_log(f'You typed: {text}')
    if text in msg_types:
      create_message(text.upper())
    INPUT_BUFFER.text = ''

@kb.add('tab')
def auto_complete(event):
  buff = event.app.current_buffer
  if buff.complete_state:
    buff.complete_next()
  else:
    buff.start_completion(select_first=True)

@kb.add('right')
def switch_focus(event):
  event.app.layout.focus_next()

@kb.add('left')
def switch_focus(event):
  event.app.layout.focus_previous()

@kb.add('escape')
def back(event):
  display_options()

@kb.add('c-q')
def exit_(event):
  """
  Pressing Ctrl-Q will exit the user interface.

  Setting a return value means: quit the event loop that drives the user
  interface and return this value from the `Application.run()` call.
  """
  event.app.exit()

def print_log(text):
  LOG_BUFFER._set_text(LOG_BUFFER.text + ">> " + text + '\n\n')
  LOG_BUFFER.cursor_position = len(LOG_BUFFER.text)

def set_info(text):
  INFO_BUFFER._set_text(str(text))

def add_info(text):
  INFO_BUFFER._set_text(INFO_BUFFER.text + "\n" + str(text))

def display_options():
  global options
  if options is None:
    options = ""
    options += ("\nAvailable Message Types\n\n")
    for i, (key, _) in enumerate(router.MESSAGE_REGISTRY.items(), start=1):
      options += (f"{i}. {key}\n")
      msg_types.append(key.lower())
    set_info(str(options))
  else:
    set_info(str(options))

type_parsers = {
  UserID: UserID.parse,
  Token: Token.parse,
}

def create_message(msg_type: str): # ping , dm, profile
  msg_class = router.get_module(msg_type)
  msg_schema = msg_class.__schema__

  new_msg_args = {}
  for field, rules in msg_schema.items():
    # TYPE field, autofills with schema TYPE
    if field == "TYPE":
      set_info(f"\nCreating new {rules} message\n")
      continue
    # Gets the input args for the message type constructor
    if not rules.get("input", False):
      continue
    INPUT_BUFFER._set_text(f"{field}: ")
    


def start_app():
  app = Application(layout=layout, full_screen=True, key_bindings=kb)
  display_options()
  app.run()