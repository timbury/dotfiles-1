#!/usr/bin/env python3

import asyncio
from os import getenv


async def intercept_term_theme():
    # source the current base16 theme as if it weren't running in tmux; this
    # will be fed to other iterm windows
    return (
        await (
            await asyncio.create_subprocess_shell(
                "source ~/.base16_theme",
                stdout=asyncio.subprocess.PIPE,
                env={"TMUX": ""},
            )
        ).communicate()
    )[0]


async def get_iterm_sessions():
    import iterm2

    connection = await iterm2.Connection.async_create()
    app = await iterm2.async_get_app(connection)
    current_tab = app.current_terminal_window.current_tab

    sessions = []
    for window in app.terminal_windows:
        for tab in [t for t in window.tabs if t != current_tab]:
            for session in tab.sessions:
                sessions.append(session)

    return sessions


async def update_iterm_sessions():
    code, sessions = await asyncio.gather(intercept_term_theme(), get_iterm_sessions())
    await asyncio.gather(*[s.async_inject(code) for s in sessions])


def base16_to_kitty():
    from re import compile

    with open(f'{getenv("HOME")}/.base16_theme') as theme_file:
        lines = theme_file.readlines()
    col_matcher = compile(r'^(color(?:\d\d|_\w+))=["$]?([^\s"]+)"?')
    matches = [col_matcher.match(l) for l in lines]
    cols = [m.groups() for m in matches if m != None]

    colors = {}
    for col in cols:
        val = col[1]
        if col[1] in colors:
            val = colors[col[1]]
        colors[col[0]] = val

    for k in colors:
        colors[k] = f'#{colors[k].replace("/", "")}'

    kitty_colors = {
        "cursor": colors["color07"],
        "cursor_text": colors["color00"],
        "cursor_text_color": colors["color00"],
        "selection_background": colors["color19"],
        "selection_foreground": colors["color07"],
        "foreground": colors["color_foreground"],
        "background": colors["color_background"],
    }

    for i in range(22):
        kitty_colors[f"color{i}"] = colors[f"color{i:02}"]

    return kitty_colors


async def update_kitty_sessions():
    colors = base16_to_kitty()

    color_strings = []
    for c in colors:
        color_strings.append(f"{c}={colors[c]}")

    color_string = " ".join(color_strings)

    await (
        await asyncio.create_subprocess_shell(
            f"kitty @ --to=unix:/tmp/kitty.sock set-colors -c -a {color_string}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    ).communicate()


async def update_neovim_theme():
    proc = await asyncio.create_subprocess_shell(
        "nvr --serverlist", stdout=asyncio.subprocess.PIPE
    )
    stdout = (await proc.communicate())[0].decode("utf-8")
    sockets = [s for s in stdout.split("\n") if len(s) > 0]

    await asyncio.gather(
        *[
            asyncio.create_subprocess_shell(
                '''nvr --servername %s -c ":UpdateColors"''' % socket
            )
            for socket in sockets
        ]
    )


async def list_processes():
    proc_lister = await asyncio.create_subprocess_exec(
        "ps", "-e", stdout=asyncio.subprocess.PIPE
    )
    lines = (await proc_lister.communicate())[0].decode().splitlines()
    return set([l.split()[3] for l in lines])


async def main():
    tasks = [update_neovim_theme()]
    processes = await list_processes()

    kitty_running = any("kitty.app" in p for p in processes)
    iterm_running = any("iTerm2" in p for p in processes)

    if iterm_running:
        tasks.append(update_iterm_sessions())
    if kitty_running:
        tasks.append(update_kitty_sessions())

    await asyncio.gather(*tasks)


asyncio.get_event_loop().run_until_complete(main())
