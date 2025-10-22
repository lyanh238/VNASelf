import streamlit as st
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core import MultiAgentSystem

# --------------------------------------------------------------------
# CONFIG
# Initialize multi-agent system
if "multi_agent_system" not in st.session_state:
    st.session_state.multi_agent_system = None

st.set_page_config(page_title="NekAssist", page_icon="", layout="centered")

st.markdown(
    """
    <style>
    body { font-family: 'Inter', sans-serif !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
# st.markdown(
#     """
#     <style>
#     body { font-family: 'Inter', sans-serif !important; }

#     /* ----- Chat Message Styling ----- */
#     [data-testid="stChatMessage"][data-testid="stChatMessage-user"] [data-testid="stMarkdownContainer"]::before {
#         content: "🐾 "; /* Thêm emoji mèo nhỏ trước tin nhắn của user */
#         font-size: 1.5rem;
#     }

#     [data-testid="stChatMessage"][data-testid="stChatMessage-assistant"] [data-testid="stMarkdownContainer"]::before {
#         content: "https://www.creativefabrica.com/wp-content/uploads/2023/06/19/Cute-Adorable-Little-Doctor-Kitten-With-Chibi-Dreamy-Eyes-Wearing-72527736-1.png "; /* Thêm logo mèo trước tin nhắn của bot */
#         font-size: 1.5rem;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )


# --------------------------------------------------------------------
# MOCK SUGGESTIONS
SUGGESTIONS = {
    "Đặt lịch khám bệnh": "Bạn muốn đặt lịch khám vào ngày và giờ nào?",
    "Kiểm tra lịch trống": "Bạn muốn tôi kiểm tra lịch trống trong tuần này hay tuần sau?",
    "Hủy lịch hẹn": "Bạn có thể cho tôi biết lịch nào bạn muốn hủy không?",
    "Cập nhật lịch hẹn": "Bạn muốn thay đổi thời gian hay nội dung của lịch hẹn hiện tại?",
    "Tư vấn sức khỏe": "Bạn muốn tôi tư vấn về chế độ ăn uống, giấc ngủ hay tập luyện?",
    "Theo dõi huyết áp": "Bạn có muốn ghi lại kết quả huyết áp gần nhất không?",
}


# --------------------------------------------------------------------
# SESSION STATE INIT
if "messages" not in st.session_state:
    st.session_state.messages = []
if "initial_question" not in st.session_state:
    st.session_state.initial_question = None

# --------------------------------------------------------------------
# HELPERS
async def get_multi_agent_response(user_input: str):
    """Get response from multi-agent system."""
    try:
        # Initialize system if not already done
        if st.session_state.multi_agent_system is None:
            with st.spinner("Initializing AI system..."):
                st.session_state.multi_agent_system = MultiAgentSystem()
                await st.session_state.multi_agent_system.initialize()
        
        # Process the message
        response = await st.session_state.multi_agent_system.process_message(user_input)
        return response
        
    except Exception as e:
        return f"Error processing request: {str(e)}"

def send_to_agent(user_input: str):
    """Synchronous wrapper for async multi-agent call."""
    try:
        # Run the async function in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(get_multi_agent_response(user_input))
            return response
        finally:
            loop.close()
    except Exception as e:
        return f"Error: {str(e)}"


def clear_conversation():
    st.session_state.messages = []
    st.session_state.initial_question = None
    if "initial_question_input" in st.session_state:
        del st.session_state["initial_question_input"]
    # Reset multi-agent system to start fresh conversation
    if st.session_state.multi_agent_system:
        st.session_state.multi_agent_system.state_manager.create_new_thread()

def choose_suggestion_callback(sugg: str):
    st.session_state.initial_question = sugg
    st.rerun()

# --------------------------------------------------------------------
# UI HEADER
st.html("""
<div style='text-align:center;'>
    <img src="https://www.creativefabrica.com/wp-content/uploads/2023/06/19/Cute-Adorable-Little-Doctor-Kitten-With-Chibi-Dreamy-Eyes-Wearing-72527736-1.png" 
         alt="cat logo" 
         width="80" 
         style="margin-bottom:10px; border-radius:50%;">
</div>
""")
col1, col2 = st.columns([8, 2])
with col1:
    st.title("NekAssist", anchor=False)
with col2:
    st.button("Restart", icon="🔄", on_click=clear_conversation)

# --------------------------------------------------------------------
# STATE FLAGS
user_first_interaction = st.session_state.initial_question is not None
has_message_history = len(st.session_state.messages) > 0

# --------------------------------------------------------------------
# INITIAL SCREEN
if not user_first_interaction and not has_message_history:
    with st.container():
        initial_question_value = st.chat_input("Ask a question...", key="initial_question_input")

        st.write("Examples:")
        cols = st.columns(len(SUGGESTIONS))
        for col, title in zip(cols, SUGGESTIONS.keys()):
            if col.button(title):
                choose_suggestion_callback(title)

    if initial_question_value:
        st.session_state.initial_question = initial_question_value
        st.rerun()

# --------------------------------------------------------------------
# SEND FIRST QUESTION (only once)
elif st.session_state.initial_question and not has_message_history:
    user_message = st.session_state.initial_question

    with st.chat_message("user", avatar="https://tse3.mm.bing.net/th/id/OIP.ejX7teKaUK7ZaAc4wKpvrwAAAA?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3"):
        st.markdown(user_message)

    with st.chat_message("assistant", avatar="https://www.creativefabrica.com/wp-content/uploads/2023/06/19/Cute-Adorable-Little-Doctor-Kitten-With-Chibi-Dreamy-Eyes-Wearing-72527736-1.png"):
        with st.spinner("Meowing..."):
            response = send_to_agent(user_message)
        st.markdown(response)

    st.session_state.messages.append({"role": "user", "content": user_message})
    st.session_state.messages.append({"role": "assistant", "content": response})

    #  rerun sau khi messages có, không xóa flag
    st.rerun()

# --------------------------------------------------------------------
# CHAT LOOP (đã có history)
else:   
    # render toàn bộ lịch sử
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"],avatar="https://tse3.mm.bing.net/th/id/OIP.ejX7teKaUK7ZaAc4wKpvrwAAAA?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3" if msg["role"]=="user" else "https://www.creativefabrica.com/wp-content/uploads/2023/06/19/Cute-Adorable-Little-Doctor-Kitten-With-Chibi-Dreamy-Eyes-Wearing-72527736-1.png"):
            st.markdown(msg["content"])

    # ô chat follow-up
    user_message = st.chat_input("Ask a follow-up...")

    if user_message:
        with st.chat_message("user",avatar="https://tse3.mm.bing.net/th/id/OIP.ejX7teKaUK7ZaAc4wKpvrwAAAA?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3"):
            st.markdown(user_message)

        with st.chat_message("assistant",avatar="https://www.creativefabrica.com/wp-content/uploads/2023/06/19/Cute-Adorable-Little-Doctor-Kitten-With-Chibi-Dreamy-Eyes-Wearing-72527736-1.png"):
            with st.spinner("Meowing..."):
                response = send_to_agent(user_message)
            st.markdown(response)

        st.session_state.messages.append({"role": "user", "content": user_message})
        st.session_state.messages.append({"role": "assistant", "content": response})
