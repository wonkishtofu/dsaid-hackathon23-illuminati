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

# import functions from API folder for estimator tab
import sys
sys.path.insert(0, r'../api/')
from conversions import to_bearing
from demand import get_demand_estimate
from geocode import geocode
from pvwatts import get_solar_estimate
from solarposition import get_optimal_angles, get_suninfo

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

# adding Xuean's node post processor
import sys
sys.path.insert(0, '../chatbot/')
#sys.path.insert(0, r'.../dsaid-hackathon23-illuminati/chatbot/') # Xuean's edit - original line didn't work on my laptop
from custom_node_processor import CustomSolarPostprocessor

from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())
openai.api_key = os.environ["OPENAI_API_KEY"]

# list ema docs
ema = [1,2,3,4]

UnstructuredReader = download_loader("UnstructuredReader", refresh_cache=True)
loader = UnstructuredReader()
doc_set = {}
all_docs = []

for ema_num in ema:
    ema_docs = loader.load_data(file=Path(f'../chatbot/data/EMA/EMA_{ema_num}.csv'), split_documents=False)
    # insert year metadata into each year
    for d in ema_docs:
        d.extra_info = {"ema_num": ema_num}
    doc_set[ema_num] = ema_docs
    all_docs.extend(ema_docs)

"""
### Setup a Vector Index for each EMA doc in the data file
We setup a separate vector index for each file
We also optionally initialize a "global" index by dumping all files into the vector store.
"""

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

"""
### Composing a Graph to synthesize answers across all the existing EMA docs.
We want our queries to aggregate/synthesize information across *all* docs. To do this, we define a List index
on top of the 4 vector indices.
"""


index_summaries = [f"These are the official documents from EMA. This is document index {ema_num}." for ema_num in ema]

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

"""
## Setting up the Chatbot Agent
We use Langchain to define the outer chatbot abstraction. We use LlamaIndex as a core Tool within this abstraction.
"""


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

for y in range(1, 4):
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
    description="Necessary for when you want to answer queries regarding EMAs energy policy.",
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

inj = """
        Please respond to the statement above.
        Your name is Jamie Neo. Your pronouns are they/them.
        You are an AI Chatbot created to support EMA in Singapore. You will answer only with reference to official documents from EMA.
        Refer to the context FAQs and the EMA documents in composing your answers.
        If the user is unclear, you can ask the user to clarify the question.
        When in doubt and/or the answer is not in the EMA documents, you can say "I am sorry but do not know the answer. Please get in touch with EMA through this webpage: https://www.ema.gov.sg/contact_us.aspx".
        Keep your answers short and as terse as possible. Be polite at all times.
    """

def get_chatbot_respone(text_input):
    return agent_chain.run(input = text_input + inj)


#######################
# END HOT LOADING LLM #
#######################

#############
# START GUI #
#############

messages: List[Tuple[str, str, str, str]] = []
thinking: bool = False

# bot id and avatar
bot_id = str('b15731ba-d28c-4a77-8076-b5750f5296d3')
bot_avatar = f'https://robohash.org/{bot_id}?bgset=bg2' # TODO: find/create static icon for Jamie Neo

# TODO: CREATE DISCLAIMER FOR BOT
disclaimer = "Hello there! I am Jamie Neo, an AI chatbot with a sunny disposition 😎 I'm here to help the Energy Market Authority (EMA) answer your questions about solar energy in Singapore."
stamp = datetime.utcnow().strftime('%X')
messages.append(('Bot', bot_avatar, disclaimer, stamp))


@ui.refreshable
async def chat_messages(own_id: str) -> None:
    for user_id, avatar, text, stamp in messages:
        ui.chat_message(text=text, stamp=stamp, avatar=avatar, sent=own_id == user_id)
    if thinking: # TODO: INSTANTANEOUS TEXT SEND (BUT UI.SPINNER UPON RESPONSE GENERATION)
        ui.spinner(size='lg', color = 'yellow').classes('self-center')
        #ui.spinner(size='3rem').classes('self-center')
    await ui.run_javascript("window.scrollTo(0,document.body.scrollHeight)", respond=False) # autoscroll


@ui.page('/')
async def main(client: Client):
    async def send() -> None:
        global thinking
        stamp = datetime.utcnow().strftime('%X')
        user_input = text.value
        messages.append((user_id, avatar, user_input, stamp))
        thinking = True
        text.value = ''
        chat_messages.refresh()

        response = get_chatbot_respone(user_input)
        stamp = datetime.utcnow().strftime('%X')
        messages.append(('Bot', bot_avatar, response, stamp))
        thinking = False
        # chat_messages.refresh()

    def on_tab_change(event):
        print(event.value)
        # remove the text and avatar when move to different tab
        # have to do this cos they are in footer
        avatar_ui.set_visibility(event.value == 'CHATBOT')
        text.set_visibility(event.value == 'CHATBOT')
        
    # define the tabs
    with ui.header().classes(replace='row items-center') as header:
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
            user_id = str('6af9dba1-022a-41ba-8f5b-34c21d1cc89a')
            avatar = f'https://robohash.org/{user_id}?bgset=bg2'
            
            with ui.footer().classes('bg-white'), ui.column().classes('w-full max-w-3xl mx-auto my-6'):
                with ui.row().classes('w-full no-wrap items-center'):
                    avatar_ui = ui.avatar().on('click', lambda: ui.open(main))
                    with avatar_ui:
                        ui.image(avatar)
                    text = ui.input(placeholder='message').on('keydown.enter', send) \
                        .props('rounded outlined input-class=mx-3').classes('flex-grow')
                    # TODO: CLEAR TEXT (VALUE AND LABEL) UPON KEYDOWN.ENTER
                    text.props('clearable') # button to clear type text
            
            await client.connected()  # chat_messages(...) uses run_javascript which is only possible after connecting

            with ui.column().classes('w-full max-w-2xl mx-auto items-stretch'):
                await chat_messages(user_id)
                # TODO: INSTANTANEOUS TEXT SEND (BUT UI.SPINNER UPON RESPONSE GENERATION)
            
        # what appears in estimator tab
        with ui.tab_panel(sparkline):
            with ui.column().classes('w-full items-center'):
                # create input fields
                # 1. enter address
                ADDRESS = ui.input(label = 'Enter an address or zipcode in Singapore', validation = {'Input too short': lambda value: len(value) >= 6}).props('clearable').classes('w-80')
                
                # 2. enter dwelling type
                dwelling_types = ['1-room / 2-room', '3-room', '4-room', '5-room and Executive', 'Landed Property']
                DWELLING = ui.select(label = 'Select dwelling type', options = dwelling_types, with_input = True).classes('w-80')
                
                if DWELLING.value == 'Landed Property': # TODO: ASK FOR ROOF AREA UPON CHOOSING LANDED PROPERTY
                # 3. if landed property, enter estimated roof area
                    ui.label('Estimate your roof area in m²')
                    ROOF_AREA = ui.slider(min = 10, max = 200, value = 10).classes('w-80')
                    ui.label().bind_text_from(ROOF_AREA, 'value')
                
                # button to generate estimate
                ui.button('Get Estimate!', on_click = lambda: ui.notify(f'Estimating your solar consumption and generation'))
                
                LAT, LON = geocode(ADDRESS.value) # TODO: RUN GEOCODE FUNCTION UPON BUTTON CLICK
                DT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) # UTC
                cloudy, exposure_times = get_suninfo(LAT, LON, DT) # needs to happen on enter
                
                if DT < exposure_times['dawn'] or DT > exposure_times['dusk']:
                    icon = ui.image('./assets/nosun.svg').classes('w-16')
                elif DT <= exposure_times['sunrise'] or DT >= exposure_times['sunset']:
                    icon = ui.image('./assets/halfsun.svg').classes('w-16')
                elif cloudy == True:
                    icon = ui.image('./assets/cloudysun.svg').classes('w-16')
                else:
                    icon = ui.image('./assets/fullsun.svg').classes('w-16')
                
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

ui.run(title = "Jamie Neo [EMA]")
