from datetime import datetime
from typing import List, Tuple
from uuid import uuid4
import numpy as np
from matplotlib import pyplot as plt

from nicegui import app, Client, ui

messages: List[Tuple[str, str, str, str]] = []
curr_tab = ''


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
        avatar_ui.set_visibility(event.value == 'CHATBOT')
        text.set_visibility(event.value == 'CHATBOT')
        # sparkline_head.set_visibility(event.value == 'SPARKLINE')
        # sparkline_body.set_visibility(event.value == 'SPARKLINE')

    with ui.tabs().classes('w-full') as tabs:
        chatbot = ui.tab('CHATBOT')
        sparkline = ui.tab('SPARKLINE')
        realtime = ui.tab('REALTIME')
        
    with ui.tab_panels(tabs, 
                       value=chatbot, 
                       on_change=on_tab_change).classes('w-full'):

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
            
        with ui.tab_panel(sparkline):
            from sparkline.main import html_code_str_head, html_code_str_body, js_script_str
            from sparkline.chart_min_js import chart_min_js_str
            
            app.add_static_files('/sparkline', './sparkline')

            with ui.column().classes('w-full max-w-3xl mx-auto my-6'):
                with ui.row().classes('w-full no-wrap items-center'):
                    with ui.pyplot(figsize=(3, 2)):
                        x = np.linspace(0.0, 5.0)
                        y = np.cos(2 * np.pi * x) * np.exp(-x)
                        plt.plot(x, y, '-')
            #         sparkline_head = ui.html('<link rel="stylesheet" href="./sparkline/style.css">')
            #         sparkline_body = ui.html('<div class="chart__container"><canvas id="chart" width="600" height="300"></canvas></div>')
            
            # await ui.run_javascript(chart_min_js_str, respond=False)
            # await ui.run_javascript(js_script_str, respond=False)
                
        with ui.tab_panel(realtime):
            ui.label('Realtime table')

ui.run()