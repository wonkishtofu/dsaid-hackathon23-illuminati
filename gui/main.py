import calendar
import os
import time
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

import numpy as np
from matplotlib import pyplot as plt
from nicegui import Client, app, ui
from nicegui.events import MouseEventArguments

"""
# import scripts to enable API linking
import sys
from conversions import to_bearing
from demand import get_demand_estimate
from geocode import geocode
from pvwatts import get_solar_estimate
from solarposition import get_optimal_angles, get_suninfo
"""
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
        sparkline = ui.tab('ESTIMATOR')
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
                # create input fields
                # 1. enter address
                ADDRESS = ui.input(label = 'Enter an address or zipcode in Singapore', validation = {'Input too short': lambda value: len(value) >= 5}).classes('w-80')
                ADDRESS.props('clearable')
                
                #LAT, LON = geocode(ADDRESS.value) # needs to happen on enter
                #LAT, LON = geocode(str(ADDRESS))
                
                # 2. enter dwelling type
                dwelling_types = ['1-room / 2-room', '3-room', '4-room', '5-room and Executive', 'Landed Properties']
                DWELLING = ui.select(label = 'Select dwelling type', options = dwelling_types, with_input = True).classes('w-80')
                
                # if DWELLING.value == 'Landed Properties': # needs to happen on enter
                # 3. if landed property, enter estimated roof area
                ui.label('Estimate your roof area in m²')
                ROOF_AREA = ui.slider(min = 10, max = 200, value = 10).classes('w-80')
                ui.label().bind_text_from(ROOF_AREA, 'value')
                
                # button to generate estimate (needs to trigger the usage of user inputs to compute)
                ui.button('Get Estimate!', on_click = lambda: ui.notify(f'Estimating your solar consumption and generation'))
                
                DT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) # UTC
                
                # exposure_times = get_suninfo(LAT, LON, DT) # needs to happen on enter
                
                # if DT < exposure_times['dawn'] or DT > exposure_times['dusk']:
                #     icon = ui.image('./assets/nosun.svg').classes('w-16')
                # elif DT <= exposure_times['sunrise'] or DT >= exposure_times['sunset']:
                #     icon = ui.image('./assets/halfsun.svg').classes('w-16')
                # else:
                #     icon = ui.image('./assets/fullsun.svg').classes('w-16')
                
        # what appears in realtime tab
        # TODO: what are the needed params?
        with ui.tab_panel(realtime):
            with ui.column().classes('w-full items-center'):
                ui.label('Realtime table')

                # create plot using matplotlib.pyplot
                plt.figure(figsize=(8, 6), dpi=80)
                x = np.linspace(0.0, 5.0)
                y = np.cos(2 * np.pi * x) * np.exp(-x)
                plt.plot(x, y, '-')
                os.makedirs('./assets/', exist_ok=True)
                plt.savefig('./assets/sparkline_table.png')
                app.add_static_files('/assets/', './assets/')
                
                def mouse_handler(e: MouseEventArguments):
                    print(e)
                    ii.tooltip(f'{e.image_x}, {e.image_y}')
                    ii.update()
                    # ii.content += f'<circle cx="{e.image_x}" cy="{e.image_y}" r="15" fill="none" stroke="{color}" stroke-width="4" />'
                    # ui.notify(f'{e.type} at ({e.image_x:.1f}, {e.image_y:.1f})')

                
                ii = ui.interactive_image('./assets/sparkline_table.png',
                                            on_mouse=mouse_handler,
                                            events=['click'],
                                            cross=True) # show cross on hover
                ii.tooltip('After')

ui.run()
