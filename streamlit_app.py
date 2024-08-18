import streamlit as st
import requests
import json
import openai
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
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys)."
)

# Get API keys and domain from user input
openai_api_key = st.text_input("OpenAI API Key", type="password")
mailgun_api_key = st.text_input("Mailgun API Key", type="password")
mailgun_domain = st.text_input("Mailgun Domain")

if not openai_api_key or not mailgun_api_key or not mailgun_domain:
    st.info("Please add your API key(s)/info to continue.", icon="🗝️")
else:
    openai.api_key = openai_api_key

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
                        "api_key": {"type": "string", "description": "Mailgun API key"},
                        "domain": {"type": "string", "description": "Mailgun domain"},
                        "sender": {"type": "string", "description": "Sender email address"},
                        "recipient": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Subject of the email"},
                        "body": {"type": "string", "description": "Body of the email"}
                    },
                    "required": ["api_key", "domain", "sender", "recipient", "subject", "body"]
                },
                "type": "function"
            },
            {
                "name": "current_time",
                "description": "Gets the current UTC time in ISO format.",
                "parameters": {},
                "type": "function"
            },
        ]

        msgs = [
            {"role": "system", "content": "You are a helpful assistant that can chat with a user and send emails."},
        ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=msgs,
            functions=functions,
            function_call="auto",
        )

        assistant_message = response['choices'][0]['message']

        if 'function_call' in assistant_message:
            function_call_name = assistant_message["function_call"]["name"]
            arguments = json.loads(assistant_message["function_call"]["arguments"])

            if function_call_name == "send_email":
                result = send_email(
                    api_key=mailgun_api_key,
                    domain=mailgun_domain,
                    sender=arguments['sender'],
                    recipient=arguments['recipient'],
                    subject=arguments['subject'],
                    body=arguments['body']
                )
                st.session_state.messages.append({"role": "assistant", "content": result})
            elif function_call_name == "current_time":
                utc_time = datetime.now(timezone.utc).isoformat()
                st.session_state.messages.append({"role": "assistant", "content": utc_time})
        else:
            response_text = assistant_message.get("content", "No response received.")
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        with st.chat_message("assistant"):
            st.markdown(st.session_state.messages[-1]["content"])
