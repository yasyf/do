import os
from functools import wraps
from typing import TYPE_CHECKING

import click

from gpt_do.getch import get_confirm

if TYPE_CHECKING:
    from gpt_do.doers.doer import Doer

_confirm = get_confirm()


def confirm(prompt):
    click.echo(f"{prompt} [Y/n]: ", nl=False)
    if resp := _confirm():
        return resp.lower() == "y"
    return True


def make_standard_args(default_model="gpt3"):
    def _standard_args(fn):
        @click.option("--debug/--no-debug", is_flag=True)
        @click.option(
            "--yes/--no", "-y/-n", is_flag=True, help="Do not ask for confirmation"
        )
        @click.option(
            "--model",
            default=default_model,
            type=click.Choice(
                ["gpt3", "codex", "chatgpt"],
                case_sensitive=False,
            ),
        )
        @wraps(fn)
        def wrapped(*args, **kwargs):
            for param in ("debug", "yes", "model"):
                os.environ[f"GPT_DO_{param.upper()}"] = str(
                    click.get_current_context().params[param]
                )
            return fn(*args, **kwargs)

        return wrapped

    return _standard_args


standard_args = make_standard_args()


def get_doer(model):
    if model == "chatgpt":
        from gpt_do.doers.rev_chatgpt_doer import RevChatGPTDoer

        return RevChatGPTDoer
    elif model == "gpt3":
        from gpt_do.doers.gpt3_doer import GPT3Doer

        GPT3Doer.model = "text-davinci-003"
        return GPT3Doer
    elif model == "codex":
        from gpt_do.doers.gpt3_doer import GPT3Doer

        GPT3Doer.model = "code-davinci-002"
        return GPT3Doer
    else:
        raise ValueError(f"Unknown model {model}")


def run_doer(doer: "Doer", request: list[str], yes: bool):
    response = doer.query(" ".join(request))
    click.echo(click.style(response["explanation"], bold=True))
    if not response["commands"]:
        return
    click.echo(click.style("\n".join(response["commands"]), fg="green"))
    if yes or confirm("Execute this command?"):
        click.echo("")
        doer.execute(response)
