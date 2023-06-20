from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from nicegui import Client, ui

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

    user_id = str(uuid4())
    avatar = f'https://robohash.org/{user_id}?bgset=bg2'

    anchor_style = r'a:link, a:visited {color: inherit !important; text-decoration: none; font-weight: 500}'
    ui.add_head_html(f'<style>{anchor_style}</style>')
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
    
    def on_tab_change(event):
        print(event.value)
        avatar_ui.set_visibility(event.value == 'CHATBOT')
        text.set_visibility(event.value == 'CHATBOT')

    with ui.tabs().classes('w-full') as tabs:
        chatbot = ui.tab('CHATBOT')
        sparkline = ui.tab('SPARKLINE')
        realtime = ui.tab('REALTIME')
        
    with ui.tab_panels(tabs, 
                       value=chatbot, 
                       on_change=on_tab_change).classes('w-full'):

        with ui.tab_panel(chatbot):
            print(tabs)
        with ui.tab_panel(sparkline):
            print(tabs)
            ui.label('Second tab')
        with ui.tab_panel(realtime):
            print(tabs)
            ui.label('Third tab')

ui.run()