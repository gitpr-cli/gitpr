# gitpr/node-quality

A quality gate for Node.js services.

## What it changes

| Surface | Effect |
|---|---|
| Review | Adds the service checklist to the review prompt: async errors, input validation, unhandled states, dependency hygiene, configuration and secrets, tests |
| PR description | Asks for the failure mode the change guards against and how it was reproduced |
| Commit | Asks for a scope naming the module or the package, and which major a dependency bump crosses |
| Linter | 7 rules: debug leftovers, `eval`/`Function`, a shell command built from a variable, unguarded `JSON.parse` on input, disabled TLS verification, `process.env` logged, npm metadata in `package.json` |
| Risk | 8 critical paths (config, middleware, auth, db, manifests, Dockerfile, Terraform), `infrastructure` weight 25, `no_test_change` weight 20, JS/TS test patterns |
| Protected paths | `src/config/**`, `**/package.json`, `Dockerfile` |

## Activate

```bash
gitpr policy use gitpr/node-quality
```

## On floating promises

The most expensive Node bug — an async function whose rejection nobody handles —
cannot be seen in a line of text. It is not a linter rule here; it is item 1 of
the review context, where the model can see the surrounding function and say
which await is missing.
