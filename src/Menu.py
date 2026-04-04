from textual.app import App, ComposeResult
from textual.widgets import Label, Button, TextArea
from textual.containers import Horizontal, Vertical
import json
from pathlib import Path
from pydantic import BaseModel
from src.Generator import Generator


class FileEditorConfig(BaseModel):
    """Validated configuration for FileEditor."""

    path_fun: str
    path_call: str
    path_output: str


class FileEditorState(BaseModel):
    """Runtime state for FileEditor."""

    current_file: str | None = None
    is_editable: bool = False


class FileEditor:
    """Load and expose JSON files for the TUI editor."""

    def __init__(self, path_fun: str, path_call: str,
                 path_output: str) -> None:
        """Initialize tracked files and edit state."""
        config = FileEditorConfig(
            path_fun=path_fun,
            path_call=path_call,
            path_output=path_output,
        )
        state = FileEditorState()

        self.current_file = state.current_file
        self.is_editable = state.is_editable
        self.files = {
            "functions": Path(config.path_fun),
            "prompts": Path(config.path_call),
            "output": Path(config.path_output),
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


class Menu(App[None]):
    CSS = """
    Screen {
        layout: horizontal;
        background: #282828;
        color: #ebdbb2;
    }

    #title {
        text-style: bold;
        text-align: center;
        width: 100%;
        padding: 1 0;
        background: #3c3836;
        color: #fe8019;
    }

    #sidebar {
        width: 30;
        border: solid #665c54;
        padding: 1 1;
        background: #3c3836;
    }

    #editor-container {
        width: 1fr;
        height: 1fr;
    }

    Button {
        margin: 1 0;
        width: 100%;
        text-style: none;
        color: #ebdbb2;
        border: none;
        padding: 1 0;
    }

    Button:hover {
        background: #504945;
        color: #fe8019;
    }

    #text-area {
        width: 1fr;
        height: 1fr;
        background: #282828;
        color: #ebdbb2;
    }

    #selector {
        width: 100%;
        height: 3;
        margin: 1 0;
    }

    #selector Button {
        width: auto;
        min-width: 3;
        max-width: 3;
        margin: 0 0;
        color: #fe8019;
    }

    #selector Label {
        width: 1fr;
        text-align: center;
        margin: 0 1;
        padding: 1 0;
        color: #d79921;
    }

    .selector-btn{
        width: 1fr;
        margin: 1 0;
        text-style: none;
        color: #ebdbb2;
    }

    .selector-label{
        width: 1fr;
        text-align: center;
        margin: 1 0;
        color: #ebdbb2;
    }
    """

    def __init__(
        self,
        path_fun: str,
        path_call: str,
        path_output: str,
    ) -> None:
        """Initialize UI state and helper objects."""
        super().__init__()
        self.file_editor = FileEditor(path_fun, path_call, path_output)
        self.generator = Generator(path_fun, path_call, path_output)
        self.p_fun = path_fun
        self.p_call = path_call
        self.p_output = path_output
        self.id_pr = -1

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Call Me Maybe", id="title")
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Button("Functions", id="btn-functions")
                    yield Button("Prompts", id="btn-prompts")
                    yield Button("Output", id="btn-output")
                    with Horizontal(id="selector"):
                        yield Button("<", id="btn-previous")
                        yield Label("Prompt: ALL", id="label-nb-prompt")
                        yield Button(">", id="btn-next")
                    yield Button("Run", id="btn-run", classes="selector-btn")
                    yield Button("Clean", id="btn-clean",
                                 classes="selector-label")
                    yield Button("Exit", id="btn-exit", classes="selector-btn")

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
            self.old_func_txt = self.query_one("#text-area", TextArea)
        elif button_id == "btn-prompts":
            self.write_text_area(self.file_editor.load_file("prompts"))
            self.old_call_txt = self.query_one("#text-area", TextArea)
        elif button_id == "btn-output":
            self.write_text_area(self.file_editor.load_file("output"))
        elif button_id == "btn-previous":
            self.update_nb_prompt("minus")
            self.update_label_pr()
        elif button_id == "btn-next":
            self.update_nb_prompt("add")
            self.update_label_pr()
        elif button_id == "btn-run":
            if self.id_pr == -1:
                self.generator.generate_all_responce()
            else:
                self.generator.generate_responce(
                    self.generator.pr.user_prompts[self.id_pr])
                self.generator.write_responce_json()
            self.write_text_area(self.file_editor.load_file("output"))
            self.notify("Generation success", severity="information")
        elif button_id == "btn-clean":
            self.write_text_area("")
            self.notify("Cleaned", severity="information")
        elif button_id == "btn-exit":
            self.exit()
        else:
            return

    def update_nb_prompt(self, action: str) -> None:
        """ Function to update the promp run """
        if (action == "add"
                and self.id_pr < len(self.generator.pr.user_prompts) - 1):
            self.id_pr += 1
        elif action == "minus" and self.id_pr > -1:
            self.id_pr -= 1

    def update_label_pr(self) -> None:
        """ Update label pr """
        if self.id_pr == -1:
            self.query_one("#label-nb-prompt", Label).update(
                "Prompt: ALL"
            )
        else:
            self.query_one("#label-nb-prompt", Label).update(
                f"Prompt: {self.id_pr}"
            )
