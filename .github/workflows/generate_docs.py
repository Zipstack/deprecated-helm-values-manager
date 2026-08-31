"""Script to generate markdown documentation for the Helm Values Manager CLI commands.

This script uses the Typer library's introspection capabilities to automatically
generate comprehensive documentation for all CLI commands, including their
arguments, options, and help text.
"""

import inspect
from typing import List, Optional, Tuple, Union

import typer

from helm_values_manager.cli import app


def get_command_parameters(
    command: typer.models.CommandInfo,
) -> List[Tuple[str, Union[typer.models.OptionInfo, typer.models.ArgumentInfo]]]:
    """Extract parameters from a command's signature.

    Args:
        command: The Typer command to extract parameters from

    Returns:
        List of tuples containing parameter names and their Typer info objects
    """
    params = []
    sig = inspect.signature(command.callback)
    for param_name, param in sig.parameters.items():
        if param_name != "ctx":  # Skip context parameter
            if isinstance(param.default, (typer.models.OptionInfo, typer.models.ArgumentInfo)):
                params.append((param_name, param.default))
    return params


def format_parameter_options(param_name: str, param: typer.models.OptionInfo) -> List[str]:
    """Format the option names (long and short forms) for a parameter.

    Args:
        param_name: The parameter's variable name
        param: The Typer option info object

    Returns:
        List of formatted option strings
    """
    options = []

    # Get the option names from the Typer.Option constructor
    if isinstance(param, typer.models.OptionInfo):
        # Get the first two arguments which are the long and short forms
        args = [arg for arg in param.param_decls if isinstance(arg, str)]
        if args:
            # Sort to ensure long form comes first
            options.extend(sorted(args, key=lambda x: not x.startswith("--")))

    return options


def format_default_value(param: Union[typer.models.OptionInfo, typer.models.ArgumentInfo]) -> Optional[str]:
    """Format the default value for a parameter.

    Args:
        param: The Typer parameter info object

    Returns:
        Formatted default value string or None if no default
    """
    if not hasattr(param, "default") or param.default is ...:
        return None

    if isinstance(param.default, str) and not param.default:
        return "(default: empty string)"
    return f"(default: {param.default})"


def generate_command_list(commands: List[typer.models.CommandInfo]) -> List[str]:
    """Generate the list of available commands.

    Args:
        commands: List of Typer command info objects

    Returns:
        List of formatted command strings
    """
    docs = []
    for command in commands:
        name = command.name or command.callback.__name__
        help_text = command.help or command.callback.__doc__ or "No description available."
        help_text = help_text.split("\n")[0]  # Get first line only
        docs.append(f"- [`{name}`](#{name}) - {help_text}\n")
    return docs


def generate_command_details(command: typer.models.CommandInfo) -> List[str]:
    """Generate detailed documentation for a single command.

    Args:
        command: The Typer command info object

    Returns:
        List of formatted documentation strings
    """
    docs = []
    name = command.name or command.callback.__name__
    help_text = command.help or command.callback.__doc__ or "No description available."

    docs.extend(
        [
            f"\n### `{name}`\n\n{help_text}\n",
            "\n**Usage:**\n```bash\nhelm values-manager",
        ]
    )

    if name != "main":
        docs.append(f" {name}")

    # Get command parameters
    params = get_command_parameters(command)
    if params:
        docs.append(" [options]")
    docs.append("\n```\n")

    # Document parameters
    args = []
    opts = []
    for param_name, param in params:
        if isinstance(param, typer.models.OptionInfo):
            if not hasattr(param, "hidden") or not param.hidden:  # Skip hidden options
                opts.append((param_name, param))
        elif isinstance(param, typer.models.ArgumentInfo):
            args.append((param_name, param))

    if args:
        docs.append("\n**Arguments:**\n")
        for param_name, param in args:
            docs.append(f"- `{param_name}`: {param.help}")
            default_value = format_default_value(param)
            if default_value:
                docs.append(f" {default_value}")
            docs.append("\n")

    if opts:
        docs.append("\n**Options:**\n")
        for param_name, param in opts:
            option_names = format_parameter_options(param_name, param)
            if not option_names:  # Skip if no option names found
                continue
            docs.append(f"- `{', '.join(option_names)}`: {param.help}")
            default_value = format_default_value(param)
            if default_value:
                docs.append(f" {default_value}")
            docs.append("\n")

    return docs


def generate_markdown_docs() -> str:
    """Generate complete markdown documentation for all commands.

    Returns:
        Complete markdown documentation as a string
    """
    header = "# Command Reference"
    description = (
        "This document provides detailed information about all available commands in the Helm Values Manager plugin."
    )
    docs = [f"{header}\n\n{description}\n\n## Available Commands\n"]

    # Add command list
    docs.extend(generate_command_list(app.registered_commands))

    # Add command details
    docs.append("\n## Command Details\n")
    for command in app.registered_commands:
        docs.extend(generate_command_details(command))

    # Add help section
    docs.append("""
## Using Help

Each command supports the `--help` flag for detailed information:

```bash
helm values-manager --help
helm values-manager <command> --help
```
""")

    return "".join(docs)


if __name__ == "__main__":
    docs = generate_markdown_docs()
    with open("docs/Commands/README.md", "w") as f:
        f.write(docs)
