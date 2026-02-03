# claude_wrapper

`claude_wrapper.py` is a compatibility wrapper that accepts a subset of
Claude CLI flags and commands and translates them into equivalent
`opencode` CLI invocations. It is intended to let existing `claude`-style
scripts keep working while actually calling `opencode` under the hood.

## What it does

- Parses common `claude` flags (session control, model, debug) and maps them to
  `opencode` flags.
- Translates a few top-level commands to their `opencode` equivalents.
- Rejects unsupported flags and commands with a clear error message.
- Runs `opencode` via `subprocess.run` and exits with an error if it is missing.

## Command translation

| Claude command | Opencode command |
| --- | --- |
| `install` | `upgrade` |
| `update` | `upgrade` |
| `mcp` | `mcp` |
| `setup-token` | `auth` |
| `doctor` | unsupported |
| `plugin` | unsupported |

If no command is supplied and a prompt is provided, the wrapper uses
`opencode run <prompt>`.

## Flag translation

- `--resume <id>` or `--session-id <id>` -> `--session <id>`
- `--continue` or `--resume` (no id) -> `--continue`
- `--system-prompt <text>` -> `--prompt <text>`
- `--from-pr <pr>` -> `pr <pr>`
- `--debug` or `-d` -> `--log-level DEBUG`
- `--debug-file <path>` -> `--print-logs` and redirects stderr to the file
- `--version` -> `--version`

Any explicitly unsupported flag results in an error and exit code 1.

## Usage

Run it as a drop-in replacement for `claude`:

```bash
./claude_wrapper.py "Summarize this repo"
```

Continue the most recent session:

```bash
./claude_wrapper.py --continue "Add a README"
```

Resume a specific session:

```bash
./claude_wrapper.py --resume 12345 "Fix tests"
```

Use a command:

```bash
./claude_wrapper.py install
```

## Requirements

- Python 3
- `opencode` installed and available on your PATH

## Notes

- Unsupported Claude flags are deliberately rejected to avoid silent
  behavior changes.
- If `opencode` is not found, the wrapper prints an error and exits.
