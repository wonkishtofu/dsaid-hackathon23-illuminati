import os
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

import numpy as np
from matplotlib import pyplot as plt
from nicegui import Client, app, ui
from nicegui.events import MouseEventArguments

messages: List[Tuple[str, str, str, str]] = []


@ui.refreshable
async def chat_messages(own_id: str) -> None:
    for user_id, avatar, text, stamp in messages:
        ui.chat_message(text=text, stamp=stamp, avatar=avatar, sent=own_id == user_id)
    await ui.run_javascript('window.scrollTo(0, document.body.scrollHeight)', respond=False)


@ui.page('/')
async def main(client: Client):
    def send() -> None:
        stamp = datetime.utcnow().strftime('%X')
        messages.append((user_id, avatar, text.value, stamp))
        text.value = ''
        chat_messages.refresh()

    def on_tab_change(event):
        print(event.value)
        # remove the text and avatar when move to different tab
        # have to do this cos they are in footer
        avatar_ui.set_visibility(event.value == 'CHATBOT')
        text.set_visibility(event.value == 'CHATBOT')

    # define the tabs
    with ui.tabs().classes('w-full') as tabs:
        chatbot = ui.tab('CHATBOT')
        sparkline = ui.tab('SPARKLINE')
        realtime = ui.tab('REALTIME')
        
    # set tabs in a tab panel
    with ui.tab_panels(tabs, 
                       value=chatbot, 
                       on_change=on_tab_change).classes('w-full'):

        # what appears in chatbot tab
        with ui.tab_panel(chatbot):
            user_id = str(uuid4())
            avatar = f'https://robohash.org/{user_id}?bgset=bg2'

            with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
                with ui.row().classes('w-full no-wrap items-center'):
                    avatar_ui = ui.avatar().on('click', lambda: ui.open(main))
                    with avatar_ui:
                        ui.image(avatar)
                    text = ui.input(placeholder='message').on('keydown.enter', send) \
                        .props('rounded outlined input-class=mx-3').classes('flex-grow')

            await client.connected()  # chat_messages(...) uses run_javascript which is only possible after connecting
            with ui.column().classes('w-full max-w-2xl mx-auto items-stretch'):
                await chat_messages(user_id)
            
        # what appears in sparkline tab
        with ui.tab_panel(sparkline):
            with ui.column().classes('w-full items-center'):
                # create plot using matplotlib.pyplot
                plt.figure(figsize=(8, 6), dpi=80)
                x = np.linspace(0.0, 5.0)
                y = np.cos(2 * np.pi * x) * np.exp(-x)
                plt.plot(x, y, '-')
                os.makedirs('./assets/', exist_ok=True)
                plt.savefig('./assets/sparkline_table.png')
                app.add_static_files('/assets/', './assets/')
                
                # what happens when mousedown/mouseup, basically adds a circle now
                def mouse_handler(e: MouseEventArguments):
                    color = 'SkyBlue' if e.type == 'mousedown' else 'SteelBlue'
                    ii.content += f'<circle cx="{e.image_x}" cy="{e.image_y}" r="15" fill="none" stroke="{color}" stroke-width="4" />'
                    ui.notify(f'{e.type} at ({e.image_x:.1f}, {e.image_y:.1f})')

                
                ii = ui.interactive_image('./assets/sparkline_table.png', 
                                          on_mouse=mouse_handler, 
                                          events=['mousedown', 'mouseup'], 
                                          cross=True) # show cross on hover

        # what appears in realtime tab
        # TODO: what are the needed params?
        with ui.tab_panel(realtime):
            ui.label('Realtime table')

ui.run()
