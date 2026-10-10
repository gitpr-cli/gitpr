# gitpr/vue-quality

A quality gate for Vue 3 codebases.

## What it changes

| Surface | Effect |
|---|---|
| Review | Adds the component checklist to the review prompt: props and emits, reactivity, cleanup, loading and error states, accessibility, size, tests |
| PR description | Asks for before/after evidence on anything user-facing |
| Commit | Asks for a scope naming the component or the concern |
| Linter | 6 rules: debug leftovers, `v-html`, array index as `:key`, `v-for` without a key, `addEventListener` without a visible cleanup, secrets referenced from client code |
| Risk | 6 critical paths (`stores`, `router`, `plugins`, `composables`, build config), Vue test patterns |
| Protected paths | `src/router/**`, `src/stores/**` |

## Activate

```bash
gitpr policy use gitpr/vue-quality
```

## On `v-for` and `:key`

`vue-v-for-without-key` is a line rule in a world where the real answer needs a
template parser: a `:key` on the next line reads as missing, and a `:key` before
the `v-for` reads as missing too. Both are false positives, which is why the rule
is a warning and its message asks rather than accuses. ESLint's
`vue/require-v-for-key` remains the right tool for that one; this rule exists for
the repositories that do not run ESLint.
