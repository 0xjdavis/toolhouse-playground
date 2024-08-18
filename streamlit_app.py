import streamlit as st
from openai import OpenAI
import requests
import json
import os
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

st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-4 model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

openai_api_key = st.text_input("OpenAI API Key", type="password")
mailgun_api_key = st.text_input("Mailgun API Key", type="password")
mailgun_domain = st.text_input("Mailgun Domain", type="default")

if not openai_api_key or not mailgun_api_key or not mailgun_domain:
    st.info("Please add your API key(s)/info to continue.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        functions = [
            {
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
            {
                "name": "current_time",
                "description": "Gets the current UTC time in ISO format.",
                "parameters": {}
            },
        ]
        
        msgs = [
            {"role": "system", "content": "You are a helpful assistant that can chat with a user and send emails. Your sender email address is 'hello@sorcery.ai'."},
        ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=msgs,
            tools=functions,
            tool_choice="auto",
        )
        
        assistant_message = response.choices[0].message
        
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "send_email":
                    result = send_email(
                        api_key=mailgun_api_key,
                        domain=mailgun_domain,
                        sender=function_args['sender'],
                        recipient=function_args['recipient'],
                        subject=function_args['subject'],
                        body=function_args['body']
                    )
                    msgs.append({
                        "role": "function",
                        "name": "send_email",
                        "content": f"Email sent: {result}"
                    })
                elif function_name == "current_time":
                    utc_time = datetime.now(timezone.utc).isoformat()
                    msgs.append({
                        "role": "function",
                        "name": "current_time",
                        "content": utc_time
                    })
            
            second_response = client.chat.completions.create(
                model="gpt-4",
                messages=msgs,
            )
            assistant_message = second_response.choices[0].message
        
        st.session_state.messages.append({"role": "assistant", "content": assistant_message.content})
        with st.chat_message("assistant"):
            st.markdown(assistant_message.content)
