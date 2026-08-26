"""Read-only upload monitor commands."""

import time

import click

from ....infrastructure.upload_observe import (
    load_sessions,
    render_list,
    render_session,
    select_session,
)


def status(_context, session_id=None, list_only=False):
    if list_only:
        click.echo(render_list(load_sessions()))
        return
    session = select_session(session_id)
    if session is None:
        click.echo("没有可监控的上传会话")
        return
    click.echo(render_session(session))
    if session.get("status") in (
        "finished",
        "success",
        "succeeded",
        "failed",
        "完成",
        "失败",
    ):
        time.sleep(2)
        return
    try:
        while True:
            time.sleep(1)
            current = select_session(session_id)
            if current is not None:
                click.clear()
                click.echo(render_session(current))
    except KeyboardInterrupt:
        return
