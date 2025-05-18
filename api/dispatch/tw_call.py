# Download the helper library from https://www.twilio.com/docs/python/install
import os

from twilio.rest import Client

from logger import logger

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)


def call(text: str, caller="+15413488156", reciever="+18586884297"):
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

    logger.info("SID: " + (call.sid or "None"))
