"""Declarative schema of the user-facing configuration surface.

This module is pure data: it describes every ~/.gitpr/.env variable that the
`gitpr config` TUI exposes, and it is the single source of truth for the menu
categories, the widgets, the validation rules and the labels.

The labels and descriptions are literal `__("...")` calls on purpose — the AST
scanner in tests/test_i18n.py only finds statically resolvable keys, so a
computed label would silently become an orphan key and break the suite.

Deliberately NOT here: CI / GITHUB_ACTIONS — process environment markers, not
.env settings.
"""

from dataclasses import dataclass
from string import Formatter

from src.i18n import __

# Widget kinds. Each one maps to a different control in ui/config_app.py.
KIND_BOOL = "bool"
KIND_INT = "int"
KIND_STR = "str"
KIND_ENUM = "enum"
KIND_TEMPLATE = "template"
KIND_PATH = "path"
KIND_SECRET = "secret"
KIND_VERSION = "version"
# A pipe/semicolon joined list rendered read-only as a wrapped list, not as a
# one-line text box.
KIND_WORDS = "words"

KINDS = (
    KIND_BOOL,
    KIND_INT,
    KIND_STR,
    KIND_ENUM,
    KIND_TEMPLATE,
    KIND_PATH,
    KIND_SECRET,
    KIND_VERSION,
    KIND_WORDS,
)

# Per-field action buttons rendered by the TUI, dispatched by name in
# ui/config_app.py (_ACTION_HANDLERS).
ACTION_DOWNLOAD = "download"
ACTION_DOWNLOAD_WORDS = "download_words"
ACTIONS = (ACTION_DOWNLOAD, ACTION_DOWNLOAD_WORDS)

# Which code constant a version marker is compared against by its loader. The
# TUI shows that constant when the marker is absent, so a read-only box is
# never blank. Maps to VERSION_SOURCES in ui/config_app.py.
VERSION_LANG = "lang"
VERSION_SCRIPTS = "scripts"
VERSION_SOURCES = (VERSION_LANG, VERSION_SCRIPTS)

# The only literals every boolean reader in the project agrees on. Anything
# outside this set is a real trap, because the two readers disagree:
#   _env_flag() [main.py]            — true only for true/1/yes/y
#   _env_bool_default_true() [config.py] — false only for false/0/no/off/n
# So "maybe" is false to the first and true to the second, and "on" — which
# looks symmetrical with "off" — is false to the first and true to the second.
# "off" is unambiguous (false to both); "on" is not. Do not add it.
BOOL_TRUE = ("true", "1", "yes", "y")
BOOL_FALSE = ("false", "0", "no", "off", "n")

# Validators are resolved by name in the TUI so this module stays import-light.
VALIDATOR_AI_KEY = "ai_key"
VALIDATOR_SCM_TOKEN = "scm_token"

# Placeholders accepted inside OUTPUT_FILE_NAME* templates. resolve_output_path()
# calls .format(branch=..., datetime=...), so anything else raises KeyError and
# a template without {datetime} makes every run overwrite the previous artifact.
TEMPLATE_PLACEHOLDERS = ("branch", "datetime")
TEMPLATE_REQUIRED = ("datetime",)


@dataclass(frozen=True)
class ConfigField:
    """One editable entry of ~/.gitpr/.env."""

    key: str
    label: str
    description: str
    category: str
    kind: str
    default: str = ""
    choices: tuple = ()
    # Optional (value, label) pairs for an enum, so a choice can read as
    # something other than its raw value — the language codes, mostly. A value
    # missing from here falls back to the value itself, which is what every
    # other enum wants.
    choice_labels: tuple = ()
    advanced: bool = False
    validator: str = ""
    read_only: bool = False
    # Themed sub-header this field renders under inside its category. "" means
    # no header. A group id belongs to ONE category only: the header widget id
    # is derived from it ("grp_<id>"), so reusing an id elsewhere would collide
    # and show the wrong label.
    group: str = ""
    # ((controlling_key, allowed_values), ...) — ANDed. The controlling value is
    # compared against the field's EFFECTIVE value (pending edit first, file
    # second), so the pane re-filters as soon as the selector changes instead of
    # only after a save.
    show_if: tuple = ()
    # Constant the field falls back to when its marker is absent from the file.
    version_source: str = ""
    # Action button rendered next to the control, dispatched by ACTION_*.
    action: str = ""


@dataclass(frozen=True)
class Group:
    """A themed sub-header inside a category."""

    id: str
    label: str


@dataclass(frozen=True)
class Category:
    """A sidebar entry of the configuration screen."""

    id: str
    label: str
    description: str = ""
    # File name of this section's page under docs/, linked from the screen.
    # "" means the section has no technical page (the synthesised "unknown").
    doc: str = ""


CATEGORIES = (
    Category(
        "general",
        __("General"),
        __("Language and global preferences."),
        doc="config-tui.md",
    ),
    Category(
        "ai",
        __("AI Providers"),
        __("Default engine, models, timeouts and API keys."),
        doc="providers-ia.md",
    ),
    Category(
        "pr",
        __("Pull Request"),
        __("Default behaviour of the pull request flow."),
        doc="pull-request-publication.md",
    ),
    Category(
        "review",
        __("Code Review"),
        __("Local review, full review and single file audit."),
        doc="code-review-ia.md",
    ),
    Category(
        "issue",
        __("Issue"),
        __("Issue drafts generated from a diff, history or blame."),
        doc="gitpr-issue-option.md",
    ),
    Category(
        "blame",
        __("Blame"),
        __("Code archaeology reports."),
        doc="blame-arqueologo.md",
    ),
    Category(
        "linter",
        __("Linter"),
        __("Static analysis of the local changes."),
        doc="linter-regras-customizadas.md",
    ),
    Category(
        "release",
        __("Release"),
        __("Changelog generation and release publishing."),
        doc="release-notes.md",
    ),
    Category(
        "fix",
        __("Fix"),
        __("Review findings turned into patches, and the safety rules of a batch."),
        doc="fix-command.md",
    ),
    Category(
        "split",
        __("Split"),
        __("A mixed working tree turned into atomic commits, one concern each."),
        doc="split-command.md",
    ),
    Category(
        "scm",
        __("SCM / Forge"),
        __("GitHub, GitLab, Bitbucket and Azure DevOps connection."),
        doc="scm-multiforge.md",
    ),
    Category(
        "diff",
        __("Diff Filters"),
        __("Paths excluded from every diff sent to the AI."),
        doc="smart-excludes.md",
    ),
    Category(
        "skills",
        __("Skills"),
        __(
            "Skill files are the AI instructions of this project, read from .gitpr/skill. Edit one here and press F2 to save it."
        ),
        doc="skill-template.md",
    ),
    Category(
        "advanced",
        __("Advanced"),
        __("Internal markers and maintenance settings."),
        doc="version-markers.md",
    ),
)

# skill type -> the name shown in the Skills section. The keys are the ones in
# config.SKILL_FILES_BY_TYPE; a test asserts the two agree, because a type
# missing here would render a blank sidebar entry and one in excess would be
# unreachable. Literal __() calls for the same reason as everywhere else in this
# module, and the labels reuse the wording of the matching categories.
SKILL_LABELS = {
    "commit": __("Commit"),
    "pr": __("Pull Request"),
    "review": __("Code Review"),
    "filereview": __("File Review"),
    "issue": __("Issue"),
    "blame": __("Blame"),
    "release": __("Release"),
    "fix": __("Fix"),
}

# Sub-headers shown inside a category. Generic words go through __(); forge and
# provider names stay literal, like the display names in
# src/infrastructure/scm/factory.py.
GROUPS = (
    Group("github", "GitHub"),
    Group("bitbucket", "Bitbucket"),
    Group("azure_devops", "Azure DevOps"),
    Group("spinner", __("Spinner")),
    Group("hooks", __("Git Hooks")),
    Group("downloads", __("Downloads")),
)

FIELDS = (
    # ------------------------------------------------------------------ General
    ConfigField(
        key="GITPR_LANG",
        label=__("Interface Language"),
        description=__(
            "Language of the interface and of the generated content. Leave it empty to detect it from the operating system."
        ),
        category="general",
        kind=KIND_ENUM,
        default="",
        choices=("", "en_us", "pt_br", "pt_pt", "es_es", "fr_fr"),
        choice_labels=(
            ("en_us", __("English")),
            ("pt_br", __("Portuguese (Brazil)")),
            ("pt_pt", __("Portuguese (Portugal)")),
            ("es_es", __("Spanish (Spain)")),
            ("fr_fr", __("French (France)")),
        ),
    ),
    ConfigField(
        key="GITPR_COAUTHOR",
        label=__("Co-author Trailer"),
        description=__(
            "Appends the GitPR co-author trailer to the commit messages generated by the tool."
        ),
        category="general",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_BADGE",
        label=__("Pull Request Badge"),
        description=__(
            "Adds a GitPR badge with the linter counts to published pull request bodies. Enabled by default; false hides it."
        ),
        category="general",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_SHOW_LOGS",
        label=__("Save General Logs"),
        description=__(
            "Writes one line per command to ~/.gitpr/logs, in a daily file named after the date."
        ),
        category="general",
        kind=KIND_BOOL,
        default="true",
    ),
    # ------------------------------------------------------------ AI providers
    # Only the fields of the selected engine are shown — see the show_if rules
    # below. "" is a real state: get_ai_provider() only falls back to gemini
    # when the key is ABSENT, and an empty value sends setup_environment() to
    # its interactive prompt.
    ConfigField(
        key="DEFAULT_AI_PROVIDER",
        label=__("Default Provider"),
        description=__(
            "Engine used when no provider is forced with the --provider flag. When empty, GitPR asks again on the next run."
        ),
        category="ai",
        kind=KIND_ENUM,
        default="gemini",
        choices=("", "gemini", "deepseek", "ollama"),
        choice_labels=(("", __("(not configured)")),),
    ),
    ConfigField(
        key="GITPR_AI_TIMEOUT",
        label=__("AI Timeout"),
        description=__(
            "Maximum time in seconds to wait for a single AI response."
        ),
        category="ai",
        kind=KIND_INT,
        default="180",
    ),
    ConfigField(
        key="GEMINI_API_MODEL_PRIMARY",
        label=__("Gemini Advanced Model"),
        description=__("Model used for the complex tasks."),
        category="ai",
        kind=KIND_STR,
        default="gemini-pro-latest",
        show_if=(("DEFAULT_AI_PROVIDER", ("gemini",)),),
    ),
    ConfigField(
        key="GEMINI_API_MODEL_SECONDARY",
        label=__("Gemini Fast Model"),
        description=__("Model used for the simple tasks."),
        category="ai",
        kind=KIND_STR,
        default="gemini-flash-lite-latest",
        show_if=(("DEFAULT_AI_PROVIDER", ("gemini",)),),
    ),
    ConfigField(
        key="GEMINI_API_KEY_ENCRYPTED",
        label=__("Gemini API Key"),
        description=__(
            "Stored encrypted with the local key. The value is never displayed back."
        ),
        category="ai",
        kind=KIND_SECRET,
        default="",
        validator=VALIDATOR_AI_KEY,
        show_if=(("DEFAULT_AI_PROVIDER", ("gemini",)),),
    ),
    ConfigField(
        key="DEEPSEEK_API_MODEL_PRIMARY",
        label=__("DeepSeek Advanced Model"),
        description=__("Model used for the complex tasks."),
        category="ai",
        kind=KIND_STR,
        default="deepseek-v4-pro",
        show_if=(("DEFAULT_AI_PROVIDER", ("deepseek",)),),
    ),
    ConfigField(
        key="DEEPSEEK_API_MODEL_SECONDARY",
        label=__("DeepSeek Fast Model"),
        description=__("Model used for the simple tasks."),
        category="ai",
        kind=KIND_STR,
        default="deepseek-v4-flash",
        show_if=(("DEFAULT_AI_PROVIDER", ("deepseek",)),),
    ),
    ConfigField(
        key="DEEPSEEK_API_KEY_ENCRYPTED",
        label=__("DeepSeek API Key"),
        description=__(
            "Stored encrypted with the local key. The value is never displayed back."
        ),
        category="ai",
        kind=KIND_SECRET,
        default="",
        validator=VALIDATOR_AI_KEY,
        show_if=(("DEFAULT_AI_PROVIDER", ("deepseek",)),),
    ),
    ConfigField(
        key="OLLAMA_API_MODEL_PRIMARY",
        label=__("Ollama Advanced Model"),
        description=__("Local model used for the complex tasks."),
        category="ai",
        kind=KIND_STR,
        default="llama3",
        show_if=(("DEFAULT_AI_PROVIDER", ("ollama",)),),
    ),
    ConfigField(
        key="OLLAMA_API_MODEL_SECONDARY",
        label=__("Ollama Fast Model"),
        description=__("Local model used for the simple tasks."),
        category="ai",
        kind=KIND_STR,
        default="llama3",
        show_if=(("DEFAULT_AI_PROVIDER", ("ollama",)),),
    ),
    # ----------------------------------------------------------- Pull request
    ConfigField(
        key="OUTPUT_FILE_NAME",
        label=__("PR Description Filename"),
        description=__(
            "Name of the generated pull request description file. Placeholders: branch and datetime."
        ),
        category="pr",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_PR_DESC.md",
    ),
    ConfigField(
        key="PR_DEFAULT_BASE",
        label=__("Default Base Branch"),
        description=__(
            "Target branch of the pull request. Leave it empty to detect it automatically."
        ),
        category="pr",
        kind=KIND_STR,
        default="",
    ),
    ConfigField(
        key="GITPR_AUTO_COMMIT",
        label=__("Auto Commit"),
        description=__(
            "Commits automatically instead of asking for confirmation before publishing."
        ),
        category="pr",
        kind=KIND_BOOL,
        default="false",
    ),
    ConfigField(
        key="GITPR_SKIP_LINT",
        label=__("Skip Linter"),
        description=__(
            "Skips the static analysis before the automatic commit."
        ),
        category="pr",
        kind=KIND_BOOL,
        default="false",
    ),
    ConfigField(
        key="GITPR_AUTO_STAGE",
        label=__("Auto Stage"),
        description=__(
            "Stages every unstaged file automatically instead of opening the selection screen."
        ),
        category="pr",
        kind=KIND_BOOL,
        default="false",
    ),
    ConfigField(
        key="GITPR_SKIP_UNSTAGED_CHECK",
        label=__("Skip Unstaged Check"),
        description=__(
            "Skips the verification of pending changes before the AI processing."
        ),
        category="pr",
        kind=KIND_BOOL,
        default="false",
    ),
    ConfigField(
        key="PR_PUBLISH_LOG",
        label=__("Write Publish Log"),
        description=__(
            "Writes a log file of every publication under the local GitPR logs folder."
        ),
        category="pr",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_AUTO_MERGE",
        label=__("Auto Merge"),
        description=__(
            "Merges the pull request right after publishing it, without asking."
        ),
        category="pr",
        kind=KIND_BOOL,
        default="false",
    ),
    ConfigField(
        key="GITPR_SUGGEST_REVIEWERS",
        label=__("Suggest Reviewers"),
        description=__(
            "Computes and suggests reviewers based on the history of the changed files."
        ),
        category="pr",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_REVIEWER_SUGGESTION_TOP_N",
        label=__("Reviewer Suggestions"),
        description=__("How many reviewer candidates are suggested."),
        category="pr",
        kind=KIND_INT,
        default="3",
    ),
    ConfigField(
        key="GITPR_REVIEWER_SUGGESTION_EXCLUDED",
        label=__("Excluded Reviewers"),
        description=__(
            "Comma separated names or e-mails that are never suggested as reviewers."
        ),
        category="pr",
        kind=KIND_STR,
        default="",
    ),
    # ------------------------------------------------------------- Code review
    ConfigField(
        key="OUTPUT_FILE_NAME_REVIEW",
        label=__("Review Filename"),
        description=__(
            "Name of the local code review file. Placeholders: branch and datetime."
        ),
        category="review",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_PR_REVIEW.txt",
    ),
    ConfigField(
        key="OUTPUT_FILE_NAME_FULLREVIEW",
        label=__("Full Review Filename"),
        description=__(
            "Name of the full review file. Placeholders: branch and datetime."
        ),
        category="review",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_PR_FULLREVIEW.txt",
    ),
    ConfigField(
        key="OUTPUT_FILE_NAME_FILEREVIEW",
        label=__("File Audit Filename"),
        description=__(
            "Name of the single file audit report. Placeholders: branch and datetime."
        ),
        category="review",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_FILE_REVIEW.txt",
    ),
    # ------------------------------------------------------------------- Issue
    ConfigField(
        key="OUTPUT_FILE_NAME_ISSUE",
        label=__("Issue Filename"),
        description=__(
            "Name of the saved issue draft. Placeholders: branch and datetime."
        ),
        category="issue",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_ISSUE.md",
    ),
    # ------------------------------------------------------------------- Blame
    ConfigField(
        key="OUTPUT_FILE_NAME_BLAME",
        label=__("Blame Report Filename"),
        description=__(
            "Name of the code archaeology report. Placeholders: branch and datetime."
        ),
        category="blame",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_BLAME_REPORT.md",
    ),
    # ------------------------------------------------------------------ Linter
    ConfigField(
        key="OUTPUT_FILE_NAME_LINTER",
        label=__("Linter Report Filename"),
        description=__(
            "Name of the static analysis report. Placeholders: branch and datetime."
        ),
        category="linter",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_LINTER.md",
    ),
    ConfigField(
        key="GITPR_LINTER_TIMEOUT",
        label=__("External Linter Timeout"),
        description=__(
            "Maximum time in seconds to wait for an external linter executable."
        ),
        category="linter",
        kind=KIND_INT,
        default="120",
    ),
    ConfigField(
        key="GITPR_LINTER_SECURITY",
        label=__("Secret Scanning"),
        description=__(
            "Looks for hardcoded credentials in every file: provider keys, private key blocks, database URLs and password assignments."
        ),
        category="linter",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_LINTER_SECURITY_DISABLED_RULES",
        label=__("Disabled Security Rules"),
        description=__(
            "Security rule names to skip, separated by semicolons. Empty runs all of them."
        ),
        category="linter",
        kind=KIND_STR,
        default="",
    ),
    # ----------------------------------------------------------------- Release
    ConfigField(
        key="GITPR_RELEASE_CHANGELOG_PATH",
        label=__("Changelog Path"),
        description=__(
            "Changelog file updated by the release command. A relative path is resolved against the repository root."
        ),
        category="release",
        kind=KIND_PATH,
        default="CHANGELOG.md",
    ),
    ConfigField(
        key="GITPR_RELEASE_AI_SUMMARY",
        label=__("AI Summary"),
        description=__(
            "Adds an executive summary written by the AI to the release notes."
        ),
        category="release",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_RELEASE_AUTO_BUMP",
        label=__("Auto Version Bump"),
        description=__(
            "Suggests the next semantic version based on the commits of the range."
        ),
        category="release",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT",
        label=__("Publish as Draft"),
        description=__(
            "Creates the release as a draft on the forge. Only GitHub supports drafts."
        ),
        category="release",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="OUTPUT_FILE_NAME_RELEASE",
        label=__("Release Notes Filename"),
        description=__(
            "Name of the generated release notes file. Placeholders: branch and datetime."
        ),
        category="release",
        kind=KIND_TEMPLATE,
        default="{branch}_{datetime}_RELEASE.md",
    ),
    # --------------------------------------------------------------------- Fix
    ConfigField(
        key="GITPR_FIX_SAFE_MAX_LINES_CHANGED",
        label=__("Safe Patch Size"),
        description=__(
            "Maximum number of added plus removed lines a patch may have and still be classified as safe."
        ),
        category="fix",
        kind=KIND_INT,
        default="5",
    ),
    ConfigField(
        key="GITPR_FIX_SAFE_EXCLUDED_PATHS",
        label=__("Sensitive Paths"),
        description=__(
            "Semicolon separated glob patterns a patch may not touch and still be safe (migrations, workflows, containers, infrastructure)."
        ),
        category="fix",
        kind=KIND_STR,
        default=(
            "database/migrations/**;**/*.ci.yml;docker/**;terraform/**;.github/workflows/**"
        ),
    ),
    ConfigField(
        key="GITPR_FIX_REQUIRE_CONFIRMATION",
        label=__("Ask Before Applying"),
        description=__(
            "Shows the diff and asks for confirmation before a patch is written to the working tree."
        ),
        category="fix",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE",
        label=__("Branch for a Batch"),
        description=__(
            "Creates a new branch when the safe patches are applied in a batch, so the current branch stays untouched."
        ),
        category="fix",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_FIX_BRANCH_NAME_TEMPLATE",
        label=__("Branch Name"),
        description=__(
            "Name of the branch created for a batch. Placeholders: branch and datetime."
        ),
        category="fix",
        kind=KIND_TEMPLATE,
        default="fix/gitpr-{datetime}",
    ),
    # ------------------------------------------------------------------- Split
    ConfigField(
        key="GITPR_SPLIT_MAX_GROUPS",
        label=__("Maximum Commits"),
        description=__(
            "Upper limit on how many atomic commits a plan may propose, so a diff with many small changes is not shredded into as many commits."
        ),
        category="split",
        kind=KIND_INT,
        default="5",
    ),
    ConfigField(
        key="GITPR_SPLIT_REQUIRE_CONFIRMATION",
        label=__("Ask Before Committing"),
        description=__(
            "Shows the plan and asks for confirmation before the first commit is created."
        ),
        category="split",
        kind=KIND_BOOL,
        default="true",
    ),
    ConfigField(
        key="GITPR_SPLIT_MAX_HUNKS",
        label=__("Maximum Hunks Analysed"),
        description=__(
            "Upper limit on how many hunks are sent to the grouping call. Anything beyond it stays ungrouped and uncommitted, with a warning."
        ),
        category="split",
        kind=KIND_INT,
        default="50",
    ),
    # --------------------------------------------------------------- SCM/Forge
    # The common settings stay ungrouped and always visible; the fields that
    # only exist for one forge live under its sub-header and follow the
    # selected provider. GITPR_SCM_TOKEN is common on purpose: get_scm_token()
    # reads it for every forge, so hiding it behind the GitHub group would make
    # it invisible to GitLab/Bitbucket/Azure users who have it set.
    ConfigField(
        key="GITPR_SCM_PROVIDER",
        label=__("Forge Provider"),
        description=__(
            "Git hosting service of this repository. Leave it empty to use GitHub."
        ),
        category="scm",
        kind=KIND_ENUM,
        default="",
        choices=("", "github", "gitlab", "bitbucket", "azure_devops"),
    ),
    ConfigField(
        key="GITPR_SCM_TOKEN",
        label=__("CI/CD Token (raw)"),
        description=__(
            "Raw token injected by CI/CD. It takes precedence over the encrypted token for every forge, and is configured with `gitpr --init`. The value is never displayed and never written here."
        ),
        category="scm",
        kind=KIND_SECRET,
        default="",
        read_only=True,
    ),
    ConfigField(
        key="GITPR_SCM_TOKEN_ENCRYPTED",
        label=__("Forge Token"),
        description=__(
            "Access token of the configured forge, stored encrypted. The value is never displayed back."
        ),
        category="scm",
        kind=KIND_SECRET,
        default="",
        validator=VALIDATOR_SCM_TOKEN,
    ),
    ConfigField(
        key="GITPR_SCM_BASE_URL",
        label=__("API Base URL"),
        description=__(
            "API address of a self managed forge. Leave it empty to use the public service."
        ),
        category="scm",
        kind=KIND_STR,
        default="",
    ),
    ConfigField(
        key="GITHUB_TOKEN_ENCRYPTED",
        label=__("GitHub Token"),
        description=__(
            "Legacy GitHub personal access token, used when no forge is configured."
        ),
        category="scm",
        kind=KIND_SECRET,
        default="",
        validator=VALIDATOR_SCM_TOKEN,
        group="github",
        show_if=(("GITPR_SCM_PROVIDER", ("", "github")),),
    ),
    ConfigField(
        key="GITPR_SCM_USERNAME",
        label=__("Username"),
        description=__(
            "Bitbucket account used together with the app password."
        ),
        category="scm",
        kind=KIND_STR,
        default="",
        group="bitbucket",
        show_if=(("GITPR_SCM_PROVIDER", ("bitbucket",)),),
    ),
    ConfigField(
        key="GITPR_SCM_ORGANIZATION",
        label=__("Organization"),
        description=__("Organization of the Azure DevOps project."),
        category="scm",
        kind=KIND_STR,
        default="",
        group="azure_devops",
        show_if=(("GITPR_SCM_PROVIDER", ("azure_devops",)),),
    ),
    ConfigField(
        key="GITPR_SCM_PROJECT",
        label=__("Project"),
        description=__("Project name of the Azure DevOps repository."),
        category="scm",
        kind=KIND_STR,
        default="",
        group="azure_devops",
        show_if=(("GITPR_SCM_PROVIDER", ("azure_devops",)),),
    ),
    # ----------------------------------------------------------- Diff filters
    ConfigField(
        key="GITPR_SKIP_SMART_EXCLUDES",
        label=__("Disable Diff Filters"),
        description=__(
            "Sends every changed file to the AI, including the ones the smart filters would drop."
        ),
        category="diff",
        kind=KIND_BOOL,
        default="",
    ),
    ConfigField(
        key="GITPR_SMART_EXCLUDES_GLOBAL",
        label=__("Global Filters File"),
        description=__(
            "Path of a custom filter list used by every project. Leave it empty to use the downloaded list."
        ),
        category="diff",
        kind=KIND_PATH,
        default="",
    ),
    ConfigField(
        key="GITPR_SMART_EXCLUDES_LOCAL",
        label=__("Project Filters File"),
        description=__(
            "Path of a filter list that only applies to the current project."
        ),
        category="diff",
        kind=KIND_PATH,
        default="",
    ),
    # ------------------------------------------------------------------ Skills
    # A read-only sentinel, and the only row of the section: the skills
    # themselves are files, not .env keys, so they are not ConfigFields and are
    # rendered by the dedicated pane below them. This field exists because it
    # carries information the screen would otherwise never state — the skills
    # are resolved from the directory gitpr was started in, which is exactly the
    # mistake this line prevents — and because a category with no field at all
    # is a shape the schema does not allow. Its value comes from
    # config.get_skill_dir(), resolved in ui/config_app.py.
    ConfigField(
        key="SKILLS_FOLDER",
        label=__("Skills folder"),
        description=__(
            "Where this project's skill files live. It comes from the folder gitpr was started in."
        ),
        category="skills",
        kind=KIND_PATH,
        default="",
        read_only=True,
    ),
    # ---------------------------------------------------------------- Advanced
    # Grouped by theme, in the order the user meets them: what the spinner
    # shows, how the hooks are installed, and finally the downloaded packs that
    # can be refreshed by hand.
    ConfigField(
        key="SPINNER_THINKING_WORDS",
        label=__("Spinner Words"),
        description=__(
            "Words shown next to the loading spinner. Use the button below to download the published list again."
        ),
        category="advanced",
        kind=KIND_WORDS,
        default="",
        advanced=True,
        read_only=True,
        group="spinner",
        action=ACTION_DOWNLOAD_WORDS,
    ),
    ConfigField(
        key="THINKING_WORDS_VERSION",
        label=__("Spinner Words Version"),
        description=__(
            "Version of the downloaded spinner word list. Managed automatically."
        ),
        category="advanced",
        kind=KIND_VERSION,
        default="",
        advanced=True,
        read_only=True,
        group="spinner",
        version_source=VERSION_LANG,
        action=ACTION_DOWNLOAD,
    ),
    ConfigField(
        key="SCRIPTS_LANG",
        label=__("Hooks Language"),
        description=__(
            "Language the git hooks are installed in. Leave it empty to follow the interface language."
        ),
        category="advanced",
        kind=KIND_ENUM,
        default="",
        choices=("", "en_us", "pt_br", "pt_pt", "es_es", "fr_fr"),
        choice_labels=(
            ("en_us", __("English")),
            ("pt_br", __("Portuguese (Brazil)")),
            ("pt_pt", __("Portuguese (Portugal)")),
            ("es_es", __("Spanish (Spain)")),
            ("fr_fr", __("French (France)")),
        ),
        advanced=True,
        group="hooks",
    ),
    ConfigField(
        key="SCRIPTS_INSTALLED_LANG",
        label=__("Installed Hooks Language"),
        description=__(
            "Language of the hook scripts currently on disk. Managed by the hook installer."
        ),
        category="advanced",
        kind=KIND_ENUM,
        default="",
        choices=("", "en_us", "pt_br", "pt_pt", "es_es", "fr_fr"),
        choice_labels=(
            ("en_us", __("English")),
            ("pt_br", __("Portuguese (Brazil)")),
            ("pt_pt", __("Portuguese (Portugal)")),
            ("es_es", __("Spanish (Spain)")),
            ("fr_fr", __("French (France)")),
        ),
        advanced=True,
        read_only=True,
        group="hooks",
    ),
    ConfigField(
        key="SCRIPTS_VERSION",
        label=__("Hooks Version"),
        description=__(
            "Version of the installed git hook scripts. Managed automatically."
        ),
        category="advanced",
        kind=KIND_VERSION,
        default="",
        advanced=True,
        read_only=True,
        group="hooks",
        version_source=VERSION_SCRIPTS,
    ),
    ConfigField(
        key="LANG_VERSION",
        label=__("Translation Pack Version"),
        description=__(
            "Version of the downloaded translation file. Managed automatically."
        ),
        category="advanced",
        kind=KIND_VERSION,
        default="",
        advanced=True,
        read_only=True,
        group="downloads",
        version_source=VERSION_LANG,
        action=ACTION_DOWNLOAD,
    ),
    ConfigField(
        key="SMART_EXCLUDES_VERSION",
        label=__("Filters List Version"),
        description=__(
            "Version of the downloaded filter list. Managed automatically."
        ),
        category="advanced",
        kind=KIND_VERSION,
        default="",
        advanced=True,
        read_only=True,
        group="downloads",
        version_source=VERSION_LANG,
        action=ACTION_DOWNLOAD,
    ),
    ConfigField(
        key="LINTER_PRESETS_VERSION",
        label=__("Linter Presets Version"),
        description=__(
            "Version of the downloaded external linter catalogue. Managed automatically."
        ),
        category="advanced",
        kind=KIND_VERSION,
        default="",
        advanced=True,
        read_only=True,
        group="downloads",
        version_source=VERSION_LANG,
        action=ACTION_DOWNLOAD,
    ),
)

# Keyed lookups used by the TUI and the tests.
FIELDS_BY_KEY = {field.key: field for field in FIELDS}
CATEGORIES_BY_ID = {category.id: category for category in CATEGORIES}
GROUPS_BY_ID = {group.id: group for group in GROUPS}
GROUP_LABELS = {group.id: group.label for group in GROUPS}
KNOWN_KEYS = frozenset(FIELDS_BY_KEY)

# Fields whose value decides whether other fields are shown. The TUI re-renders
# the pane when one of them changes, so this must not drift from the schema.
VISIBILITY_CONTROLLERS = frozenset(
    key for field in FIELDS for key, _allowed in field.show_if
)

# Category ids in menu order, for rendering the sidebar.
CATEGORY_ORDER = tuple(category.id for category in CATEGORIES)


def fields_of(category_id, include_advanced=False):
    """Returns the fields of *category_id*, honouring the advanced toggle."""
    return tuple(
        field
        for field in FIELDS
        if field.category == category_id
        and (include_advanced or not field.advanced)
    )


def category_has_fields(category_id, include_advanced=False):
    """True when the category would render at least one row."""
    return bool(fields_of(category_id, include_advanced))


def field_lookup_terms(field):
    """Lowercase tokens the search box matches *field* against.

    The env var name and the label — the two things a user can actually recall.
    """
    return field.key.lower(), field.label.lower()


def validate_field_value(field, value):
    """Checks *value* against the rules *field* declares, offline.

    Returns an empty string when the value is acceptable, or a ready-to-display
    error message when it is not.

    Every rule here mirrors a silent fallback in the read path — the whole point
    of the screen is to say out loud what the getters currently swallow. Network
    credential checks are NOT done here: they are resolved by name from
    config.validate_ai_key()/validate_github_token() by the TUI.
    """
    value = (value or "").strip()

    if field.kind == KIND_BOOL:
        if value.lower() not in BOOL_TRUE + BOOL_FALSE:
            return __("Use true or false.")

    elif field.kind == KIND_INT:
        # config.py's _positive_float() and the reviewer top-N reader both
        # discard non-positive and unparsable values without telling anyone.
        try:
            parsed = int(value)
        except ValueError:
            return __("Use a whole number greater than zero.")
        if parsed <= 0:
            return __("Use a whole number greater than zero.")

    elif field.kind == KIND_ENUM:
        if value not in field.choices:
            return __("Choose one of: {choices}", choices=", ".join(field.choices))

    elif field.kind == KIND_TEMPLATE:
        try:
            used = {name for _, name, _, _ in Formatter().parse(value) if name}
        except ValueError as exc:
            return __("Invalid template: {error}", error=str(exc))
        unknown = sorted(used - set(TEMPLATE_PLACEHOLDERS))
        if unknown:
            # core.resolve_output_path() calls .format(branch=, datetime=), so an
            # unknown placeholder is a KeyError on the next command run.
            return __("Unknown placeholder: {names}", names=", ".join(unknown))
        missing = sorted(set(TEMPLATE_REQUIRED) - used)
        if missing:
            # Without {datetime} every run resolves to the same filename and
            # silently overwrites the previous report.
            return __(
                "The name must keep {names}.", names=", ".join(f"{{{n}}}" for n in missing)
            )

    return ""
