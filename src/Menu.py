from textual.app import App, ComposeResult
from textual.widgets import Label, Button, TextArea
from textual.containers import Horizontal, Vertical
import json
from pathlib import Path
from src.Generator import Generator


class FileEditor:

    def __init__(self, path_fun: str, path_call: str,
                 path_output: str) -> None:
        self.current_file = None
        self.is_editable = False
        self.files = {
            "functions": Path(path_fun),
            "prompts": Path(path_call),
            "output": Path(path_output),
        }

    def load_file(self, file_key: str) -> str:
        file_path = self.files.get(file_key)
        if not file_path or not file_path.exists():
            return f"ERROR: No file found: {file_path}"

        try:
            with open(file_path, 'r') as fd:
                data = json.load(fd)
                self.current_file = file_key
                self.is_editable = file_key in ["functions", "prompts"]
                return json.dumps(data, indent=4)
        except json.JSONDecodeError:
            return "Error: to open file"

    def save_file(self, content: str) -> bool:
        if not self.current_file or not self.is_editable:
            return False

        file_path = self.files[self.current_file]
        try:
            json.loads(content)
            with open(file_path, 'w') as fd:
                fd.write(content)
            return True
        except (json.JSONDecodeError, IOError):
            return "Error: to open file"


class Menu(App[None]):
    CSS = """
    Screen {
        layout: horizontal;
        background: rgb(0,0,0);
        color: rgb(0, 255, 0);
    }

    #title {
        text-style: bold;
        text-align: center;
        width: 100%;
        padding: 1 0;
    }

    #sidebar {
        width: 20;
        border: solid;
        padding: 1 1;
    }

    #editor-container {
        width: 1fr;
        height: 1fr;
    }

    Button {
        margin: 1 0;
        width: 100%;
        text-style: none;
        color: rgb(0, 255, 0);
    }

    #text-area {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, path_fun, path_call, path_output):
        super().__init__()
        self.file_editor = FileEditor(path_fun, path_call, path_output)
        self.generator = Generator(path_fun, path_call, path_output)
        self.p_fun = path_fun
        self.p_call = path_call
        self.p_output = path_output

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Call Me Maybe", id="title")
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Button("Functions", id="btn-functions")
                    yield Button("Prompts", id="btn-prompts")
                    yield Button("Output", id="btn-output")
                    yield Button("Save", id="btn-save")
                    yield Button("Run", id="btn-run")
                    yield Button("Clean", id="btn-clean")
                    yield Button("Exit", id="btn-exit")

                with Vertical(id="editor-container"):
                    yield TextArea(id="text-area")

    def write_text_area(self, content: str) -> None:
        text_area = self.query_one("#text-area", TextArea)
        text_area.text = content
        text_area.read_only = not self.file_editor.is_editable

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn-functions":
            self.write_text_area(self.file_editor.load_file("functions"))
        elif button_id == "btn-prompts":
            self.write_text_area(self.file_editor.load_file("prompts"))
        elif button_id == "btn-output":
            self.write_text_area(self.file_editor.load_file("output"))
        elif button_id == "btn-save":
            self.action_save_file()
        elif button_id == "btn-run":
            self.generator.generate_all_responce()
            self.write_text_area(self.file_editor.load_file("output"))
            self.notify("Generation success", severity="information")
        elif button_id == "btn-clean":
            self.write_text_area("")
            self.notify("Cleaned", severity="information")
        elif button_id == "btn-exit":
            self.exit()
        else:
            return

    def action_save_file(self) -> None:
        if not self.file_editor.is_editable:
            self.notify("File Read Only", severity="warning")
            return

        text_area = self.query_one("#text-area", TextArea)
        if self.file_editor.save_file(text_area.text):
            self.notify("File Saved", severity="information")
            self.generator = Generator(self.p_fun, self.p_call, self.p_output)
        else:
            self.notify("Error to save", severity="error")
