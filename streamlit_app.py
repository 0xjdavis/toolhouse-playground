import streamlit as st
from openai import OpenAI
import requests
import json
from datetime import datetime, timezone

# Function to send an email using Mailgun API
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

# Streamlit UI setup
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-4o model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Collecting API keys and domain from user
openai_api_key = st.text_input("OpenAI API Key", type="password")
mailgun_api_key = st.text_input("Mailgun API Key", type="password")
mailgun_domain = st.text_input("Mailgun Domain", placeholder="your_domain.com")

# Check if the API keys and domain are provided
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
                        "api_key": {"type": "string", "description": "Mailgun API key"},
                        "domain": {"type": "string", "description": "Mailgun domain"},
                        "sender": {"type": "string", "description": "Sender email address"},
                        "recipient": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Subject of the email"},
                        "body": {"type": "string", "description": "Body of the email"}
                    },
                    "required": ["api_key", "domain", "sender", "recipient", "subject", "body"]
                }
            },
            {
                "name": "current_time",
                "description": "Gets the current UTC time in ISO format.",
                "parameters": {}
            },
        ]

        msgs = [
            {"role": "system", "content": "You are a helpful assistant that can chat with a user and send emails."},
            {"role": "assistant", "content": "My sender email address is 'hello@sorcery.ai'."},
        ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=msgs,
            stream=False,
            tools=functions,
            tool_choice="auto",
        )

        if stream.choices[0].message.tool_calls is not None:
            function_call = stream.choices[0].message.tool_calls[0]
            function_call_name = function_call.function.name

            if function_call_name == "send_email":
                arguments = json.loads(function_call.function.arguments)
                result = send_email(
                    api_key=mailgun_api_key,
                    domain=mailgun_domain,
                    sender=arguments['sender'],
                    recipient=arguments['recipient'],
                    subject=arguments['subject'],
                    body=arguments['body']
                )
                msgs.append({
                    "role": "assistant", 
                    "tool_call_id": function_call.id, 
                    "name": function_call_name, 
                    "content": f"Email sent to {arguments['recipient']}. Result: {result}"
                })

            elif function_call_name == "current_time":
                utc_time = datetime.now(timezone.utc).isoformat()
                msgs.append({
                    "role": "assistant", 
                    "tool_call_id": function_call.id, 
                    "name": function_call_name, 
                    "content": utc_time
                })

            model_response_with_function_call = client.chat.completions.create(
                model="gpt-4o",
                messages=msgs,
            )
            st.session_state.messages.append({"role": "assistant", "content": model_response_with_function_call.choices[0].message.content})
            with st.chat_message("assistant"):
                st.markdown(model_response_with_function_call.choices[0].message.content)
                
        else:
            with st.chat_message("assistant"):
                st.markdown(stream.choices[0].message.content)
                st.session_state.messages.append({"role": "assistant", "content": stream.choices[0].message.content})
