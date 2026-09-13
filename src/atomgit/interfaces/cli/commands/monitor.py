"""Read-only upload monitor commands."""

import time

import click

from ....infrastructure.upload_observe import (
    load_sessions,
    render_list,
    render_session,
    select_session,
)

_TERMINAL_STATUSES = frozenset(
    ("finished", "success", "succeeded", "failed", "完成", "失败")
)


def status(_context, session_id=None, list_only=False):
    if list_only:
        click.echo(render_list(load_sessions()))
        return
    session = select_session(session_id)
    if session is None:
        click.echo("没有可监控的上传会话")
        return
    try:
        click.echo(render_session(session))
        if session.get("status") in _TERMINAL_STATUSES:
            time.sleep(2)
            return
        selected_session_id = str(session.get("session_id", ""))
        while True:
            time.sleep(1)
            current = select_session(selected_session_id)
            if current is not None:
                click.clear()
                click.echo(render_session(current))
                if current.get("status") in _TERMINAL_STATUSES:
                    time.sleep(2)
                    return
    except KeyboardInterrupt:
        return
