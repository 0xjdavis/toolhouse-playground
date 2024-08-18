def send_email(api_key, domain, sender, recipient, subject, body):
    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ("api", api_key)
    data = {
        "from": sender,
        "to": recipient,
        "subject": subject,
        "text": body,
    }

    # Debugging output
    st.write(f"URL: {url}")
    st.write(f"Auth: {auth}")
    st.write(f"Data: {data}")

    response = requests.post(url, auth=auth, data=data)

    if response.status_code == 200:
        return "Email sent successfully!"
    else:
        return f"Failed to send email: {response.status_code}, {response.text}"
