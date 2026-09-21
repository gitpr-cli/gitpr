"""Asking the model which units belong together, and disbelieving the answer.

The model's job is narrow — partition a list of ids — and almost everything
this module does is about not trusting it. Ids it invents are discarded, ids it
repeats are kept once, ids it never mentions still reach the plan as ungrouped
units, and a group it leaves empty disappears. The rule underneath all of them:
a plan may lose a grouping decision, but it may never lose a *change*. Every
unit that went in comes out either in a group or in the ungrouped list.

The prompt is bounded twice, and both bounds degrade the same way. Each unit's
body is truncated to :data:`MAX_BODY_LINES` lines, so one enormous hunk cannot
crowd out twenty small ones; and the list itself is capped by unit count and by
total characters, largest-first. Largest-first is the point: trimming in file
order would systematically starve the last files in the diff, and file order is
not a statement about importance.

There is no skill template behind this prompt, deliberately. See
``docs/split-command.md`` §5: ``get_skill_context()`` answers an unregistered
action type with the *review* skill, so a "split" lookup would hand the grouping
prompt a code-review persona, and registering the type properly means a new
entry in the skill registry, the configuration screen's order-asserted label
list, the MCP registry and a template per language.
"""
import click

from src.ai_providers import call_ai_model
from src.cache import get_cached_response, save_cached_response
from src.config import get_ai_provider, get_api_key, get_api_model
from src.i18n import __
from src.split.split_plan import HunkGroup, SplitError

#: Cache folder of the grouping call — one folder per command, as everywhere
#: else in the project (~/.gitpr/cache/prompts/split/<md5>.json).
GROUP_ACTION = "split"

#: Bump when the prompt below changes. The MD5 cache already keys on the prompt
#: text, so this does not invalidate anything — it is what tells a later reader
#: which prompt produced a plan.
PROMPT_VERSION = "1"

#: How much of each hunk the model is shown. Enough to recognise what the code
#: does, not enough for one hunk to fill the prompt on its own.
MAX_BODY_LINES = 40

#: A ceiling on the whole prompt. The unit cap bounds the *number* of units and
#: this bounds their size, which the count cannot: fifty hunks of four thousand
#: lines each pass the count and would still be a prompt nobody can answer.
MAX_PROMPT_CHARS = 120_000

#: The envelope the prompt asks for, kept as one literal so the shape the model
#: is shown and the shape the parser expects can never drift apart.
GROUPING_JSON = (
    '{"groups": [{"unit_ids": ["0001-ab12cd34", "0002-ef56ab78"], '
    '"intent_label": "fix: short label", "justification": "one sentence"}], '
    '"ungrouped": ["0003-99887766"]}'
)

#: The grouping persona. Fixed, and not a skill file: see the module docstring.
SYSTEM_INSTRUCTION = (
    "You are a Senior Software Engineer who splits a messy working tree into atomic commits. "
    "You are given the hunks of one uncommitted diff, each with a stable id. Group the ids by "
    "logical intent: every id in a group must belong to the same single concern, so that the "
    "group could be committed alone and the history would still make sense. A file's hunks "
    "routinely belong to different groups — that is the point of the task. Never invent an id. "
    "An id you cannot place with confidence goes in 'ungrouped' rather than into a group it "
    "does not belong to. Answer with the JSON object only."
)


def group_units(units, max_groups=5, max_units=50, provider=None, quiet=False):
    """Group *units* by intent. Returns ``(groups, ungrouped, warnings)``.

    Read-only: the only thing touched is the prompt cache. *units* must hold
    hunks only — opaque sections are forced into their own groups by the caller
    without ever reaching the model, and their ids are deliberately absent from
    this prompt.

    Raises ``SplitError`` when there is no provider or key, or when the model
    answers with nothing at all. Every other kind of bad answer — prose instead
    of the envelope, ids that do not exist, a group with no units — is absorbed
    and reported through the warnings, because a malformed answer still leaves a
    working tree full of changes the user can act on, and refusing to proceed
    would leave them with nothing.
    """
    if not units:
        return [], [], []

    provider = provider or get_ai_provider()
    api_key = get_api_key(provider)
    if not api_key:
        raise SplitError(
            __(
                "❌ No API key configured for {provider}. Generate one with --install.",
                provider=provider,
            )
        )
    api_model = get_api_model(provider, task_complexity="advanced")

    kept, trimmed = _select_for_prompt(units, max_units)
    warnings = []
    if trimmed:
        warnings.append(
            __(
                "⚠️ {count} unit(s) exceeded the analysis budget and were left ungrouped: {ids}",
                count=len(trimmed),
                ids=", ".join(unit.id for unit in trimmed),
            )
        )

    payload = _grouping(kept, max_groups, provider, api_key, api_model, quiet=quiet)
    groups, ungrouped, validation_warnings = _validate(payload, kept, max_groups)
    warnings.extend(validation_warnings)

    # The trimmed units were never offered to the model, so they are ungrouped
    # by the same rule as a unit the model never mentioned.
    return groups, ungrouped + list(trimmed), warnings


def grouping_prompt(units, max_groups):
    """The one prompt: the units to group, and the envelope to answer in."""
    rendered = "\n\n".join(_render_unit(unit) for unit in units)
    return (
        __(
            "Below are the hunks of one uncommitted diff, each with a stable id. Group the ids "
            "by logical intent — hunks of the same concern in one group, unrelated hunks apart. "
            "Propose at most {max_groups} groups. Generate ONLY a JSON object in the format "
            "{json_format}:\n",
            max_groups=max_groups,
            json_format=GROUPING_JSON,
        )
        + "\n"
        + __("=== HUNKS ===")
        + f"\n{rendered}"
    )


def _render_unit(unit):
    """One unit as the model sees it: identity, location, and a bounded body.

    The body is truncated from the middle out would be prettier and is worse
    here — the opening lines of a hunk are its context and the lines that follow
    are the change, so the head is what says what the code is. The tail is what
    gets cut, and the cut is announced so the model knows the hunk continues.
    """
    body = unit.content.split("\n")
    if len(body) > MAX_BODY_LINES:
        body = body[:MAX_BODY_LINES] + [
            __("... ({count} more lines)", count=len(body) - MAX_BODY_LINES)
        ]

    return (
        f"{__('id:')} {unit.id}\n"
        f"{__('file:')} {unit.file_path}\n"
        f"{__('range:')} {unit.hunk_header}\n"
        + "\n".join(body)
    )


def _select_for_prompt(units, max_units):
    """``(kept, dropped)`` — the units that fit the budget, and those that do not.

    Largest-first, so a long diff does not systematically starve its last files:
    trimming in file order would cut the tail every time, and the tail of a diff
    is not its least important part. The returned halves keep their original
    traversal order, because that is the order the plan reports them in.

    The cost is measured on the *rendered* unit, after truncation — measuring
    the raw content would reject a four-thousand-line hunk that costs forty
    lines to send.

    One unit is always kept, even if it alone is over budget. A unit too large
    to send is still a unit the model can be shown the head of, and sending
    nothing at all would turn the whole diff ungrouped over a single file.
    """
    by_size = sorted(units, key=_prompt_cost, reverse=True)

    kept = []
    budget = MAX_PROMPT_CHARS
    for unit in by_size:
        if len(kept) >= max_units:
            break
        cost = _prompt_cost(unit)
        if kept and cost > budget:
            break
        budget -= cost
        kept.append(unit)

    chosen = {unit.id for unit in kept}
    ordered = [unit for unit in units if unit.id in chosen]
    dropped = [unit for unit in units if unit.id not in chosen]
    return ordered, dropped


def _prompt_cost(unit):
    """How many characters *unit* adds to the prompt, truncation included."""
    return len(_render_unit(unit))


def _grouping(units, max_groups, provider, api_key, api_model, quiet=False):
    """The grouping payload — from cache, or the AI.

    Cached like every other AI call in the project, and here the cache does more
    than save a call: it is what makes a re-run of ``--dry-run`` on an unchanged
    tree print the same plan, group ids included.
    """
    prompt = grouping_prompt(units, max_groups)

    cached = get_cached_response(GROUP_ACTION, prompt)
    if isinstance(cached, dict) and cached.get("groups") is not None:
        _say(quiet, __("⚡ Grouping retrieved from local cache."), fg="green", dim=True)
        return cached

    response = call_ai_model(
        provider, api_key, api_model, prompt, SYSTEM_INSTRUCTION, action=GROUP_ACTION
    )

    if not response:
        raise SplitError(
            __(
                "❌ The AI did not return a grouping. Try again or check the provider."
            )
        )

    # A fresh dict, so the telemetry the transport attaches never reaches the
    # cache. Prose instead of the envelope is stored as an empty grouping rather
    # than raising: it is an ordinary answer, just an unhelpful one.
    payload = {
        "groups": response.get("groups") if isinstance(response, dict) else None,
        "ungrouped": response.get("ungrouped") if isinstance(response, dict) else None,
    }
    if not isinstance(payload["groups"], list):
        payload["groups"] = []
    if not isinstance(payload["ungrouped"], list):
        payload["ungrouped"] = []
    save_cached_response(GROUP_ACTION, GROUP_ACTION, prompt, payload)
    return payload


def _validate(payload, units, max_groups):
    """Turn the model's answer into groups, against the units actually sent.

    Returns ``(groups, ungrouped, warnings)``. Every failure mode here has the
    same shape: the decision is thrown away, the unit is not.
    """
    known = {unit.id: unit for unit in units}
    if not isinstance(payload, dict):
        return [], list(units), [
            __("⚠️ The AI's grouping could not be read; every unit stays ungrouped.")
        ]

    warnings = []
    claimed = set()
    placed = set()
    surplus = set()
    groups = []

    raw_groups = payload.get("groups")
    raw_groups = raw_groups if isinstance(raw_groups, list) else []

    for raw in raw_groups:
        if not isinstance(raw, dict):
            continue
        ids = raw.get("unit_ids")
        ids = ids if isinstance(ids, list) else []

        members = []
        unknown = []
        for unit_id in ids:
            unit_id = str(unit_id).strip()
            if unit_id not in known:
                unknown.append(unit_id)
            elif unit_id in claimed:
                # Kept by whichever group named it first: a unit cannot be in
                # two commits, and dropping it from the later group is the only
                # choice that does not silently relocate it.
                continue
            else:
                claimed.add(unit_id)
                members.append(known[unit_id])

        if unknown:
            warnings.append(
                __(
                    "⚠️ The AI named {count} unit(s) that do not exist; discarded: {ids}",
                    count=len(unknown),
                    ids=", ".join(unknown),
                )
            )
        if not members:
            continue
        if len(groups) >= max_groups:
            # The cap is stated in the prompt; a model that ignores it is not
            # overruled here by merging unrelated concerns into one commit. The
            # surplus concerns stay uncommitted and are named, which is true.
            # They are deliberately not added to `placed`: a unit that reached
            # no group is an ungrouped unit, and `placed` is what decides that.
            surplus.update(unit.id for unit in members)
            warnings.append(
                __(
                    "⚠️ The AI proposed more than {max_groups} groups; the surplus units stay ungrouped: {ids}",
                    max_groups=max_groups,
                    ids=", ".join(unit.id for unit in members),
                )
            )
            continue

        placed.update(unit.id for unit in members)
        groups.append(
            HunkGroup(
                group_id=f"G{len(groups) + 1}",
                intent_label=str(raw.get("intent_label") or "").strip(),
                justification=str(raw.get("justification") or "").strip(),
                units=members,
            )
        )

    ungrouped = [unit for unit in units if unit.id not in placed]
    # Surplus units were already named in their own warning; saying it twice
    # would read as two separate problems.
    unmentioned = [
        unit
        for unit in ungrouped
        if unit.id not in surplus and not _named_ungrouped(payload, unit.id)
    ]
    if unmentioned:
        warnings.append(
            __(
                "⚠️ The AI did not place {count} unit(s); left ungrouped: {ids}",
                count=len(unmentioned),
                ids=", ".join(unit.id for unit in unmentioned),
            )
        )
    return groups, ungrouped, warnings


def _named_ungrouped(payload, unit_id):
    """Whether the model itself put *unit_id* in its ungrouped list."""
    declared = payload.get("ungrouped")
    if not isinstance(declared, list):
        return False
    return unit_id in {str(item).strip() for item in declared}


def _say(quiet, text, **kwargs):
    """Prints *text* unless the caller asked for silence (MCP, --quiet flows)."""
    if not quiet:
        click.secho(text, **kwargs)
