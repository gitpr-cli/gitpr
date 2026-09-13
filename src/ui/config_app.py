"""Interactive configuration screen for ~/.gitpr/.env (gitpr config).

Master-detail layout: the sidebar lists the categories declared in
src/config_schema.py, the main area renders the fields of the selected one.

Three behaviours are worth stating up front, because they are the reason this
screen exists rather than the user editing the file by hand:

  * The value displayed comes from the FILE, never from os.getenv(). Every
    load_dotenv() call in the project runs with override=False, so a process
    environment variable silently beats the .env — a field whose environment
    value differs is annotated instead of being silently misrepresented.
  * "Restore default" (Ctrl+R) removes the line from the .env rather than
    writing the default back, so the key keeps following the code default if
    that default ever changes.
  * A secret is never displayed back. The widget stays empty and only a newly
    typed value is written, after being validated against the provider.
"""

import os
import sys
from contextlib import contextmanager

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
    Switch,
    TextArea,
)

from src.config import (
    ENV_FILE,
    SKILL_FILES_BY_TYPE,
    SKILL_TYPES,
    VALIDATION_AUTH,
    VALIDATION_NETWORK,
    get_skill_dir,
    read_env_file_values,
    read_skill_file,
    remove_config_value,
    save_config_values,
    skill_file_path,
    skill_file_status,
    skill_template_remote_name,
    validate_ai_key,
    write_skill_file,
)
from src.config_schema import (
    ACTION_DOWNLOAD,
    ACTION_DOWNLOAD_WORDS,
    BOOL_TRUE,
    CATEGORIES,
    CATEGORY_ORDER,
    FIELDS,
    FIELDS_BY_KEY,
    GROUP_LABELS,
    KIND_BOOL,
    KIND_ENUM,
    KIND_SECRET,
    KIND_STR,
    KIND_VERSION,
    KIND_WORDS,
    KNOWN_KEYS,
    SKILL_LABELS,
    VALIDATOR_AI_KEY,
    VALIDATOR_SCM_TOKEN,
    VERSION_LANG,
    VERSION_SCRIPTS,
    VISIBILITY_CONTROLLERS,
    ConfigField,
    field_lookup_terms,
    validate_field_value,
)
from src.doc_links import doc_url
from src.i18n import AMBIENT_ENV_KEYS, __, set_lang
from src.security import encrypt_data

# Safe to import here: stdlib plus click and i18n, with no I/O at import time.
# It carries the version constants the screen falls back to below.
from src.updater import __lang_version__, __scripts_version__

# Category id created on the fly for keys the schema does not know about.
UNKNOWN_CATEGORY_ID = "unknown"

_VALUE_PREFIX = "value_"
_MARK_PREFIX = "mark_"
_ERROR_PREFIX = "error_"
_WORDS_PREFIX = "words_"
_ROW_PREFIX = "row_"
_ACTION_PREFIX = "act_"
_STATUS_PREFIX = "status_"

# --- Skills section. The prefix differs from the plain "skill_" the other
# widgets use on purpose: a skill item's id carries the skill type, and
# "skill_editor" would otherwise parse as a type named "editor".
_SKILL_ITEM_PREFIX = "skillitem_"
_SKILLS_LIST_ID = "skills_list"
_SKILL_PANE_ID = "skills_pane"
_SKILL_EDITOR_ID = "skill_editor"
_SKILL_ABSENT_NOTE_ID = "skill_absent_note"
_SKILL_ACTIONS_ID = "skill_actions"
_SKILL_DOWNLOAD_ID = "skill_download"
_SKILL_STATUS_ID = "skill_status"

# The states config.skill_file_status() distinguishes, and what each one means
# for the pane:
#   editable   a file is there and can be written      -> editor open
#   missing    this project has no such file yet       -> note + download
#   readonly   the file is there but not writable      -> editor shown, locked
#   unreadable the file cannot be read at all          -> editor shown, locked
_SKILL_MISSING = "missing"
_SKILL_EDITABLE = "editable"
_SKILL_READONLY = "readonly"
_SKILL_UNREADABLE = "unreadable"

# The one schema key whose displayed value is not an .env value: the folder the
# project's skill files live in, resolved from the working directory.
SKILLS_FOLDER_KEY = "SKILLS_FOLDER"

# Label shown for the empty choice of an enum ("let GitPR decide").
_AUTOMATIC_LABEL = __("(automatic)")

# Secret field -> the AI provider whose endpoint validates it.
_SECRET_PROVIDERS = {
    "GEMINI_API_KEY_ENCRYPTED": "gemini",
    "DEEPSEEK_API_KEY_ENCRYPTED": "deepseek",
}

# Version marker source -> the constant the code falls back to when the marker
# is not in the file. A marker only exists once its loader has run, and some
# loaders are reached only through an optional command (LINTER_PRESETS_VERSION
# comes from `gitpr --linter-setup`), so an empty box is the common case rather
# than the exception. It is display only: nothing here is ever written back.
_VERSION_FALLBACKS = {
    VERSION_LANG: __lang_version__,
    VERSION_SCRIPTS: __scripts_version__,
}

# Schema action -> the label of its button. An unknown action falls back to a
# generic label: the button still works, because the dispatch below goes by
# field key, not by the action.
_ACTION_LABELS = {
    ACTION_DOWNLOAD: __("📥 Force download"),
    ACTION_DOWNLOAD_WORDS: __("📥 Download the word list"),
}


def _current_lang():
    """The live session language.

    Read lazily on purpose: set_lang() rebinds src.i18n.CURRENT_LANG, so a
    module-level ``from src.i18n import CURRENT_LANG`` here would freeze the
    value the process started with.
    """
    from src.i18n import CURRENT_LANG

    return CURRENT_LANG


# --------------------------------------------------------------- downloads
# The four loaders behind the action buttons. Each one imports its module
# INSIDE the function, because importing any of them at module level would run
# work this screen must not do while opening: src.spinner downloads the word
# list at import time, and src.core (reached through src.linter_wizard too)
# pulls the AI SDKs.


def _download_lang_pack():
    """Re-downloads the translation pack of the current language."""
    from src.i18n import get_translations

    return get_translations(_current_lang(), force=True)


def _download_smart_excludes():
    """Re-downloads the smart-excludes filter list."""
    from src.core import _load_smart_excludes

    return _load_smart_excludes(force=True)


def _download_linter_presets():
    """Re-downloads the external linter presets used by --linter-setup."""
    from src.linter_wizard import load_linter_presets

    return load_linter_presets(force=True)


def _download_thinking_words():
    """Re-downloads the spinner word list and returns it."""
    from src.spinner import reload_thinking_words

    return reload_thinking_words(_current_lang(), force=True)


# Field key -> the loader that refreshes it. Keyed by field rather than by
# action: three fields share ACTION_DOWNLOAD, and each one refreshes a
# different artifact.
_DOWNLOAD_SOURCES = {
    "LANG_VERSION": _download_lang_pack,
    "SMART_EXCLUDES_VERSION": _download_smart_excludes,
    "LINTER_PRESETS_VERSION": _download_linter_presets,
    "THINKING_WORDS_VERSION": _download_thinking_words,
    "SPINNER_THINKING_WORDS": _download_thinking_words,
}

# Field -> the key whose marker proves the write went through. A version field
# is proven by its own line; the word list is proven by the version line its
# loader stamps next to it.
_PAYLOAD_MARKERS = {"SPINNER_THINKING_WORDS": "THINKING_WORDS_VERSION"}


def _marker_key(field):
    return _PAYLOAD_MARKERS.get(field.key, field.key)


def _expected_marker_value(field):
    """The constant the marker must carry after a successful download.

    Taken from the version field that owns the marker, so the number stays
    declared once, in the schema. "" means the marker cannot be verified.
    """
    marker_field = FIELDS_BY_KEY.get(_marker_key(field))
    if marker_field is None:
        return ""
    return _VERSION_FALLBACKS.get(marker_field.version_source, "")


def _clear_click_cache():
    """Click caches its stdout wrapper; it must be dropped around the redirect."""
    import click._compat

    for fn in (click._compat._default_text_stdout, click._compat._default_text_stderr):
        try:
            fn.cache_clear()
        except Exception:
            pass


@contextmanager
def _quiet_output():
    """Silences anything a loader prints while it runs in the worker thread.

    Duplicated from ui/pr_publish_app.py instead of imported: that module
    imports src.core, which would put the AI SDKs in the import graph of a
    screen that opens on every ``gitpr config``. The loaders are silent today —
    this is insurance against a print or click.echo added to one of them later,
    and against Textual's captured stdout, which has no valid fd.
    """
    old_stdout = sys.stdout
    _clear_click_cache()
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout
        _clear_click_cache()


def _as_bool(raw):
    """Mirrors main.py's _env_flag(): everything outside BOOL_TRUE is false."""
    return (raw or "").strip().lower() in BOOL_TRUE


def _split_words(raw):
    """Splits the stored word list the way spinner._parse_env_words() does.

    Duplicated on purpose: importing src.spinner would run its module-level
    _load_thinking_words() — a network download — just for opening this screen.
    """
    raw = raw or ""
    sep = "|" if "|" in raw else ";"
    return [word.strip() for word in raw.split(sep) if word.strip()]


def _value_id(key):
    return f"{_VALUE_PREFIX}{key}"


def _mark_id(key):
    return f"{_MARK_PREFIX}{key}"


def _error_id(key):
    return f"{_ERROR_PREFIX}{key}"


def _words_id(key):
    return f"{_WORDS_PREFIX}{key}"


def _action_id(key):
    return f"{_ACTION_PREFIX}{key}"


def _status_id(key):
    return f"{_STATUS_PREFIX}{key}"


def unknown_field(key):
    """A read-only pseudo field for a key the schema does not declare."""
    return ConfigField(
        key=key,
        label=key,
        description=__("Not used by GitPR — kept as it is in the file."),
        category=UNKNOWN_CATEGORY_ID,
        kind=KIND_STR,
        default="",
        read_only=True,
    )


class ConfigHelpScreen(ModalScreen):
    """Help modal (F1)."""

    BINDINGS = [Binding("escape", "dismiss", __("Close"))]

    CSS = """
    ConfigHelpScreen { align: center middle; }
    #help_root {
        width: 74; height: auto;
        padding: 1 2;
        background: $surface; border: thick $background 80%;
    }
    #help_root Static { width: 100%; height: auto; }
    #help_title { text-align: center; text-style: bold; margin-bottom: 1; }
    #help_close { margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help_root"):
            yield Static(__("⌨️  Configuration — shortcuts"), id="help_title")
            yield Static(__("F1 — this help"))
            yield Static(__("F2 — validate and save the pending changes"))
            yield Static(__("Ctrl+R — restore the default of the focused field"))
            yield Static(__("/ — search a key or a label in every category"))
            yield Static(__("Esc — leave, or clear the search; asks before discarding"))
            yield Static("")
            yield Static(
                __(
                    "Values are read from ~/.gitpr/.env. A field marked "
                    "“in environment” is being overridden by a process "
                    "environment variable, which always wins over the file."
                )
            )
            yield Button(__("Close"), variant="primary", id="help_close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()


class ConfirmDiscardScreen(ModalScreen):
    """Asks before leaving with unsaved changes."""

    BINDINGS = [Binding("escape", "keep_editing", __("Keep Editing"))]

    CSS = """
    ConfirmDiscardScreen { align: center middle; }
    #confirm_root {
        width: 60; height: 50%;
        padding: 1 2;
        background: $surface; border: thick $background 80%;
    }
    #confirm_text { width: 100%; height: auto; text-align: center; margin-bottom: 1; }
    #confirm_buttons { height: auto; align-horizontal: center; }
    Button { margin: 0 1; min-width: 16; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm_root"):
            yield Static(
                __("There are unsaved changes. Leave and lose them?"),
                id="confirm_text",
            )
            with Horizontal(id="confirm_buttons"):
                yield Button(__("Discard"), variant="error", id="btn_discard")
                yield Button(__("Keep Editing"), variant="primary", id="btn_keep")

    def action_keep_editing(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn_discard")


class FieldRow(Vertical):
    """One configuration entry: label, control, description and inline error."""

    def __init__(self, field, raw_value, is_set, shadowed, read_only=False):
        super().__init__(id=f"row_{field.key}", classes="field")
        self.field = field
        self.raw_value = raw_value
        self.is_set = is_set
        self.shadowed = shadowed
        self.read_only = read_only or field.read_only
        self.marked_for_removal = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="field-head"):
            yield Static(self.field.label, classes="field-label")
            yield Static(
                self._annotation(),
                id=_mark_id(self.field.key),
                classes="field-annotation",
            )
        yield self._build_control()
        if self.field.action:
            # A line of its own: .field-head is height 1, and the annotation
            # there is a 1fr Static that would push the button to the far right.
            with Horizontal(classes="field-actions"):
                yield Button(
                    _ACTION_LABELS.get(self.field.action, __("Download")),
                    compact=True,
                    id=_action_id(self.field.key),
                )
                yield Static(
                    "", id=_status_id(self.field.key), classes="action-status"
                )
        yield Static(self.field.description, classes="field-help")
        yield Static("", id=_error_id(self.field.key), classes="field-error")

    def _annotation(self):
        """The ambient note shown next to the label, if any.

        A field whose key is present in the process environment is flagged
        because load_dotenv(override=False) makes os.environ win over the file —
        editing it here changes the file without changing the running value.
        """
        notes = []
        if self.read_only:
            notes.append(__("read only"))
        if self.field.kind == KIND_WORDS:
            notes.append(
                __("{count} word(s)", count=len(_split_words(self.raw_value)))
            )
        if self.field.kind == KIND_VERSION and not self.is_set and self.raw_value:
            # Say where the number on screen came from: it is the version the
            # code would use, not something the file already records.
            notes.append(__("code version — not set in the file"))
        if self.shadowed:
            notes.append(__("⚠ in environment — the file value is not in use"))
        if self.marked_for_removal:
            notes.append(__("— will be removed —"))
        return "   ".join(notes)

    def _build_control(self):
        key = self.field.key
        widget_id = _value_id(key)

        if self.field.kind == KIND_BOOL:
            return Switch(value=_as_bool(self.raw_value), id=widget_id)

        if self.field.kind == KIND_ENUM:
            labels = dict(self.field.choice_labels)
            # An explicit label always wins, so a field can name its own empty
            # choice — DEFAULT_AI_PROVIDER reads "(not configured)" there, which
            # is what an empty value really does. Everything else falls back to
            # "(automatic)" for "" and to the raw value.
            options = [
                (
                    labels.get(
                        choice, _AUTOMATIC_LABEL if choice == "" else choice
                    ),
                    choice,
                )
                for choice in self.field.choices
            ]
            # A value that is not a declared choice must stay visible instead of
            # crashing Select — the user sees what the file really holds, and
            # validation refuses to save it as it is.
            if self.raw_value and self.raw_value not in self.field.choices:
                options.append(
                    (__("{value} (invalid)", value=self.raw_value), self.raw_value)
                )
            return Select(
                options, value=self.raw_value, allow_blank=False, id=widget_id
            )

        if self.field.kind == KIND_WORDS:
            # One Static inside a scroll, not one widget per word: the published
            # list has hundreds of entries, and a ListView would have to be
            # cleared asynchronously — the interleaving _mount_rows() exists to
            # avoid. markup=False because the words are user data, and text in
            # brackets would otherwise be parsed as markup and raise.
            return VerticalScroll(
                Static(self._words_text(), id=_words_id(key), markup=False),
                id=widget_id,
                classes="words-box",
            )

        if self.field.kind == KIND_SECRET:
            # The real value never reaches the widget; an empty box means
            # "leave it exactly as it is".
            return Input(
                value="",
                password=True,
                placeholder=(
                    __("•••••••• (set — type to replace)")
                    if self.is_set
                    else __("not set")
                ),
                id=widget_id,
                disabled=self.read_only,
            )

        return Input(value=self.raw_value, id=widget_id, disabled=self.read_only)

    def set_error(self, text):
        self.query_one(f"#{_error_id(self.field.key)}", Static).update(text)

    def set_removal_mark(self, marked):
        """Announces that the line will be deleted from the .env.

        The control stays enabled on purpose: disabling it moves the focus
        away, which would make Ctrl+R impossible to undo.
        """
        self.marked_for_removal = marked
        self.refresh_annotation()

    def set_action_status(self, text):
        """Writes the short outcome next to the button."""
        self.query_one(f"#{_status_id(self.field.key)}", Static).update(text)

    def set_action_enabled(self, enabled):
        """Disabled while the download runs, so a second click cannot start one."""
        self.query_one(f"#{_action_id(self.field.key)}", Button).disabled = not enabled

    def refresh_annotation(self):
        """Re-renders the note next to the label from the row's current state."""
        self.query_one(f"#{_mark_id(self.field.key)}", Static).update(
            self._annotation()
        )

    def _words_text(self):
        words = _split_words(self.raw_value)
        if not words:
            return __("No words in the file — GitPR falls back to its built-in list.")
        return " · ".join(words)

    def set_words(self, raw):
        """Re-renders the word list after a download rewrote it in the .env."""
        self.raw_value = raw
        self.is_set = True
        self.query_one(f"#{_words_id(self.field.key)}", Static).update(
            self._words_text()
        )
        self.refresh_annotation()

    def mark_downloaded(self):
        """Drops the "not set in the file" note once the file holds the marker.

        Only the stored state and the note change. The control is never written
        back: for a version marker the value on screen already is the code
        constant it was stamped with, and assigning to Input.value would post
        Input.Changed — turning a download into an unsaved edit that F2 would
        then offer to save.
        """
        self.is_set = True
        self.refresh_annotation()


class ConfigApp(App):
    """Master-detail configuration screen for ~/.gitpr/.env."""

    TITLE = __("GitPR - Configuration")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    #toolbar { height: 3; padding: 0 1; background: $panel; }
    #search { width: 1fr; }
    #dirty_indicator { width: 30; content-align: right middle; color: $warning; }
    #advanced_box { width: 26; height: 3; }
    #advanced_box Label { width: auto; padding: 1 0 0 1; color: $text-muted; }
    #body { height: 1fr; }
    #sidebar { width: 34; border-right: solid $accent; }
    #categories { height: 1fr; }
    #main { width: 1fr; padding: 0 2; }
    #fields { height: auto; }
    .category-title { text-style: bold; color: $accent; }
    .category-help { color: $text-muted; margin-bottom: 1; }
    .group-head {
        text-style: bold;
        color: $text-muted;
        margin: 1 0 1 0;
        border-bottom: solid $panel;
    }
    .field { height: auto; margin-bottom: 1; }
    .field-head { height: 1; }
    .field-label { width: auto; text-style: bold; }
    .field-annotation { margin-left: 1; }
    .words-box {
        height: auto;
        max-height: 12;
        border: solid $panel;
        padding: 0 1;
    }
    .field-actions { height: auto; margin-top: 1; }
    .action-status { margin-left: 2; color: $text-muted; }
    #category_doc { height: auto; margin-bottom: 1; }
    .doc-url { margin-left: 2; color: $text-muted; }
    .field-help { color: $text-muted; }
    .field-error { color: $error; }
    #empty { color: $text-muted; }
    #skills_pane { height: auto; }
    #skills_list { height: auto; max-height: 8; border: solid $panel; }
    #skill_editor_box { height: auto; margin-top: 1; }
    #skill_editor_title { text-style: bold; }
    #skill_editor { height: 14; border: solid $panel; }
    #skill_absent_note { color: $text-muted; }
    #skill_actions { height: auto; margin-top: 1; }
    """

    BINDINGS = [
        Binding("f1", "show_help", __("Help")),
        Binding("f2", "save", __("Save")),
        Binding("ctrl+r", "reset_field", __("Restore Default")),
        Binding("slash", "focus_search", __("Search")),
        Binding("escape", "quit", __("Exit")),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_values = read_env_file_values()
        self.shadowed_keys = {
            key
            for key in self.file_values
            if key in AMBIENT_ENV_KEYS and os.environ.get(key) not in (None, "")
        }
        # Keys in the file that the schema does not declare. The screen never
        # writes one, so this set is fixed for the lifetime of the screen —
        # only an external edit to the file could change it. A download button
        # cannot either: every key the loaders write is a declared field, so
        # re-reading the file after one never adds a row the sidebar lacks.
        self.unknown_keys = sorted(set(self.file_values) - set(KNOWN_KEYS))
        # The edited values, keyed by env var name. This — not the widgets — is
        # the state of the screen: the visible set changes as the user navigates
        # or searches, and a value read back from a hidden control would be
        # fragile. It is also what makes F2 independent of what is on screen.
        self.pending = {}
        # Keys the user asked to delete from the .env (Ctrl+R, applied on save).
        self.marked_for_removal = set()
        self.show_advanced = False
        self._saving = False
        # Every row is mounted once (see _mount_rows), keyed by env var name.
        self.rows = {}
        # Group headers, mounted once as well, and the keys each one labels —
        # the header is only shown when one of its own fields survived the
        # filter, so a group never labels an empty stretch of screen.
        self.group_headers = {}
        self.group_members = {}
        # --- Skills. Separate from self.pending, which holds .env keys: a skill
        # is a file of this project, not a setting, and the two are saved by
        # different code paths. skill_files is what is on disk (the baseline the
        # editor is compared against), skill_pending the edits not yet written.
        self.skill_files = {}
        self.skill_status = {}
        self.skill_pending = {}
        # The skill the editor is showing. Set before the text is loaded, so a
        # Changed message arriving later is attributed to the right skill.
        self.selected_skill = None
        self._load_skills()

    # ------------------------------------------------------------- lifecycle

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="toolbar"):
            yield Input(placeholder=__("/ search a key or a label"), id="search")
            yield Static("", id="dirty_indicator")
            with Horizontal(id="advanced_box"):
                yield Label(__("Show advanced"))
                yield Switch(value=False, id="show_advanced")
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield ListView(id="categories")
            with VerticalScroll(id="main"):
                yield Static("", id="category_title", classes="category-title")
                yield Static("", id="category_help", classes="category-help")
                with Horizontal(id="category_doc"):
                    yield Button(__("📚 Documentation"), compact=True, id="doc_open")
                    yield Static("", id="doc_url", classes="doc-url")
                with Vertical(id="fields"):
                    yield Static("", id="empty")
                with Vertical(id=_SKILL_PANE_ID):
                    yield ListView(
                        *[
                            ListItem(
                                Static(self._skill_item_text(skill_type)),
                                id=f"{_SKILL_ITEM_PREFIX}{skill_type}",
                            )
                            for skill_type in SKILL_TYPES
                        ],
                        id=_SKILLS_LIST_ID,
                    )
                    with Vertical(id="skill_editor_box"):
                        yield Static("", id="skill_editor_title")
                        yield TextArea("", id=_SKILL_EDITOR_ID)
                        yield Static("", id=_SKILL_ABSENT_NOTE_ID)
                        with Horizontal(id=_SKILL_ACTIONS_ID):
                            yield Button(
                                __("📥 Download the template"),
                                compact=True,
                                id=_SKILL_DOWNLOAD_ID,
                            )
                            yield Static(
                                "", id=_SKILL_STATUS_ID, classes="action-status"
                            )
        yield Footer()

    def on_mount(self) -> None:
        self._build_sidebar()
        self._mount_rows()
        list_view = self.query_one("#categories", ListView)
        if len(list_view.children):
            list_view.index = 0
            list_view.focus()
        self._render_view()
        # The skill list is static, so its index is set once here; the load is
        # explicit rather than left to the Highlighted message, so the pane is
        # never blank if that message does not fire.
        self.query_one(f"#{_SKILLS_LIST_ID}", ListView).index = 0
        self._select_skill(SKILL_TYPES[0])

    def _mount_rows(self):
        """Mounts every row once; switching view only toggles visibility.

        Rebuilding the rows on each switch would mean awaiting an async
        removal, and two overlapping renders — fast typing in the search box —
        would then interleave and mount duplicate rows. Toggling display is
        synchronous and cannot interleave.

        The same holds for the group headers, mounted here for the same reason:
        one Static per group, placed right before its first field.
        """
        container = self.query_one("#fields", Vertical)
        widgets = []

        for field in FIELDS:
            if field.group and field.group not in self.group_headers:
                header = Static(
                    GROUP_LABELS.get(field.group, field.group),
                    id=f"grp_{field.group}",
                    classes="group-head",
                )
                self.group_headers[field.group] = header
                self.group_members[field.group] = set()
                widgets.append(header)
            if field.group:
                self.group_members[field.group].add(field.key)
            self.rows[field.key] = self._make_row(field, self.file_values)
            widgets.append(self.rows[field.key])

        for key in self.unknown_keys:
            self.rows[key] = self._make_row(
                unknown_field(key), self.file_values, forced_read_only=True
            )
            widgets.append(self.rows[key])

        container.mount_all(widgets)

    @staticmethod
    def _make_row(field, file_values, forced_read_only=False):
        """Builds a row, standing the code constant in for an absent marker.

        is_set stays False, so the annotation explains where the value came
        from and the field is still understood as absent from the file.
        """
        is_set = field.key in file_values
        raw_value = file_values.get(field.key, field.default)
        if field.kind == KIND_VERSION and not is_set:
            raw_value = _VERSION_FALLBACKS.get(field.version_source, field.default)
        if field.key == SKILLS_FOLDER_KEY:
            # Not an .env key at all: the folder is resolved from the working
            # directory each time it is asked for. Reading it here is what puts
            # the path on screen without the schema having to know about it.
            raw_value = get_skill_dir()
        return FieldRow(
            field,
            raw_value,
            is_set=is_set,
            shadowed=field.key in AMBIENT_ENV_KEYS
            and os.environ.get(field.key) not in (None, ""),
            read_only=forced_read_only,
        )

    # --------------------------------------------------------------- sidebar

    def sidebar_categories(self):
        """Sidebar ids in mount order — every category, visible or not."""
        return list(CATEGORY_ORDER) + (
            [UNKNOWN_CATEGORY_ID] if self.unknown_keys else []
        )

    def _build_sidebar(self):
        """Mounts every category once; the toggle only hides the advanced one.

        Clearing and re-appending would be async — ListView.clear() removes on
        the next refresh — and a second toggle landing before that completes
        would raise DuplicateIds.
        """
        list_view = self.query_one("#categories", ListView)
        for category_id in CATEGORY_ORDER:
            list_view.append(
                ListItem(
                    Label(self.category_label(category_id)), id=f"cat_{category_id}"
                )
            )
        if self.unknown_keys:
            list_view.append(
                ListItem(
                    Label(self.category_label(UNKNOWN_CATEGORY_ID)),
                    id=f"cat_{UNKNOWN_CATEGORY_ID}",
                )
            )
        self._apply_advanced_visibility()

    def _apply_advanced_visibility(self):
        """Hides the advanced entry when the toggle is off.

        Disabled as well as hidden: ListView's cursor skips disabled items but
        would still land on a merely hidden one.
        """
        item = self.query_one("#cat_advanced", ListItem)
        item.display = self.show_advanced
        item.disabled = not self.show_advanced

    def category_label(self, category_id):
        if category_id == UNKNOWN_CATEGORY_ID:
            return __("Unknown")
        for category in CATEGORIES:
            if category.id == category_id:
                return category.label
        return category_id

    def category_doc(self, category_id):
        """The documentation page of a category ("" when it has none)."""
        for category in CATEGORIES:
            if category.id == category_id:
                return category.doc
        return ""

    def category_description(self, category_id):
        if category_id == UNKNOWN_CATEGORY_ID:
            return __(
                "Keys present in the file that GitPR does not use. Read only — "
                "edit the file by hand to change them."
            )
        for category in CATEGORIES:
            if category.id == category_id:
                return category.description
        return ""

    def selected_category(self):
        list_view = self.query_one("#categories", ListView)
        if list_view.index is None or not list_view.children:
            return None
        item = list_view.children[list_view.index]
        return (item.id or "")[len("cat_") :]

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Fires on navigation and once on the initial mount.

        Both lists post the same message, so it is dispatched by the view it
        came from: the categories list re-renders the pane, the skills list
        opens the highlighted skill.
        """
        if event.list_view.id == _SKILLS_LIST_ID:
            skill_type = (event.item.id or "")[len(_SKILL_ITEM_PREFIX) :] if event.item else ""
            if skill_type in SKILL_FILES_BY_TYPE:
                self._select_skill(skill_type)
            return
        self._render_view()

    # ------------------------------------------------------------- rendering

    def visible_keys(self, term=""):
        """The env var names the main area should show.

        The search deliberately ignores show_if: looking a provider up while
        another one is selected has to find its fields, otherwise a value typed
        for an unused provider could never be reached from the screen. Saving is
        blind to visibility anyway, so a field found that way is a normal edit.
        """
        needle = (term or "").strip().lower()
        if needle:
            return {
                field.key
                for field in FIELDS
                if (self.show_advanced or not field.advanced)
                and any(needle in token for token in field_lookup_terms(field))
            }
        category_id = self.selected_category()
        if category_id == UNKNOWN_CATEGORY_ID:
            return set(self.unknown_keys)
        return {
            field.key
            for field in FIELDS
            if field.category == category_id
            and (self.show_advanced or not field.advanced)
            and self.show_if_satisfied(field)
        }

    def show_if_satisfied(self, field):
        """True when every show_if gate accepts its controller's value.

        The controller is read through effective_value — the pending edit first,
        the file second — so picking another provider or forge re-filters the
        pane straight away, instead of only on the next launch after saving.
        """
        for key, allowed in field.show_if:
            controller = FIELDS_BY_KEY[key]
            if self.effective_value(controller) not in allowed:
                return False
        return True

    def _focus_is_visible(self):
        """False when the focused widget sits inside a row the view hid."""
        widget = self.focused
        while widget is not None:
            if not widget.display:
                return False
            widget = widget.parent
        return True

    def _render_view(self, term=""):
        """Shows the rows of the current view and hides every other one.

        Only display is toggled — never a widget's value — so this cannot post
        a Changed message and re-enter itself.
        """
        visible = self.visible_keys(term)
        for key, row in self.rows.items():
            row.display = key in visible

        # A header belongs to the category view: the search returns a flat list
        # in FIELDS order, so a header there would label only the first stretch
        # of its group and leave the rest looking like it belongs to the header
        # above.
        for group_id, header in self.group_headers.items():
            header.display = not term and any(
                key in visible for key in self.group_members[group_id]
            )

        title = self.query_one("#category_title", Static)
        help_text = self.query_one("#category_help", Static)
        empty = self.query_one("#empty", Static)
        doc_row = self.query_one("#category_doc", Horizontal)
        doc_text = self.query_one("#doc_url", Static)

        if term:
            title.update(__("Search: {term}", term=term))
            help_text.update(
                __("{count} field(s) match in every category.", count=len(visible))
            )
            empty.update(__("No field matches that search."))
        else:
            category_id = self.selected_category()
            title.update(self.category_label(category_id) if category_id else "")
            help_text.update(
                self.category_description(category_id) if category_id else ""
            )
            empty.update(__("Nothing to show in this category."))
        empty.display = not visible

        # The link belongs to a category, so neither the search nor the
        # synthesised "unknown" section — which has no Category, hence no page —
        # shows it. The URL is printed next to the button so it can be read and
        # copied, the way the CLI already prints it.
        doc = "" if term else self.category_doc(self.selected_category())
        doc_row.display = bool(doc)
        doc_text.update(doc_url(doc) if doc else "")

        # The skills list and its editor are not ConfigFields, so the search
        # cannot filter them — it would have to search file contents, and hiding
        # a skill because its label missed the term would look like the file had
        # disappeared from the project. The search hides the pane whole; the
        # SKILLS_FOLDER row above it still matches like any other field.
        self.query_one(f"#{_SKILL_PANE_ID}", Vertical).display = (
            not term and self.selected_category() == "skills"
        )

        # A gate can hide the row the user is on, and Textual keeps the focus
        # on a widget set to display=False — so without this the user would
        # keep typing into a field that is no longer on screen. The search box
        # is never hidden, so its focus is never stolen.
        if self.focused is None or not self._focus_is_visible():
            self.query_one("#categories", ListView).focus()

    # ------------------------------------------------------------ field state

    def file_value(self, field):
        """The value currently on disk, falling back to the declared default."""
        return self.file_values.get(field.key, field.default)

    def effective_value(self, field):
        """The value that would be written: the pending edit, else the file."""
        return self.pending.get(field.key, self.file_value(field))

    def is_dirty(self, field):
        """True when saving would change the file for this field."""
        if field.read_only:
            return False
        if field.key in self.marked_for_removal:
            return True
        if field.key not in self.pending:
            return False
        if field.kind == KIND_BOOL:
            # ``GITPR_X=1`` and ``GITPR_X=true`` are the same setting: comparing
            # the raw strings would report a change that saving would not make.
            return _as_bool(self.pending[field.key]) != _as_bool(self.file_value(field))
        return self.pending[field.key] != self.file_value(field)

    def dirty_fields(self):
        return [field for field in FIELDS if self.is_dirty(field)]

    def _record(self, key, value):
        """Stores an edit; a secret emptied back out is no longer an edit."""
        field = FIELDS_BY_KEY.get(key)
        if field is None:
            return
        if field.kind == KIND_SECRET and not value:
            self.pending.pop(key, None)
        else:
            self.pending[key] = value
        self._update_dirty_indicator()

    def _update_dirty_indicator(self):
        count = len(self.dirty_fields()) + len(self.dirty_skills())
        indicator = self.query_one("#dirty_indicator", Static)
        if count:
            indicator.update(__("● {count} unsaved change(s)", count=count))
        else:
            indicator.update("")

    # ----------------------------------------------------------------- skills
    # The only part of this screen that belongs to the PROJECT rather than to
    # ~/.gitpr/.env: it edits the AI instruction files in .gitpr/skill/ of the
    # folder gitpr was started in.
    #
    # The list is NOT discovered from that folder — it is the fixed registry in
    # config.SKILL_FILES_BY_TYPE, the same one get_skill_context() reads. A file
    # sitting in the folder that the registry does not list is not a skill and
    # is never shown, let alone written: .gitpr.linter.yml is the standing
    # example, a rule catalogue with a screen of its own elsewhere.

    def _load_skills(self):
        """Reads every supported skill from disk into the screen state."""
        self.skill_files = {}
        self.skill_status = {}
        for skill_type in SKILL_TYPES:
            state, detail = skill_file_status(skill_type)
            if state in (_SKILL_MISSING, _SKILL_UNREADABLE):
                self.skill_files[skill_type] = ""
            else:
                try:
                    self.skill_files[skill_type] = read_skill_file(
                        skill_file_path(skill_type)
                    )
                except OSError as exc:
                    # os.access() said it was readable and the read disagreed —
                    # an ACL, a network share. Lock the editor rather than let
                    # the user type into something that cannot be saved.
                    state, detail = _SKILL_UNREADABLE, str(exc)
                    self.skill_files[skill_type] = ""
            self.skill_status[skill_type] = (state, detail)

    def _skill_state(self, skill_type):
        return self.skill_status.get(skill_type, (_SKILL_MISSING, ""))[0]

    def _skill_item_text(self, skill_type):
        """One list entry: the skill name, plus whatever is worth flagging."""
        notes = []
        if skill_type in self.skill_pending:
            notes.append(__("● edited"))
        state = self._skill_state(skill_type)
        if state == _SKILL_MISSING:
            notes.append(__("not in this project"))
        elif state in (_SKILL_READONLY, _SKILL_UNREADABLE):
            notes.append(__("read only"))
        label = SKILL_LABELS.get(skill_type, skill_type)
        return f"{label}   {'   '.join(notes)}" if notes else label

    def _skill_title(self, skill_type):
        """The file the editor is showing, named, plus why it may be locked."""
        name = SKILL_FILES_BY_TYPE[skill_type]
        state = self._skill_state(skill_type)
        if state == _SKILL_READONLY:
            return f"{name}   {__('read only')}"
        if state == _SKILL_UNREADABLE:
            return f"{name}   {__('⚠ could not be read')}"
        return name

    def _refresh_skill_item(self, skill_type):
        item = self.query_one(f"#{_SKILL_ITEM_PREFIX}{skill_type}", ListItem)
        item.query_one(Static).update(self._skill_item_text(skill_type))

    def _refresh_skill_list(self):
        for skill_type in SKILL_TYPES:
            self._refresh_skill_item(skill_type)

    def _apply_skill_controls(self, skill_type):
        """Matches the widgets to what the file on disk allows.

        The editor is hidden, not merely locked, when the skill is absent: an
        empty box would read as "this skill is empty", which is the opposite of
        what is true. read_only is set in every non-editable case as well, so a
        stray focus cannot type into a box that has nowhere to save.
        """
        state = self._skill_state(skill_type)
        editor = self.query_one(f"#{_SKILL_EDITOR_ID}", TextArea)
        editor.read_only = state != _SKILL_EDITABLE
        editor.display = state != _SKILL_MISSING

        absent = self.query_one(f"#{_SKILL_ABSENT_NOTE_ID}", Static)
        absent.display = state == _SKILL_MISSING
        absent.update(
            __(
                "This project has no {name} file yet.",
                name=SKILL_FILES_BY_TYPE[skill_type],
            )
        )

        self.query_one(f"#{_SKILL_ACTIONS_ID}", Horizontal).display = (
            state == _SKILL_MISSING
        )
        # A detail on an absent skill is the folder itself, handed over by
        # skill_file_status() when even a download could not be written there.
        detail = self.skill_status.get(skill_type, (_SKILL_MISSING, ""))[1]
        self.query_one(f"#{_SKILL_DOWNLOAD_ID}", Button).disabled = bool(detail)
        self._set_skill_status(
            __("⚠ the folder {path} is not writable", path=detail) if detail else ""
        )

        self.query_one("#skill_editor_title", Static).update(
            self._skill_title(skill_type)
        )

    def _select_skill(self, skill_type):
        """Loads a skill into the editor and matches the widgets to its state.

        Safe to repeat: whatever is in the editor is mirrored in skill_pending
        by the Changed handler, so reading it back from there returns exactly
        what the user sees. Navigating away and back cannot lose an edit.
        """
        self.selected_skill = skill_type
        text = self.skill_pending.get(
            skill_type, self.skill_files.get(skill_type, "")
        )
        # load_text(), never an assignment to .text: it clears the undo history,
        # which would otherwise still hold the previous skill and let Ctrl+Z
        # splice one skill's content into another's file.
        self.query_one(f"#{_SKILL_EDITOR_ID}", TextArea).load_text(text)
        self._apply_skill_controls(skill_type)

    def _set_skill_status(self, text):
        self.query_one(f"#{_SKILL_STATUS_ID}", Static).update(text)

    def dirty_skills(self):
        """The skills holding an edit that saving would write to the file."""
        return [
            skill_type for skill_type in SKILL_TYPES if skill_type in self.skill_pending
        ]

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Tracks an edit by comparing with the file, not with a load flag.

        load_text() posts Changed as well — it is how the widget announces the
        new content — and the message is delivered later, on its own pump, so a
        flag set around the programmatic load would already be clear by the time
        this runs. Comparing against the text on disk is idempotent and
        order-independent: it states what is true whenever it happens to land.
        """
        if event.text_area.id != _SKILL_EDITOR_ID:
            return
        skill_type = self.selected_skill
        if skill_type is None:
            return
        if event.text_area.text == self.skill_files.get(skill_type, ""):
            self.skill_pending.pop(skill_type, None)
        else:
            self.skill_pending[skill_type] = event.text_area.text
        self._refresh_skill_item(skill_type)
        self._update_dirty_indicator()

    def _focused_skill(self):
        """The skill whose pane holds the focused widget, or None.

        Walks up instead of reading ids: the list, the editor and the download
        button all sit inside the pane, and Ctrl+R on any of them means "put the
        file back".
        """
        widget = self.focused
        while widget is not None:
            if getattr(widget, "id", None) == _SKILL_PANE_ID:
                return self.selected_skill
            widget = widget.parent
        return None

    def _revert_skill(self, skill_type):
        """Ctrl+R inside the Skills pane: drop the edit, keep the file.

        Downloading the published template would be the other reading of
        "restore", and it is destructive — it stays behind its own button.
        """
        name = SKILL_FILES_BY_TYPE[skill_type]
        if skill_type not in self.skill_pending:
            self.notify(
                __("{name} already uses the default value.", name=name),
                severity="information",
            )
            return
        self.skill_pending.pop(skill_type, None)
        self.query_one(f"#{_SKILL_EDITOR_ID}", TextArea).load_text(
            self.skill_files.get(skill_type, "")
        )
        self._refresh_skill_item(skill_type)
        self._update_dirty_indicator()
        self.notify(__("{name} restored from the file on disk.", name=name))

    def _start_skill_download(self):
        skill_type = self.selected_skill
        if skill_type is None:
            return
        button = self.query_one(f"#{_SKILL_DOWNLOAD_ID}", Button)
        if button.disabled:
            return
        button.disabled = True
        self._set_skill_status(__("Downloading…"))
        self._run_skill_download(skill_type)

    @work(thread=True)
    def _run_skill_download(self, skill_type):
        """Fetches the published template off the event loop.

        src.core is imported inside the worker, for the reason stated at the top
        of this module: a module-level import would pull the AI SDKs into a
        screen that opens on every ``gitpr config``. _quiet_output() covers the
        one message the loader prints without honouring its own quiet flag —
        resolve_skill_path()'s note about moving a legacy root file.
        """
        local_name = SKILL_FILES_BY_TYPE[skill_type]
        try:
            with _quiet_output():
                from src.core import download_skill_file

                download_skill_file(
                    local_name, skill_template_remote_name(local_name), quiet=True
                )
        except Exception:
            # download_skill_file() reports its own failures and never raises.
            # The file on disk is the verdict, and it is read below.
            pass
        self.call_from_thread(self._after_skill_download, skill_type)

    def _after_skill_download(self, skill_type):
        """Main thread: the file on disk decides, not the download's report.

        That also covers the legacy copy at the project root, which
        download_skill_file() MOVES into .gitpr/skill/ instead of downloading —
        the file is there afterwards either way, and this is what sees it.
        """
        name = SKILL_FILES_BY_TYPE[skill_type]
        self._load_skills()
        self._refresh_skill_list()
        if self.selected_skill != skill_type:
            # The user moved on while the download ran. The pane now belongs to
            # another skill, whose controls _apply_skill_controls() has already
            # set; touching them here would undo that.
            return
        self._select_skill(skill_type)
        if self._skill_state(skill_type) == _SKILL_MISSING:
            self._set_skill_status(__("✖ not updated"))
            self.notify(
                __(
                    "Could not download {name}. The skill file was not created.",
                    name=name,
                ),
                severity="error",
                timeout=8,
            )
            return
        self._set_skill_status(__("✔ {name} downloaded.", name=name))
        self.notify(
            __("✔ {name} downloaded.", name=name), severity="information", timeout=8
        )

    # --------------------------------------------------------------- events

    def action_show_help(self) -> None:
        self.push_screen(ConfigHelpScreen())

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_open_doc(self) -> None:
        """Opens the technical page of the section on screen, if it has one."""
        doc = self.category_doc(self.selected_category())
        if not doc:
            return
        import webbrowser

        webbrowser.open(doc_url(doc))

    def on_input_changed(self, event: Input.Changed) -> None:
        widget_id = event.input.id or ""
        if widget_id == "search":
            self._render_view(event.value)
        elif widget_id.startswith(_VALUE_PREFIX):
            self._record(widget_id[len(_VALUE_PREFIX) :], event.value)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        widget_id = event.switch.id or ""
        if widget_id == "show_advanced":
            self.show_advanced = event.value
            self._apply_advanced_visibility()
            if not self.show_advanced and self.selected_category() == "advanced":
                # The category just vanished; do not leave the cursor on it.
                self.query_one("#categories", ListView).index = 0
            self._render_view(self.query_one("#search", Input).value)
        elif widget_id.startswith(_VALUE_PREFIX):
            self._record(
                widget_id[len(_VALUE_PREFIX) :], "true" if event.value else "false"
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        widget_id = event.select.id or ""
        if not widget_id.startswith(_VALUE_PREFIX):
            return
        key = widget_id[len(_VALUE_PREFIX) :]
        value = event.value
        self._record(key, "" if value is Select.BLANK else str(value))
        if key in VISIBILITY_CONTROLLERS:
            # Picking another provider or forge re-filters the pane right here,
            # without waiting for a save. The pending value set above is what
            # the gates read, so the new selection is already in effect.
            self._render_view(self.query_one("#search", Input).value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Runs the action button of a field row.

        The prefix guard is not decorative: the modals handle their own buttons
        without stopping the message, so btn_discard, btn_keep and help_close
        all arrive at this handler too.
        """
        widget_id = event.button.id or ""
        if widget_id == "doc_open":
            self.action_open_doc()
            return
        if widget_id == _SKILL_DOWNLOAD_ID:
            self._start_skill_download()
            return
        if not widget_id.startswith(_ACTION_PREFIX):
            return
        field = FIELDS_BY_KEY.get(widget_id[len(_ACTION_PREFIX) :])
        if field is None or field.key not in _DOWNLOAD_SOURCES:
            return

        if field.key == "LANG_VERSION" and _current_lang().startswith("en"):
            # English is the source language: get_translations() returns an
            # empty dict without touching the network. Say plainly that there
            # is nothing to fetch instead of reporting a failed download.
            self.notify(
                __(
                    "English needs no translation pack — there is nothing to download."
                ),
                severity="information",
            )
            return

        event.button.disabled = True
        self._set_action_status(field.key, __("Downloading…"))
        self._run_download(field)

    def _set_action_status(self, key, text):
        row = self.rows.get(key)
        if row is not None:
            row.set_action_status(text)

    @work(thread=True)
    def _run_download(self, field):
        """Runs the loader off the event loop, then reports the file's state.

        No exclusive=True: every action button shares this method, and an
        exclusive worker cancels the previous one — clicking a second button
        would kill the download already in flight instead of letting it finish.
        """
        try:
            with _quiet_output():
                _DOWNLOAD_SOURCES[field.key]()
        except Exception:
            # A loader swallows its own failure and falls back to the copy
            # already on disk; the marker check below is the verdict.
            pass
        self.call_from_thread(self._after_download, field)

    def _after_download(self, field):
        """Main thread: re-reads the file and says what it holds now.

        The proof is read back from the FILE, never from os.getenv: every
        load_dotenv() in the project runs with override=False, so the process
        environment still holds the value from before the download and would
        report a marker that was already stale as if it were current.
        """
        self.file_values = read_env_file_values()
        marker_key = _marker_key(field)
        expected = _expected_marker_value(field)
        actual = self.file_values.get(marker_key, "")

        row = self.rows.get(field.key)
        if row is not None:
            if field.kind == KIND_WORDS:
                row.set_words(self.file_values.get(field.key, ""))
            else:
                row.mark_downloaded()
            row.set_action_enabled(True)

        if expected and actual == expected:
            if marker_key != field.key:
                # The marker has a row of its own (the word list is proven by
                # its version line), and that row is now out of date.
                marker_row = self.rows.get(marker_key)
                if marker_row is not None:
                    marker_row.mark_downloaded()
            self._set_action_status(field.key, __("✔ {version}", version=actual))
            self.notify(
                __(
                    "{name} is up to date ({version}).",
                    name=field.label,
                    version=actual,
                ),
                severity="information",
                timeout=8,
            )
        else:
            self._set_action_status(field.key, __("✖ not updated"))
            self.notify(
                __(
                    "Could not download {name}. The previous copy stays in use.",
                    name=field.label,
                ),
                severity="error",
                timeout=8,
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter inside the search box hands the focus back to the sidebar."""
        if event.input.id == "search":
            self.query_one("#categories", ListView).focus()

    def on_key(self, event) -> None:
        """Escape clears the search before it can reach the quit binding."""
        if event.key != "escape":
            return
        search = self.query_one("#search", Input)
        if search.has_focus or search.value:
            search.value = ""
            self.query_one("#categories", ListView).focus()
            self._render_view()
            event.stop()

    # -------------------------------------------------------- restore default

    def _focused_field(self):
        """The field whose row holds the focused widget, if any.

        Both prefixes matter: the control carries value_*, and the action button
        carries act_* — clicking it moves the focus there, so without the row_
        branch Ctrl+R would silently do nothing on a focused button.
        """
        widget = self.focused
        while widget is not None:
            widget_id = getattr(widget, "id", None) or ""
            if widget_id.startswith(_VALUE_PREFIX):
                return FIELDS_BY_KEY.get(widget_id[len(_VALUE_PREFIX) :])
            if widget_id.startswith(_ROW_PREFIX):
                return FIELDS_BY_KEY.get(widget_id[len(_ROW_PREFIX) :])
            widget = widget.parent
        return None

    def action_reset_field(self) -> None:
        """Ctrl+R: drop the line from the .env so the default applies again."""
        skill_type = self._focused_skill()
        if skill_type is not None:
            self._revert_skill(skill_type)
            return
        field = self._focused_field()
        if field is None:
            return
        if field.read_only:
            self.notify(__("This field is managed by GitPR."), severity="warning")
            return

        row = self.rows.get(field.key)
        if field.key in self.marked_for_removal:
            self.marked_for_removal.discard(field.key)
            if row is not None:
                row.set_removal_mark(False)
            self._update_dirty_indicator()
            return

        if field.key not in self.file_values:
            # "{name}", not "{key}": __()'s first parameter is itself named key.
            self.notify(
                __("{name} already uses the default value.", name=field.key),
                severity="information",
            )
            return

        # The mark supersedes any edit typed into the field.
        self.pending.pop(field.key, None)
        self.marked_for_removal.add(field.key)
        if row is not None:
            row.set_removal_mark(True)
        self._update_dirty_indicator()

    # ------------------------------------------------------------------ exit

    def action_quit(self) -> None:
        # A pending skill edit is as unsaved as an .env one, so it opens the
        # same confirmation rather than leaving silently.
        if self.dirty_fields() or self.dirty_skills():
            self.push_screen(ConfirmDiscardScreen(), self._after_discard_confirmation)
            return
        self.exit()

    def _after_discard_confirmation(self, discard) -> None:
        if discard:
            self.exit()

    # ------------------------------------------------------------------ save

    def action_save(self) -> None:
        if self._saving:
            return
        plan = self._build_plan()

        if plan["errors"]:
            self._reveal(next(iter(plan["errors"])))
            self._show_errors(plan["errors"])
            self.notify(
                __(
                    "{count} field(s) need attention before saving.",
                    count=len(plan["errors"]),
                ),
                severity="error",
            )
            return

        if not plan["values"] and not plan["removals"] and not plan["skills"]:
            self.notify(__("Nothing to save."), severity="information")
            return

        if not plan["secrets"]:
            self._apply_save(plan, [])
            return

        self._saving = True
        self.notify(__("Checking the credentials…"), severity="information")
        self._validate_secrets(plan)

    def _build_plan(self):
        """Collects the pending changes and validates everything offline.

        Reads self.pending, never the widgets: the field being validated may
        well be in a category that is not on screen right now. The skill edits
        ride along in their own bucket — a skill is a file, not an .env key, so
        the loop below must never turn one into a value to write to the file.
        """
        plan = {
            "values": {},
            "secrets": {},
            "removals": [],
            "errors": {},
            "skills": {
                skill_type: self.skill_pending[skill_type]
                for skill_type in self.dirty_skills()
            },
        }

        for field in FIELDS:
            if field.read_only:
                continue
            if field.key in self.marked_for_removal:
                if field.key in self.file_values:
                    plan["removals"].append(field.key)
                continue
            if not self.is_dirty(field):
                continue

            value = self.effective_value(field)
            error = validate_field_value(field, value)
            if error:
                plan["errors"][field.key] = error
                continue

            if field.kind == KIND_SECRET and field.validator:
                plan["secrets"][field.key] = value
            plan["values"][field.key] = value

        return plan

    def _reveal(self, key):
        """Brings the row holding *key* on screen so its error is visible.

        Navigating to the category is not always enough: a field gated out by
        show_if would stay hidden there, and the save summary would point at a
        row the user cannot see. The search is the one view that ignores the
        gates, so a hidden field is reached through it instead.
        """
        field = FIELDS_BY_KEY.get(key)
        if field is None:
            return
        search = self.query_one("#search", Input)
        if search.value:
            search.value = ""
        if field.advanced and not self.show_advanced:
            # The switch re-enters this handler, so stop here and let it finish.
            self.query_one("#show_advanced", Switch).value = True
            return
        if not self.show_if_satisfied(field):
            search.value = field.key
            search.focus()
            return
        list_view = self.query_one("#categories", ListView)
        index = self.sidebar_categories().index(field.category)
        if list_view.index != index:
            list_view.index = index
        self._render_view()

    def _show_errors(self, errors):
        """Annotates the rows on screen; the rest follow as the user fixes them."""
        for key, row in self.rows.items():
            row.set_error(f"✖ {errors[key]}" if key in errors else "")
        first = self.rows.get(next(iter(errors)))
        if first is not None:
            first.scroll_visible()

    @work(thread=True, exclusive=True)
    def _validate_secrets(self, plan) -> None:
        """Probes the typed credentials off the UI thread, then saves."""
        blocked = {}
        warnings = []
        for key, plaintext in plan["secrets"].items():
            kind, message = self._probe_secret(key, plaintext, plan)
            if kind == VALIDATION_AUTH:
                blocked[key] = message
            elif kind == VALIDATION_NETWORK:
                warnings.append(message)
        self.call_from_thread(self._finish_save, plan, blocked, warnings)

    def _probe_secret(self, key, plaintext, plan):
        """Returns (failure_kind, message) for one typed credential."""
        validator = FIELDS_BY_KEY[key].validator
        if validator == VALIDATOR_AI_KEY:
            is_valid, kind, message = validate_ai_key(
                _SECRET_PROVIDERS.get(key, ""), plaintext
            )
            return ("" if is_valid else kind), message
        if validator == VALIDATOR_SCM_TOKEN:
            return self._probe_scm_token(plaintext, plan)
        return "", ""

    def _probe_scm_token(self, plaintext, plan):
        """Validates a forge token through the provider's own test_connection.

        The forge comes from the state the save would produce, so switching
        GITPR_SCM_PROVIDER and typing the new token in the same pass validates
        against the new forge rather than the one still on disk.
        """
        from src.infrastructure.scm import ScmProviderError, resolve_scm_provider

        provider_key = self._planned_value("GITPR_SCM_PROVIDER", plan) or "github"
        extra = {
            name: self._planned_value(f"GITPR_SCM_{name.upper()}", plan) or None
            for name in ("base_url", "organization", "project", "username")
        }

        try:
            provider = resolve_scm_provider(
                {"provider": provider_key, "token": plaintext, **extra}
            )
            if provider.test_connection():
                return "", ""
            return VALIDATION_AUTH, __(
                "{provider} rejected the token.", provider=provider_key
            )
        except ScmProviderError as exc:
            if exc.http_status in (401, 403):
                return VALIDATION_AUTH, __(
                    "{provider} rejected the token.", provider=provider_key
                )
            # http_status 0 means the request never reached the forge.
            return VALIDATION_NETWORK, __(
                "Could not reach {provider}.", provider=provider_key
            )
        except Exception as exc:
            return VALIDATION_NETWORK, __(
                "Could not check the token: {error}", error=str(exc)
            )

    def _planned_value(self, key, plan):
        """The value a key would hold once the pending changes are saved."""
        if key in plan["values"]:
            return plan["values"][key]
        if key in self.file_values:
            return self.file_values[key]
        field = FIELDS_BY_KEY.get(key)
        return field.default if field else ""

    def _finish_save(self, plan, blocked, warnings):
        self._saving = False
        if blocked:
            self._reveal(next(iter(blocked)))
            self._show_errors(blocked)
            self.notify(
                __("The credential was refused, nothing was saved."),
                severity="error",
            )
            return
        self._apply_save(plan, warnings)

    def _apply_save(self, plan, warnings):
        values = dict(plan["values"])
        for key in plan["secrets"]:
            # Encrypted only now, so a rejected credential never reaches disk.
            values[key] = encrypt_data(values[key])

        try:
            save_config_values(values)
            for key in plan["removals"]:
                remove_config_value(key)
        except Exception as exc:
            # A failure here would otherwise take the screen down with it and
            # lose every pending edit, so it is reported instead.
            self.notify(
                __("Could not write {path}: {error}", path=ENV_FILE, error=str(exc)),
                severity="error",
            )
            return

        for message in warnings:
            self.notify(message, severity="warning")

        self._after_save(plan, values, self._write_skills(plan["skills"]))

    def _write_skills(self, skills):
        """Writes the edited skill files, one failure at a time.

        Returns the types actually written. A file that could not be written is
        reported and LEFT PENDING, so the edit stays on screen and nothing the
        user typed is lost — the same reason the caller above reports its own
        failure instead of letting it take the screen down.
        """
        written = []
        for skill_type, text in skills.items():
            path = skill_file_path(skill_type)
            try:
                write_skill_file(path, text)
            except Exception as exc:
                # One unwritable file must not cost the user the other edits.
                self.notify(
                    __("Could not write {path}: {error}", path=path, error=str(exc)),
                    severity="error",
                )
                continue
            written.append(skill_type)
        return written

    def _after_save(self, plan, values, written_skills=()):
        from dotenv import load_dotenv

        # override=True on purpose: the user just edited the file, so the
        # running process must stop using the older process environment value.
        load_dotenv(ENV_FILE, override=True)

        self.file_values = read_env_file_values()
        self.shadowed_keys = {
            key
            for key in self.file_values
            if key in AMBIENT_ENV_KEYS and os.environ.get(key) not in (None, "")
        }
        self.pending.clear()
        self.marked_for_removal.clear()
        for key, row in self.rows.items():
            row.set_removal_mark(False)
            row.set_error("")

        # Only what was written stops being pending: a skill whose write failed
        # is still an unsaved edit, and it has to stay legible as one.
        for skill_type in written_skills:
            self.skill_pending.pop(skill_type, None)
        self._load_skills()
        self._refresh_skill_list()
        if self.selected_skill is not None:
            self._select_skill(self.selected_skill)

        if "GITPR_LANG" in values or "GITPR_LANG" in plan["removals"]:
            language = values.get("GITPR_LANG", "")
            if language:
                set_lang(language)
            # __() is bound at import time in most modules, so the switch only
            # takes full effect on the next launch — the user is told rather
            # than left with a half-translated screen.
            self.notify(
                __("Language applied. Restart GitPR for the whole interface."),
                severity="warning",
            )

        self._render_view(self.query_one("#search", Input).value)
        self._update_dirty_indicator()
        self.notify(
            __(
                "{count} setting(s) saved.",
                count=len(values) + len(plan["removals"]) + len(written_skills),
            ),
            severity="information",
        )


def launch_config_app():
    """Entry point: opens the configuration screen."""
    ConfigApp().run()
