import streamlit as st
from openai import OpenAI
import requests
import json
from datetime import datetime, timezone

def send_email(api_key, domain, sender, recipient, subject, body):
    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ("api", api_key)
    data = {
        "from": sender,
        "to": recipient,
        "subject": subject,
        "text": body,
    }
    
    response = requests.post(url, auth=auth, data=data)
    
    if response.status_code == 200:
        return "Email sent successfully!"
    else:
        return f"Failed to send email: {response.status_code}, {response.text}"

def get_current_time():
    return datetime.now(timezone.utc).isoformat()

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_user_input(client, prompt, mailgun_api_key, mailgun_domain):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    functions = [
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email using the Mailgun API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sender": {"type": "string", "description": "Sender email address"},
                        "recipient": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Subject of the email"},
                        "body": {"type": "string", "description": "Body of the email"}
                    },
                    "required": ["sender", "recipient", "subject", "body"]
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "current_time",
                "description": "Gets the current UTC time in ISO format.",
                "parameters": {}
            },
        },
    ]
    
    msgs = [
        {"role": "system", "content": "You are a helpful assistant that can chat with a user and send emails."},
        {"role": "assistant", "content": "My sender email address is 'hello@sorcery.ai'."},
    ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=msgs,
        stream=False,
        tools=functions,
        tool_choice="auto",
    )
    
    handle_model_response(client, stream, mailgun_api_key, mailgun_domain, msgs)

def handle_model_response(client, stream, mailgun_api_key, mailgun_domain, msgs):
    if stream.choices[0].message.tool_calls:
        tool_call = stream.choices[0].message.tool_calls[0]
        function_call_name = tool_call.function.name
        tool_call_id = tool_call.id
        
        if function_call_name == "send_email":
            arguments = json.loads(tool_call.function.arguments)
            result = send_email(
                api_key=mailgun_api_key,
                domain=mailgun_domain,
                sender=arguments['sender'],
                recipient=arguments['recipient'],
                subject=arguments['subject'],
                body=arguments['body']
            )
            msgs.append({
                "role": "function",
                "content": f"Email sent: {result}",
                "name": "send_email"
            })
        
        elif function_call_name == "current_time":
            utc_time = get_current_time()
            msgs.append({
                "role": "function",
                "content": utc_time,
                "name": "current_time"
            })
        
        model_response = client.chat.completions.create(
            model="gpt-4",
            messages=msgs,
        )
        
        response_content = model_response.choices[0].message.content
    else:
        response_content = stream.choices[0].message.content
    
    if response_content:
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        with st.chat_message("assistant"):
            st.write(response_content)

def main():

    
    # Setting page layout
    st.set_page_config(
        page_title="Figma basics",
        page_icon="✨",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar for API Key and User Info
    st.sidebar.header("About App")
    st.sidebar.markdown('This is an app that retreives data from files using the Figma API created by <a href="https://ai.jdavis.xyz" target="_blank">0xjdavis</a>.', unsafe_allow_html=True)
    
    # Calendly
    st.sidebar.markdown("""
        <hr />
        <center>
        <div style="border-radius:8px;padding:8px;background:#fff";width:100%;">
        <img src="https://avatars.githubusercontent.com/u/98430977" alt="Oxjdavis" height="100" width="100" border="0" style="border-radius:50%"/>
        <br />
        <span style="height:12px;width:12px;background-color:#77e0b5;border-radius:50%;display:inline-block;"></span> <b>I'm available for new projects!</b><br />
        <a href="https://calendly.com/0xjdavis" target="_blank"><button style="background:#126ff3;color:#fff;border: 1px #126ff3 solid;border-radius:8px;padding:8px 16px;margin:10px 0">Schedule a call</button></a><br />
        </div>
        </center>
        <br />
    """, unsafe_allow_html=True)
    
    # Copyright
    st.sidebar.caption("©️ Copyright 2024 J. Davis")

    st.title("AI Chatbot with Email Tools")
    st.write(
        "This chatbot uses OpenAI's GPT-4 model for natural language processing and Mailgun to send emails."
        "You need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
        
    )

    openai_api_key = st.text_input("OpenAI API Key", type="password")
    mailgun_api_key = st.text_input("Mailgun API Key", type="password")
    mailgun_domain = st.text_input("Mailgun Domain", type="default")

    if not openai_api_key or not mailgun_api_key or not mailgun_domain:
        st.info("Please add your API key(s)/info to continue.", icon="🗝️")
    else:
        client = OpenAI(api_key=openai_api_key)
        
        initialize_session_state()
        display_chat_history()
        
        if prompt := st.chat_input("What's up?"):
            handle_user_input(client, prompt, mailgun_api_key, mailgun_domain)

if __name__ == "__main__":
    main()
