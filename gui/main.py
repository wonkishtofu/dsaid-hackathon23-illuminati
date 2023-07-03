import calendar
import os
import time
from datetime import datetime
from dateutil import tz
from dotenv import find_dotenv, load_dotenv
from typing import List, Tuple
from uuid import uuid4

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from nicegui import Tailwind, Client, app, ui
from nicegui.events import MouseEventArguments
import mermaid

import sys

""" LOAD API KEYS FROM ENV """
#_ = load_dotenv(find_dotenv(filename='tab2_apikeys.txt')) # XUEAN PATH
_ = load_dotenv(find_dotenv())
PVWATTS_API_KEY = os.environ['PVWATTS_API_KEY']
OPENUV_API_KEY = os.environ['OPENUV_API_KEY']
TOMTOM_API_KEY = os.environ['TOMTOM_API_KEY']

""" IMPORT FUNCTIONS FOR ESTIMATOR TAB """
#sys.path.insert(0, r'C:/Users/Zhong Xuean/Documents/dsaid-hackathon23-illuminati/api/') # XUEAN PATH
sys.path.insert(0, r'../api/')
from conversions import to_bearing
from demand import get_demand_estimate, get_hours_elapsed
from geocode import geocode
from pvwatts import get_solar_estimate
from solarposition import get_optimal_angles, get_suninfo, utc_to_sgt, time_readable

# TODO: modularize hot loading LLM to make this script more readable and lightweight
#########################
# START HOT LOADING LLM #
#########################

from pathlib import Path

import openai
from langchain import OpenAI
from langchain.agents import initialize_agent
from langchain.chains.conversation.memory import ConversationBufferMemory
from llama_index import (ListIndex, LLMPredictor, ServiceContext,
                         VectorStoreIndex, download_loader)
from llama_index.indices.composability import ComposableGraph
from llama_index.indices.query.query_transform.base import \
    DecomposeQueryTransform
from llama_index.langchain_helpers.agents import (IndexToolConfig,
                                                  LlamaToolkit,
                                                  create_llama_chat_agent)
from llama_index.query_engine.transform_query_engine import \
    TransformQueryEngine

## ADDING XUEAN'S NODE POST PROCESSOR
# sys.path.insert(0, '../chatbot/')
# sys.path.insert(1,'../gui/assets/')
# #sys.path.insert(0, r'C:/Users/Zhong Xuean/Documents/dsaid-hackathon23-illuminati/chatbot/') # XUEAN PATH
# from custom_node_processor import CustomSolarPostprocessor

from dotenv import find_dotenv, load_dotenv

#_ = load_dotenv(find_dotenv(find_dotenv(filename='C:/Users/Zhong Xuean/Documents/dsaid-hackathon23-illuminati/chatbot/apikey.txt'))) # XUEAN PATH
# _ = load_dotenv(find_dotenv())
# openai.api_key = os.environ["OPENAI_API_KEY"]

"""
# list ema docs
ema = [1,2,3,4,5,6,7,8,9]

UnstructuredReader = download_loader("UnstructuredReader", refresh_cache=True)
loader = UnstructuredReader()
doc_set = {}
all_docs = []

for ema_num in ema:
    #ema_docs = loader.load_data(file=Path(f'C:/Users/Zhong Xuean/Documents/dsaid-hackathon23-illuminati/chatbot/data/EMA/EMA_{ema_num}.csv'), split_documents=False) # XUEAN PATH
    ema_docs = loader.load_data(file=Path(f'../chatbot/data/EMA/EMA_{ema_num}.csv'), split_documents=False)
    # insert year metadata into each year
    for d in ema_docs:
        d.extra_info = {"ema_num": ema_num}
    doc_set[ema_num] = ema_docs
    all_docs.extend(ema_docs)


### Setup a Vector Index for each EMA doc in the data file
# We setup a separate vector index for each file
# We also optionally initialize a "global" index by dumping all files into the vector store.


# initialize simple vector indices + global vector index
# NOTE: don't run this cell if the indices are already loaded!
index_set = {}
service_context = ServiceContext.from_defaults(chunk_size=512)
for ema_num in ema:
    cur_index = VectorStoreIndex.from_documents(doc_set[ema_num], service_context=service_context)
    index_set[ema_num] = cur_index

# Load indices from disk
index_set = {}
for ema_num in ema:
    index_set[ema_num] = cur_index

### Composing a Graph to synthesize answers across all the existing EMA docs.
# We want our queries to aggregate/synthesize information across *all* docs.
# To do this, we define a List index on top of the 4 vector indices.

index_summaries = [f"These are the official documents from EMA. This is document index {ema_num}." for ema_num in ema]

index_summary_new = []

index_summary_new.append('These are official documents Q&A documents from EMA. Structured as a CSV with the following columns: (Title -- Questions -- Answers)')

index_summary_new.append('These are official documents Q&A documents from EMA. Structured as a CSV with the following columns: (Title -- Questions -- Answers)')

index_summary_new.append('This official document from EMA contains all minister speeches on Singapore\s energy policy. Structured as a CSV with the following columns: (Title -- Date -- Content)')

index_summary_new.append('This official document from EMA summaries of videos in document index 3. Structured as a CSV with the following columns: (Title -- Summary)')

index_summary_new.append('This official document from EMA contains the official video transcript of policy explainers from EMA. Structured as a CSV with the following columns: (URL Source -- Title -- Content)')

index_summary_new.append('This official document from EMA contains the contents of EMA\'s Official Solar Handbook. Structured as a CSV with the following columns: (URL Source -- Title -- Content)')

index_summary_new.append('This official document from EMA contains the Question and Answer component of EMA\'s Official Solar Handbook. Structured as a CSV with the following columns: (URL Source -- Title -- Content)')

index_summary_new.append('This official document from EMA contains the summaries of EMA\'s Official Solar Handbook. Structured as a CSV with the following columns: (Title -- Summary)')

index_summary_new.append('This official document from EMA contains the raw content of EMA\'s Official Solar Handbook. Structured as a CSV with the following columns: (Chapter -- Subheader1 -- Subheader2 -- Text)')


# set number of output tokens
llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, max_tokens=512))
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)

# define a list index over the vector indices
# allows us to synthesize information across each index
graph = ComposableGraph.from_indices(
    ListIndex,
    [index_set[ema_num] for ema_num in ema],
    index_summaries=index_summaries,
    service_context=service_context
)

## Setting up the Chatbot Agent
# We use Langchain to define the outer chatbot abstraction. We use LlamaIndex as a core Tool within this abstraction.

# define a decompose transform
decompose_transform = DecomposeQueryTransform(
    llm_predictor, verbose=True
)

# define custom query engines
custom_query_engines = {}
for index in index_set.values():
    query_engine = index.as_query_engine()
    query_engine = TransformQueryEngine(
        query_engine,
        query_transform=decompose_transform,
        transform_extra_info={'index_summary': index.index_struct.summary},
    )
    custom_query_engines[index.index_id] = query_engine
custom_query_engines[graph.root_id] = graph.root_index.as_query_engine(
    response_mode='tree_summarize',
    verbose=True,
)

# construct query engine
graph_query_engine = graph.as_query_engine(custom_query_engines=custom_query_engines)
node_postprocessor = CustomSolarPostprocessor(service_context=service_context, top_k_recency = 1, top_k_min = 3)

query_engine_node_postproc = index.as_query_engine(
    similarity_top_k=3,
    node_postprocessors=[node_postprocessor]
)

index_configs = []

for y in range(1, 9):
    query_engine_node_postproc = index.as_query_engine(
        similarity_top_k=3,
        node_postprocessors=[node_postprocessor]
    )
    tool_config = IndexToolConfig(
        query_engine=query_engine,
        name=f"Vector Index {y}",
        description=f"Necessary for when you want to answer queries about solar energy, EMA's energy policy, and other energy policy related matters {y} ",
        tool_kwargs={"return_direct": True, "return_sources": True},
    )
    index_configs.append(tool_config)

graph_config = IndexToolConfig(
    query_engine=graph_query_engine,
    name=f"Graph Index",
    description="Necessary for when you need to cross-reference files from EMA's official documents.",
    tool_kwargs={"return_direct": True, "return_sources": True},
    return_sources=True
)

toolkit = LlamaToolkit(
    index_configs=index_configs,
    graph_configs=[graph_config]
)


# initialize agent
memory = ConversationBufferMemory(memory_key="chat_history")
llm=OpenAI(temperature=0)
agent_chain = create_llama_chat_agent(
    toolkit,
    llm,
    memory=memory,
)

inj = '''
        
        Please respond to the statement above.
        Your name is Jamie Neo. Your pronouns are they/them.
        You are an AI chatbot created to support EMA by answering questions about solar energy in Singapore.
        You will answer only with reference to official documents from EMA.
        Refer to the context FAQs and the EMA documents in composing your answers. Define terms if needed.
        If the user is unclear, you can ask the user to clarify the question.
        When in doubt and/or the answer is not in the EMA documents, you can say "I am sorry but do not know the answer. Please get in touch with EMA through this webpage: https://www.ema.gov.sg/"
        Keep your answers short and terse. Be polite at all times.
    '''

def get_chatbot_respone(text_input):
    return agent_chain.run(input = text_input + inj)
"""

#######################
# END HOT LOADING LLM #
#######################

#############
# START GUI #
#############

"""
messages: List[Tuple[str, str, str, str]] = []
thinking: bool = False

# bot id and avatar
sys.path.insert(0, '../gui/')
bot_id = str('b15731ba-d28c-4a77-8076-b5750f5296d3')
#bot_avatar = f'https://robohash.org/{bot_id}?bgset=bg2'
bot_avatar = 'https://raw.githubusercontent.com/wonkishtofu/dsaid-hackathon23-illuminati/main/gui/assets/bot.png'

disclaimer = "Hello there! I am Jamie Neo, an AI chatbot with a sunny disposition 😎 On behalf of the Energy Market Authority (EMA), I'm here to answer your questions about solar energy in Singapore."

messages.append(('Bot', bot_avatar, disclaimer))

# refresh function for CHATBOT
@ui.refreshable
async def chat_messages(own_id: str) -> None:
    for user_id, avatar, text in messages:
        ui.chat_message(text = text, avatar = avatar, sent = own_id == user_id)
    if thinking:
        # TODO: SHOW UI.SPINNER BEFORE RESPONSE GENERATION
        ui.classes('self-center')
        ui.spinner(size='3rem').classes('self-center')
    await ui.run_javascript("window.scrollTo(0,document.body.scrollHeight)", respond = False) # autoscroll

"""
# bot avatar
bot_avatar = 'https://raw.githubusercontent.com/wonkishtofu/dsaid-hackathon23-illuminati/main/gui/assets/bot.png'

@ui.page('/')
async def main(client: Client):
    """
    async def send() -> None:
        user_input = text.value
        messages.append((user_id, avatar, user_input))
        chat_messages.refresh()
        thinking = True
        text.value = ''
        # TODO: CLEAR TEXT UPON SEND
        # TODO: DECREASE LAG BETWEEN SEND AND APPEAR IN CONVERSATION
        text.label = ''

        response = get_chatbot_respone(user_input)
        messages.append(('Bot', bot_avatar, response))
        thinking = False
        text.set_value(None)

    def on_tab_change(event):
        print(event.value)
        # remove the text and avatar when move to different tab
        # have to do this cos they are in footer
        avatar_ui.set_visibility(event.value == 'CHATBOT')
        text.set_visibility(event.value == 'CHATBOT')
    
    """
    
    # define the tabs
    with ui.header().classes(replace = 'row items-center') as header:
        with ui.tabs().classes('w-full') as tabs:
            chatbot = ui.tab('SEARCH')
            estimator = ui.tab('ESTIMATOR')
            #realtime = ui.tab('REALTIME')
            resources = ui.tab('RESOURCES')
    
    # set tabs in a tab panel
    with ui.tab_panels(tabs,
                       value = chatbot).classes('w-full'): #on_change = on_tab_change
        
        
        # what appears in chatbot tab
        with ui.tab_panel(chatbot):
            with ui.column().classes('w-full items-center'):
                ui.image(bot_avatar).classes('w-20 h-20')
                ui.link('Talk to Jamie Neo!', 'https://ema-doc-search.vercel.app/', new_tab = True).style('font-weight: 1000; font-size: 150%')

            """
            user_id = str('6af9dba1-022a-41ba-8f5b-34c21d1cc89a')
            avatar = f'https://robohash.org/{user_id}?bgset=bg2'
            
            # TODO: change color of speech bubble for something less jarring
            with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
                with ui.row().classes('w-full no-wrap items-center'):
                    avatar_ui = ui.avatar().on('click', lambda: ui.open(main))
                    with avatar_ui:
                        ui.image(avatar)
                    text = ui.input(placeholder = 'type your query here').on('keydown.enter', send) \
                        .props('rounded outlined input-class=mx-6').classes('flex-grow')
                    text.props('clearable') # button to clear type text
            
            await client.connected()  # chat_messages(...) uses run_javascript which is only possible after connecting

            with ui.column().classes('w-full max-w-2xl mx-auto items-stretch'):
                await chat_messages(user_id)
        """
        # what appears in estimator tab
        with ui.tab_panel(estimator):
            # initiate variables 
            global_vars = {'LAT': 0, 'LON': 0,
                           'AZIMUTH': 0, 'TILT': 0,
                           'YTD_DEMAND': 1, 'ANNUAL_DEMAND': 1,
                           'YTD_SUPPLY': 0, 'ANNUAL_SUPPLY': 0,
                           'HOURS_ELAPSED': 0, 'NUM_PANELS': 1,
                           'SYSTEM_MSG': ""}
            rerun_vars = {'YTD_SUPPLY': 0, 'ANNUAL_SUPPLY': 0,
                          'NUM_PANELS': 1} # variables that can change as you toggle back and forth

            with ui.stepper().props('vertical').classes('w-full') as stepper:

                with ui.step('Address'):
                    # 1. enter address
                    ADDRESS = ui.input(label = 'Enter an address or postal code',
                       validation = {'Input too short': lambda value: len(value) >= 5})\
                        .props('clearable')\
                        .classes('w-80')\
                        .on('keydown.enter', lambda: trigger_generation.refresh())
                    
                    #Spinner before results load
                    # spinner = ui.spinner(size='lg')
                    # spinner.visible = False
                    
                    # generation function for ESTIMATOR, triggered upon entering an address
                    @ui.refreshable
                    async def trigger_generation():

                        """
                        FUNCTION to trigger address-related api calls including:
                        1. geocode to get LAT, LON coordinates, and SYSTEM_MSG
                        2. get_suninfo to get exposure_times dictionary with time of dawn, sunrise, sunriseEnd, solarNoon, sunsetStart, sunset, dusk
                        3. pick icon to display alongside current datetime (DT) based on time of day
                        4. get_optimal_angles to get optimal azimuth and altitude angles for PVWatts query
                        """

                        #def generate_demand():
                        if ADDRESS.value != "":
                            try:
                                # sequentially run all the functions to return outputs
                                LAT, LON, SYSTEM_MSG = geocode(ADDRESS.value)
                                DT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) # UTC
                                exposure_times = get_suninfo(LAT, LON, DT)
                                azimuth, tilt = get_optimal_angles(LAT, LON, exposure_times)
                                AC_output, SYSTEM_MSG2 = get_solar_estimate(LAT, LON, azimuth, tilt)
                                hours_elapsed = get_hours_elapsed(DT)
                                
                                # calculate annual & year-to-date generation estimate
                                annual_supply = sum(AC_output)/1000
                                ytd_supply = sum(AC_output[:hours_elapsed])/1000
                                
                                # assign to global variables
                                global_vars.update([('LAT', LAT), ('LON', LON),
                                                    ('AZIMUTH', azimuth), ('TILT', tilt),
                                                    ('YTD_SUPPLY', ytd_supply), ('ANNUAL_SUPPLY', annual_supply),
                                                    ('HOURS_ELAPSED', hours_elapsed), ('SYSTEM_MSG', SYSTEM_MSG2)])
                                rerun_vars.update([('YTD_SUPPLY', ytd_supply), ('ANNUAL_SUPPLY', annual_supply)])
                                
                                # output the system message and the coordinates
                                with ui.column().classes('w-100 items-left'):
                                    ui.label(f"{SYSTEM_MSG}")
                                    ui.label(f"The coordinates are ({LAT}, {LON})")
                                    
                                    # output sun icon and current time
                                    with ui.row():
                                        if pd.to_datetime(DT) < pd.to_datetime(exposure_times['dawn']) or pd.to_datetime(DT) > pd.to_datetime(exposure_times['dusk']):
                                            ui.image('./assets/nosun.svg').classes('w-8')
                                            ui.label(f"\nCurrent time is {time_readable(utc_to_sgt(DT))}\n").style("font-weight: 1000")
                                            ui.image('./assets/nosun.svg').classes('w-8')
                                        elif pd.to_datetime(DT) <= pd.to_datetime(exposure_times['sunriseEnd']) or pd.to_datetime(DT) >= pd.to_datetime(exposure_times['sunsetStart']):
                                            ui.image('./assets/halfsun.svg').classes('w-8')
                                            ui.label(f"\nCurrent time is {time_readable(utc_to_sgt(DT))}\n").style("font-weight: 1000")
                                            ui.image('./assets/halfsun.svg').classes('w-8')
                                        else:
                                            ui.image('./assets/fullsun.svg').classes('w-8')
                                            ui.label(f"\nCurrent time is {time_readable(utc_to_sgt(DT))}\n").style("font-weight: 1000")
                                            ui.image('./assets/fullsun.svg').classes('w-8')
                                            
                                    # output grid with solar exposure timeline
                                    ui.label("Today's Expected Solar Exposure:\n").style("font-weight: 1000")
                                    with ui.grid(columns = 2):
                                        ui.label(f"{time_readable(utc_to_sgt(exposure_times['dawn']))}")
                                        ui.label("DAWN")
                                        ui.label(f"{time_readable(utc_to_sgt(exposure_times['sunrise']))}")
                                        ui.label("SUNRISE")
                                        ui.label(f"{time_readable(utc_to_sgt(exposure_times['solarNoon']))}")
                                        ui.label("SOLAR NOON")
                                        ui.label(f"{time_readable(utc_to_sgt(exposure_times['sunset']))}")
                                        ui.label("SUNSET")
                                        ui.label(f"{time_readable(utc_to_sgt(exposure_times['dusk']))}")
                                        ui.label("DUSK")
                                    
                                    # output grid with optimal solar panel orientation
                                    ui.label("Optimal Solar Panel Orientation:\n").style("font-weight: 1000")
                                    with ui.grid(columns = 2):
                                        ui.label("Azimuth")
                                        ui.label(f"{np.round(azimuth, 2)}° ({to_bearing(azimuth)})")
                                        ui.label("Tilt")
                                        ui.label(f"{np.round(tilt,2)}°")
                                
                                # make NEXT button appear
                                with ui.stepper_navigation():
                                    with ui.row():
                                        # ui.button('Regenerate Results', on_click = lambda: trigger_generation.refresh())
                                        ui.button('Next', on_click = stepper.next)
                            
                            except AssertionError:
                                with ui.column().classes('w-100 items-left'):
                                    ui.label("Oops! The address you have queried was not found in Singapore")
                                    ui.label("Please input a Singapore address or postal code or simply type 'SUNNY' and hit enter for an island-averaged estimate.")
                        
                        # spinner.set_visibility(True)
                        # await generate_demand()
                        # spinner.set_visibility(False)
                        # end of function

                    trigger_generation() 
                    #await ui.run_javascript("window.scrollTo(0,document.body.scrollHeight)", respond = False) # autoscroll
                                     
                with ui.step('Consumption'):
                    # 2. enter dwelling type
                    DWELLING = ui.select(label = 'Select dwelling type',
                        options = ['1-room / 2-room', '3-room', '4-room', '5-room and Executive', 'Landed Property'],
                        with_input = True)\
                        .classes('w-80')\
                        .on('update:model-value', lambda: trigger_roofarea.refresh())

                    # refresh roof area function for ESTIMATOR triggered upon entering dwelling type
                    @ui.refreshable
                    def trigger_roofarea():
                        DT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        try:
                            # get annual and ytd demand estimate
                            annual_demand, ytd_demand = get_demand_estimate(DT, DWELLING.value)
                            # assign to global variables
                            global_vars.update([('YTD_DEMAND', ytd_demand), ('ANNUAL_DEMAND', annual_demand)])
                            
                            # output grid with annual and ytd demand
                            with ui.column().classes('w-100 items-left'):
                                ui.row()
                                ui.label(f"Average Energy Consumption of {DWELLING.value}").style("font-weight: 1000")
                                with ui.grid(columns = 2):
                                    ui.label(f"Annual:")
                                    ui.label(f"{np.round(annual_demand,0):,} kWh")
                                    ui.label(f"Year-to-date*:")
                                    ui.label(f"{np.round(ytd_demand,0):,} kWh")
                                ui.label("*estimated to the current hour").style("font-weight: 300")
                        except:
                            pass
                        
                        # if Landed Property, as for roof area input
                        if DWELLING.value == "Landed Property":
                            with ui.column().classes('w-100 items-left'):
                                ui.separator().classes('w-80')
                                ui.label('Estimate your roof area in m²').style("font-weight: 1000")
                                ROOF_AREA = ui.slider(min = 10, max = 200, value = 10).classes('w-80')
                                ui.label().bind_text_from(ROOF_AREA, 'value', backward = lambda x: f"{x} m²")
                                ui.separator().classes('w-80')
                            
                            # function to dynamically update global variables
                            def update_num_panels(ROOF_AREA):
                                global_vars.update(NUM_PANELS = int(np.floor(float(ROOF_AREA)/1.6)))
                                x = rerun_vars['ANNUAL_SUPPLY']
                                global_vars.update(ANNUAL_SUPPLY = x*int(np.floor(float(ROOF_AREA)/1.6)))
                                x = rerun_vars['YTD_SUPPLY']
                                global_vars.update(YTD_SUPPLY = x*int(np.floor(float(ROOF_AREA)/1.6)))
                                return f"You can fit {int(np.floor(float(ROOF_AREA)/1.6))} Standard 250 W (1.6 m²) Solar Panels on your roof."
                                
                            # show number of solar panels
                            with ui.column().classes('w-100 items-left'):
                                with ui.grid(columns = 1):
                                    ui.label()\
                                        .bind_text_from(ROOF_AREA, 'value', backward = lambda x: update_num_panels(x))\
                                        .style("font-weight: 1000")
                        else:
                            global_vars.update([('NUM_PANELS', 1),
                                                ('YTD_SUPPLY', rerun_vars['YTD_SUPPLY']),
                                                ('ANNUAL_SUPPLY', rerun_vars['ANNUAL_SUPPLY'])])
                        
                        # make NEXT button appear
                        # make BACK button appear
                        with ui.stepper_navigation():
                            ui.button('Next', on_click = stepper.next)
                            ui.button('Back', on_click = stepper.previous).props('flat')
                            
                    trigger_roofarea() # end of function
                    #await ui.run_javascript("window.scrollTo(0,document.body.scrollHeight)", respond = False) # autoscroll

                with ui.step('Supply'):
                    with ui.column().classes('w-100 items-left'):
                        with ui.column().classes('w-100 items-left'):
                            ui.label("Estimated Solar Energy Generation").style("font-weight: 1000")
                            ui.label().bind_text_from(global_vars, 'NUM_PANELS', backward=lambda x: f"[from {x} Standard 250 W Solar Panel(s)]")
                        with ui.grid(columns = 2):
                            ui.label(f"Annual:")
                            ui.label().bind_text_from(global_vars, 'ANNUAL_SUPPLY', backward=lambda x: f"{np.round(x,0):,} kWh")
                            ui.label(f"Year-to-date*:")
                            ui.label().bind_text_from(global_vars, 'YTD_SUPPLY', backward=lambda x: f"{np.round(x,0):,} kWh")
                        ui.label("*estimated to the current hour").style("font-weight: 300")
                        
                        with ui.column().classes('w-100 items-left'):
                            ui.label("Proportion of Personal Consumption Satisfied:").style("font-weight: 1000")
                            ui.label().bind_text_from(global_vars, 'ANNUAL_SUPPLY', backward=lambda x: f"{np.round(100*x/global_vars['ANNUAL_DEMAND'],1)}%")\
                                .style("font-size: 300%")
                                
                            ui.separator().classes('w-80')
                            ui.label().bind_text_from(global_vars, 'SYSTEM_MSG', backward=lambda x: f"{x}")
                            ui.separator().classes('w-80')
                            
                            ui.label(f"Factored into this estimate are an 85% system efficiency and a 15% solar module efficiency, which are standard assumptions made by the National Renewable Energy Laboratory. Your realized output may differ from this estimate based on real-time weather and structural considerations. Visit ema.gov.sg/Guide_to_Solar_PV.aspx for more information.").style("font-weight: 300")
                    
                    # make BACK button appear
                    with ui.stepper_navigation():
                        ui.button('Back', on_click = stepper.previous).props('flat')
        """
        # COMMENTING OUT REAL-TIME TAB
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
        """
        
        # what appears in resources tab
        with ui.tab_panel(resources):
            #await ui.run_javascript("window.scrollTo(0,document.body.scrollHeight)", respond = False) # autoscroll

            with ui.expansion('PV Cell Types').classes('w-full').style('font-weight:1000'):
                    # with ui.column().classes('w-full'):
                    ui.mermaid('''
                    graph LR;
                        id1[PV CELL TYPES   ]-->id2[Crystalline Silicon   ];
                        id1[PV CELL TYPES   ]-->id3[Thin Film   ];
                        id2[Crystalline Silicon   ]-->id7[Polycrystalline   ];
                        id2[Crystalline Silicon   ]-->id8[Monocrystalline   ];
                        id3[Thin Film   ]-->id4[Amorphous Silicon, a-Si   ];
                        id3[Thin Film   ]-->id5[Tandem a-Si   ];
                        id3[Thin Film   ]-->id6[Microcrystalline   ];
                        id3[Thin Film   ]-->id9[CIGS   ];
                        id3[Thin Film   ]-->id10[CdTe   ];
                    ''')
                    
            with ui.expansion('Licensing Guidelines').classes('w-full').style('font-weight:1000'):
                    #with ui.column().classes('w-full'):
                    ui.mermaid('''
                    graph TD;
                        id1[Proposed PV system]-->id2[Capacity less than 1 MW];
                        id1[Proposed PV system]-->id3[Capacity 1-10 MW];
                        id1[Proposed PV System]-->id4[Capacity greater than 10 MW];
                        
                        id4[Capacity greater than 10 MW]-->id5[Generation License];
                        
                        id3[Capacity 1-10 MW]-->id8[NOT Connected to Grid];
                        id8[NOT Connected to Grid]-->id9[No License Required];
                        
                        id3[Capacity 1-10 MW]-->id6[Connected to Grid];
                        id6[Connected to Grid]-->id7[Wholesaler Generation License];
                        
                        id2[Capacity less than 1 MW]-->id9[No License Required];
                    ''')

            with ui.expansion('Schemes Available for Consumers').classes('w-full').style('font-weight:1000'):
                    #with ui.column().classes('w-full'):
                    ui.mermaid('''
                    graph TD;
                        id1[Contestable Consumer]-->id2[Capacity less than 1 MWac];
                        id1[Contestable Consumer]-->id3[Capacity 1-10 MWac];
                        id1[Contestable Consumer]-->id4[Capacity greater than 10 MWac];
                        
                        id2[Capacity less than 1 MWac]-->id5[NO Payment for Excess Generation];
                        id2[Capacity less than 1 MWac]-->id6[Payment for Excess Generation];
                        
                        id5[NO Payment for Excess Generation]-->id7[No Scheme Needed];
                        id6[Payment for Excess Generation]-->id8[Enhanced Central Intermediary Scheme];
                        
                        id3[Capacity 1-10 MWac]-->id8[Enhanced Central Intermediary Scheme];
                        id3[Capacity 1-10 MWac]-->id9[Register as MP with Energy Market Company];
                        
                        id4[Capacity greater than 10 MWac]-->id9[Register as MP with Energy Market Company]
                        
                        id10[Not Contestable Consumer]-->id11[Capacity less than 1 MWac];
                        id11[Capacity less than 1 MWac]-->id12[Simplified Credit Treatment Scheme, SCT];
                    ''')

            with ui.expansion('Installation Guide').classes('w-full').style('font-weight:1000'):
                    #with ui.column().classes('w-full'):
                    ui.mermaid('''
                    graph TD;
                        id((START))-->id1[Check with URA or qualified person, QP, if PV can be installed];
                        id1[Check with URA or qualified person if PV can be installed]-->id2{Planning Required?};
                        id2[Planning Required?]-->NO;
                        id2[Planning Required?]-->YES;
                        YES-->id3[Submit development application to URA through QP, allow 4 weeks];
                        NO-->id4[Appoint PV System Contractor to assess building structure, condition, loading];
                        id3[Submit development application to URA with qualified person, allow 4 weeks]-->id4[Appoint PV System Contractor to assess building structure, condition, loading];
                        id4[Appoint PV System Contractor to assess building structure, condition, loading]-->id5{Compliant with loading requirements?};
                        id5[Compliant with loading requirements?]-->id6[YES];
                        id5[Compliant with loading requirements?]-->id7[NO];
                        id6[YES]-->id8[Connecting to Grid?];
                        id8[Connecting to Grid?]-->id9[NO];
                        id9[NO]-->id10((END));
                        id7[NO]-->id11[Submit building plans to BCA for structural strengthening, allow 14 days];
                        id11[Submit building plans to BCA for structural strengthening, allow 14 days]-->id8[Connecting to Grid?];
                        id8[Connecting to Grid?]-->id12[YES];
                        id12[YES]-->id13[Contractor appoints Licensed Electrical Worker to install and connect PV system to grid];
                        id13[Contractor appoints Licensed Electrical Worker, LEW, to install and connect PV system to grid]-->id14[LEW submits application form to SP Services];
                        id14[LEW submits application form to SP Services]-->id15[SP PowerGrid evaluates technical specifications];
                        id15[SP PowerGrid evaluates technical specifications]-->id16[Comply with technical requirements?];
                        id16[Comply with technical requirements?]-->id17[NO];
                        id17[NO]-->id15[SP PowerGrid evaluates technical specifications];
                        id16[Compliant with technical requirements?]-->id18[YES];
                        id18[YES]-->id19[SP PowerGrid to advise connection scheme];
                        id19[SP PowerGrid to advise connection scheme]-->id20[LEW install, test, commission PV system and connection];
                        id20[LEW install, test, commission PV system and connection]-->id21[inform SP Services and PowerGrid when completed];
                        id21[inform SP Services and PowerGrid when completed]-->id22[Contractor O&M manual to homeowner with 12 month warranty];
                        id22[Contractor O&M manual to homeowner with 12 month warranty]-->id23((END));
                    ''')

ui.run(title = "Jamie Neo [EMA]")
