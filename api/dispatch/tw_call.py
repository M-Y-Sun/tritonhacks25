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

def call_with_audio_message(audio_url: str, location_text: str | None, building_info_text: str, caller="+15413488156", reciever="+18586884297"):
    """
    Initiates a Twilio call that first plays an audio file from a URL,
    then says location information (if provided), and finally says building information.
    """
    twiml_parts = ["<Response>"]
    twiml_parts.append(f"<Play>{audio_url}</Play>")
    
    if location_text:
        twiml_parts.append(f"<Say>User location details: {location_text}</Say>")
    else:
        twiml_parts.append("<Say>User location was not provided.</Say>")
        
    twiml_parts.append(f"<Say>{building_info_text}</Say>")
    twiml_parts.append("</Response>")
    
    twiml_str = "".join(twiml_parts)

    logger.info(f"Initiating call with TwiML: {twiml_str}")

    try:
        call_instance = client.calls.create(
            twiml=twiml_str,
            from_=caller,
            to=reciever,
        )
        logger.info(f"Call initiated with audio message. SID: {call_instance.sid or 'None'}")
        return call_instance.sid
    except Exception as e:
        logger.error(f"Error initiating Twilio call with audio message: {e}")
        raise
