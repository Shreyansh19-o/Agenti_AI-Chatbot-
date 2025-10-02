import streamlit as st
from lg_db_be import chatbot,retrive_all_threads
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import uuid
import datetime



#*********************************************utility fun


def generate_thread_id():
    if 'chat_count' not in st.session_state:
        st.session_state['chat_count'] = 0
    st.session_state['chat_count'] += 1
    
    thread_id = f"Chat No.{st.session_state['chat_count']} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return thread_id

def reset_chat():
    thread_id=generate_thread_id()
    st.session_state['thread_id']=thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history']=[]
 

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id':thread_id}}).values['messages']
    
       



# st.session_state -> dict -> 
#*********************************************session setup


if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrive_all_threads()


    add_thread(st.session_state['thread_id'])


#**********************************************side bar
st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header("My conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id']=thread_id
        messages=load_conversation(thread_id)

        temp_msg=[]

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_msg.append({'role':role,'content':msg.content})

        st.session_state['message_history']=temp_msg

# loading the conversation history

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])



user_input = st.chat_input('Type here')


if user_input:
    # First, add the user's message to history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream(user_message):
            if not user_message:
                return  # Prevent None from being sent

            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_message)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream(user_input))

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

        st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
