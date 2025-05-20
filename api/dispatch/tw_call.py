# Download the helper library from https://www.twilio.com/docs/python/install
import os

from twilio.rest import Client

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)


def call(text: str, caller: str, reciever: str):
    twiml_str = rf"""
    <Response>
      <Say>{text}</Say>
    </Response>
    """

    call = client.calls.create(
        twiml=twiml_str,
        from_=caller,
        to=reciever,
    )

    print("SID: " + (call.sid or "None"))
