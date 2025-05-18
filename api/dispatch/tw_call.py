# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from logger import logger

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

def call(text: str, caller="+15413488156", reciever="+18586884297"):
    """Makes a Twilio call that speaks the provided text."""
    response = VoiceResponse()
    response.say(text)
    
    twiml_str = str(response)
    logger.info(f"Making text-only call with TwiML: {twiml_str}")

    call = client.calls.create(
        twiml=twiml_str,
        to=reciever,
        from_=caller
    )
    
    logger.info("SID: " + (call.sid or "None"))
    return call.sid

def call_with_audio_message(audio_url: str, location_text: str | None, building_info_text: str, caller="+15413488156", reciever="+18586884297"):
    """
    Initiates a Twilio call that:
    1. Announces the emergency
    2. Plays the audio message
    3. Says the location (if available)
    4. Says the building information
    """
    response = VoiceResponse()
    
    # Initial announcement
    response.say("Emergency message received.")
    
    # Play the audio message
    response.play(audio_url)
    
    # Add a brief pause
    response.pause(length=1)
    
    # Say location if available
    if location_text:
        response.say(location_text)
        response.pause(length=1)
    
    # Say building information
    response.say(building_info_text)
    
    twiml_str = str(response)
    print(f"Making audio call with TwiML: {twiml_str}")
    
    call = client.calls.create(
        twiml=twiml_str,
        to=reciever,
        from_=caller
    )
    
    logger.info("SID: " + (call.sid or "None"))
    return call.sid
