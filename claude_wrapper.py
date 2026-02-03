#!/usr/bin/env python3
import argparse
import sys
import subprocess

def main():
    """
    Parses claude-like commands and executes corresponding opencode commands.
    """
    parser = argparse.ArgumentParser(
        description="A wrapper script to translate claude CLI commands to opencode CLI commands.",
        usage="claude [options] [command] [prompt]",
        add_help=False
    )

    # Supported and translated arguments
    parser.add_argument('--agent', help='Agent for the current session.')
    parser.add_argument('-c', '--continue', action='store_true', dest='cont', help='Continue the most recent conversation.')
    parser.add_argument('-d', '--debug', nargs='?', const='DEBUG', default=None, help='Enable debug mode.')
    parser.add_argument('--debug-file', help='Write debug logs to a file.')
    parser.add_argument('--from-pr', help='Resume a session from a PR number/URL.')
    parser.add_argument('-h', '--help', action='store_true', help='Display help for command.')
    parser.add_argument('-m', '--model', help='Model for the current session.')
    parser.add_argument('-p', '--print', action='store_true', help='Print response and exit.')
    parser.add_argument('-r', '--resume', nargs='?', const='__CONTINUE__', default=None, help='Resume a conversation by session ID.')
    parser.add_argument('--session-id', help='Use a specific session ID for the conversation.')
    parser.add_argument('--system-prompt', help='System prompt to use for the session.')
    parser.add_argument('-v', '--version', action='store_true', help='Output the version number.')

    # Arguments that are unsupported and should raise an error
    unsupported_args = {
        'add_dir': ('+', "Unsupported"), 'agents': ('?', "Unsupported"), 'allow_dangerously_skip_permissions': ('store_true', "Unsupported"),
        'allowedTools': ('+', "Unsupported"), 'allowed_tools': ('+', "Unsupported"), 'append_system_prompt': ('?', "Unsupported"),
        'betas': ('+', "Unsupported"), 'chrome': ('store_true', "Unsupported"), 'dangerously_skip_permissions': ('store_true', "Unsupported"),
        'disable_slash_commands': ('store_true', "Unsupported"), 'disallowedTools': ('+', "Unsupported"), 'disallowed_tools': ('+', "Unsupported"),
        'fallback_model': ('?', "Unsupported"), 'file': ('+', "Unsupported"), 'fork_session': ('store_true', "Unsupported"),
        'ide': ('store_true', "Unsupported"), 'include_partial_messages': ('store_true', "Unsupported"), 'input_format': ('?', "Unsupported"),
        'json_schema': ('?', "Unsupported"), 'max_budget_usd': ('?', "Unsupported"), 'mcp_config': ('+', "Unsupported"),
        'mcp_debug': ('store_true', "Unsupported"), 'no_chrome': ('store_true', "Unsupported"), 'no_session_persistence': ('store_true', "Unsupported"),
        'output_format': ('?', "Unsupported"), 'permission_mode': ('?', "Unsupported"), 'plugin_dir': ('+', "Unsupported"),
        'replay_user_messages': ('store_true', "Unsupported"), 'setting_sources': ('?', "Unsupported"), 'settings': ('?', "Unsupported"),
        'strict_mcp_config': ('store_true', "Unsupported"), 'tools': ('+', "Unsupported"), 'verbose': ('store_true', "Unsupported")
    }
    for arg, (action, help_text) in unsupported_args.items():
        if action == 'store_true':
            parser.add_argument(f'--{arg.replace("_", "-")}', action='store_true', help=help_text)
        else:
            parser.add_argument(f'--{arg.replace("_", "-")}', nargs=action, help=help_text)
    
    args, remaining_argv = parser.parse_known_args()

    # Check for usage of unsupported arguments
    for arg_name in unsupported_args:
        if getattr(args, arg_name, None):
            print(f"Error: Argument --{arg_name.replace('_', '-')} is not supported.", file=sys.stderr)
            sys.exit(1)

    # Handle help action
    if args.help:
        parser.print_help()
        sys.exit(0)

    # Process remaining arguments for command and prompt
    command = None
    prompt_list = []
    supported_commands = ['doctor', 'install', 'mcp', 'plugin', 'setup-token', 'update']
    if remaining_argv and remaining_argv[0] in supported_commands:
        command = remaining_argv[0]
        prompt_list = remaining_argv[1:]
    else:
        prompt_list = remaining_argv

    opencode_args = ["opencode"]
    debug_file_handle = None
    stderr_redirect = None

    # Translate command
    if command:
        if command in ['install', 'update']:
            opencode_args.append('upgrade')
            opencode_args.extend(prompt_list)
        elif command == 'mcp':
            opencode_args.append('mcp')
            opencode_args.extend(prompt_list)
        elif command == 'setup-token':
            opencode_args.append('auth')
        elif command in ['doctor', 'plugin']:
            print(f"Error: Command '{command}' is not supported.", file=sys.stderr)
            sys.exit(1)
    
    # Translate options
    if args.version:
        opencode_args.append('--version')
    # Session handling logic. Priority:
    # 1. Specific session ID (--resume <id> or --session-id <id>)
    # 2. Continue last session (--continue or --resume with no ID)
    specific_session_id = None
    if args.resume and args.resume != '__CONTINUE__':
        specific_session_id = args.resume
    elif args.session_id:
        specific_session_id = args.session_id

    if specific_session_id:
        # Avoid adding --continue if a specific session is provided
        if '--continue' in opencode_args:
            opencode_args.remove('--continue')
        opencode_args.extend(['--session', specific_session_id])
    elif args.cont or args.resume == '__CONTINUE__':
        if '--continue' not in opencode_args:
            opencode_args.append('--continue')

    if args.system_prompt:
        opencode_args.extend(['--prompt', args.system_prompt])
    
    if args.from_pr:
        opencode_args.extend(['pr', args.from_pr])

    if args.debug:
        opencode_args.extend(['--log-level', 'DEBUG'])

    if args.debug_file:
        opencode_args.append('--print-logs')
        try:
            debug_file_handle = open(args.debug_file, 'a')
            stderr_redirect = debug_file_handle
        except IOError as e:
            print(f"Error opening debug file: {e}", file=sys.stderr)
            sys.exit(1)

    # If there is a prompt and no other command has been added
    if prompt_list and command is None:
        if len(opencode_args) == 1:
            opencode_args.append('run')
        opencode_args.extend(prompt_list)
    
    if len(opencode_args) == 1:
        # No arguments translated, run opencode interactively
        pass

    try:
        # print(f"Executing: {' '.join(opencode_args)}", file=sys.stderr)
        subprocess.run(opencode_args, stderr=stderr_redirect, check=False)
    except FileNotFoundError:
        print("Error: 'opencode' command not found. Make sure it's installed and in your PATH.", file=sys.stderr)
        sys.exit(1)
    finally:
        if debug_file_handle:
            debug_file_handle.close()

if __name__ == "__main__":
    main()
