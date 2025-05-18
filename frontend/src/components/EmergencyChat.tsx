import React, { useState, useEffect, type FC, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from './ui/card';

interface EmergencyChatProps {
  school: string;
  building: string;
}

interface BuildingStats {
  count: number;
}

interface TalkingPoints {
  location_info: string;
  occupancy: number;
  suggested_points: string[];
}

const EmergencyChat: FC<EmergencyChatProps> = ({ school, building }) => {
  const [message, setMessage] = useState('');
  const [location, setLocation] = useState<GeolocationCoordinates | null>(null);
  const [buildingStats, setBuildingStats] = useState<BuildingStats>({ count: 0 });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [talkingPoints, setTalkingPoints] = useState<TalkingPoints | null>(null);
  const [isLoadingTalkingPoints, setIsLoadingTalkingPoints] = useState(false);
  const [isTalkingPointsVisible, setIsTalkingPointsVisible] = useState(false);

  // For voice recording
  const [isRecording, setIsRecording] = useState(false);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  // Request location access when component mounts
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation(position.coords);
        },
        (error) => {
          console.error('Error getting location:', error);
          // User might deny location, which is fine
        }
      );
    }
  }, []);

  // Poll for current count
  useEffect(() => {
    const fetchCount = async () => {
      try {
        const response = await fetch('http://localhost:8000/current-count');
        if (response.ok) {
          const data = await response.json();
          setBuildingStats({ count: data.count });
        }
      } catch (error) {
        console.error('Error fetching count:', error);
      }
    };
    fetchCount(); // Fetch immediately
    const interval = setInterval(fetchCount, 2000); // Then fetch every 2 seconds
    return () => clearInterval(interval); // Cleanup interval on unmount
  }, []);

  const handleTextSubmit = async () => {
    if (!message.trim()) return;
    
    setIsSubmitting(true);
    setVoiceError(null);
    console.log('Submitting TEXT emergency report with data:', { school, building, message, location, timestamp: new Date().toISOString() });
    
    try {
      const response = await fetch('http://localhost:8000/submit-emergency', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          school,
          building,
          message,
          location: location ? {
            latitude: location.latitude,
            longitude: location.longitude
          } : null,
          timestamp: new Date().toISOString()
        }),
      });

      if (response.ok) {
        const responseData = await response.json();
        setBuildingStats({ count: responseData.building_count });
        setIsSubmitted(true);
      } else {
        const errorBodyText = await response.text();
        let errorData;
        try { errorData = JSON.parse(errorBodyText); } catch (e) { errorData = errorBodyText; }
        console.error('Error submitting text emergency:', response.status, errorData);
        alert(`Error submitting text report: ${response.status} - ${typeof errorData === 'string' ? errorData : JSON.stringify(errorData)}`);
      }
    } catch (error: any) {
      console.error('Network error or other issue submitting text emergency:', error);
      alert(`Network error or other issue: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const startRecording = async () => {
    setVoiceError(null);
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        let mimeType = 'audio/wav';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = 'audio/webm'; // Fallback
          if (!MediaRecorder.isTypeSupported(mimeType)) {
            setVoiceError('Neither WAV nor WebM recording is supported by your browser.');
            return;
          }
        }
        
        const recorder = new MediaRecorder(stream, { mimeType });
        mediaRecorderRef.current = recorder;
        setAudioChunks([]); // Clear previous chunks

        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            setAudioChunks((prev) => [...prev, event.data]);
          }
          // Silence detection: reset timeout if data comes in
          if (silenceTimeoutRef.current) clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = setTimeout(stopRecordingAndSend, 1500);
        };

        recorder.onstop = () => {
          // Stop all tracks on the stream to turn off mic indicator
          stream.getTracks().forEach(track => track.stop());
          if (silenceTimeoutRef.current) clearTimeout(silenceTimeoutRef.current);
          // actual sending is now handled by stopRecordingAndSend or explicitly by button
        };
        
        recorder.start(); // Start recording
        setIsRecording(true);
        // Initial silence timeout when recording starts
        if (silenceTimeoutRef.current) clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = setTimeout(stopRecordingAndSend, 1500);

      } catch (err) {
        console.error('Error accessing microphone or starting recording:', err);
        setVoiceError('Could not access microphone. Please check permissions.');
        setIsRecording(false);
      }
    } else {
      setVoiceError('Audio recording is not supported by your browser.');
    }
  };

  const stopRecordingAndSend = async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (silenceTimeoutRef.current) clearTimeout(silenceTimeoutRef.current);

    if (audioChunks.length === 0) {
      setVoiceError('No audio recorded. Please try again.');
      return; // Don't submit if no audio was captured
    }

    setIsSubmitting(true);
    setVoiceError(null);
    
    const mimeType = mediaRecorderRef.current?.mimeType || 'audio/wav';
    const fileExtension = mimeType.includes('webm') ? '.webm' : '.wav';
    const audioBlob = new Blob(audioChunks, { type: mimeType });
    const formData = new FormData();

    formData.append('school', school);
    formData.append('building', building);
    if (location) {
      formData.append('latitude', location.latitude.toString());
      formData.append('longitude', location.longitude.toString());
    }
    formData.append('file', audioBlob, `emergency_audio${fileExtension}`);

    console.log('Submitting VOICE emergency report...');

    try {
      const response = await fetch('http://localhost:8000/submit-voice-emergency', {
        method: 'POST',
        body: formData, // No 'Content-Type' header needed for FormData, browser sets it
      });

      if (response.ok) {
        const responseData = await response.json();
        setBuildingStats({ count: responseData.building_count });
        setIsSubmitted(true);
        setAudioChunks([]); // Clear chunks after successful submission
      } else {
        const errorBodyText = await response.text();
        let errorData;
        try { errorData = JSON.parse(errorBodyText); } catch (e) { errorData = errorBodyText; }
        console.error('Error submitting voice emergency:', response.status, errorData);
        setVoiceError(`Error submitting voice report: ${response.status} - ${typeof errorData === 'string' ? errorData : JSON.stringify(errorData)}`);
        // Don't set isSubmitted to true on error
      }
    } catch (error: any) {
      console.error('Network error or other issue submitting voice emergency:', error);
      setVoiceError(`Network error or other issue submitting voice report: ${error.message}`);
    } finally {
      setIsSubmitting(false);
      // Do not clear audioChunks here if submission failed and user might want to retry with same audio.
      // However, for this flow, we clear it as they'd typically re-record.
      if(!isSubmitted) setAudioChunks([]); 
    }
  };

  const handleTalkingPointsClick = async () => {
    if (!talkingPoints) {
      setIsLoadingTalkingPoints(true);
      try {
        const response = await fetch(
          `http://localhost:8000/get-talking-points?school=${encodeURIComponent(school)}&building=${encodeURIComponent(building)}`
        );
        
        if (response.ok) {
          const data = await response.json();
          setTalkingPoints(data);
          setIsTalkingPointsVisible(true);
        } else {
          console.error('Error fetching talking points:', await response.text());
        }
      } catch (error) {
        console.error('Error fetching talking points:', error);
      } finally {
        setIsLoadingTalkingPoints(false);
      }
    } else {
      setIsTalkingPointsVisible(!isTalkingPointsVisible);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-md md:max-w-2xl lg:max-w-4xl mx-auto"
    >
      <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-primary">Emergency Report</CardTitle>
          <CardDescription>
            {school} - {building}
          </CardDescription>
          <div className="flex justify-between text-sm mt-2">
            <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
              👥 People in building: {buildingStats.count}
            </div>
            {location && (
              <div className="bg-green-100 text-green-800 px-2 py-1 rounded">
                📍 Location shared
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!isSubmitted ? (
            <>
              <div className="mb-4">
                <Button
                  onClick={handleTalkingPointsClick}
                  disabled={isLoadingTalkingPoints}
                  className="w-full mb-4 bg-blue-600 hover:bg-blue-700 flex items-center justify-center gap-2"
                >
                  {isLoadingTalkingPoints ? (
                    "Loading..."
                  ) : (
                    <>
                      {talkingPoints ? (
                        <>
                          {isTalkingPointsVisible ? "Hide" : "Show"} What to Say
                          <motion.span
                            animate={{ rotate: isTalkingPointsVisible ? 180 : 0 }}
                            transition={{ duration: 0.3 }}
                            className="text-xl"
                          >
                            ▼
                          </motion.span>
                        </>
                      ) : (
                        "What Should I Say?"
                      )}
                    </>
                  )}
                </Button>

                <AnimatePresence>
                  {talkingPoints && isTalkingPointsVisible && (
                    <motion.div
                      initial={{ opacity: 0, height: 0, scale: 0.95 }}
                      animate={{ 
                        opacity: 1, 
                        height: "auto", 
                        scale: 1,
                        transition: {
                          height: { duration: 0.3 },
                          opacity: { duration: 0.2 },
                          scale: { duration: 0.2 }
                        }
                      }}
                      exit={{ 
                        opacity: 0, 
                        height: 0, 
                        scale: 0.95,
                        transition: {
                          height: { duration: 0.3 },
                          opacity: { duration: 0.2 },
                          scale: { duration: 0.2 }
                        }
                      }}
                      style={{ transformOrigin: 'top' }}
                      className="overflow-hidden"
                    >
                      <motion.div
                        initial={{ y: -20 }}
                        animate={{ y: 0 }}
                        exit={{ y: -20 }}
                        className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200"
                      >
                        <h3 className="font-semibold mb-2">Suggested Talking Points:</h3>
                        <p className="text-sm mb-2">
                          <span className="font-medium">Location:</span> {talkingPoints.location_info}
                        </p>
                        <p className="text-sm mb-2">
                          <span className="font-medium">Current Occupancy:</span> {talkingPoints.occupancy} people
                        </p>
                        <ul className="list-disc list-inside text-sm space-y-1">
                          {talkingPoints.suggested_points.map((point, index) => (
                            <motion.li
                              key={index}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: -20 }}
                              transition={{ delay: index * 0.1 }}
                              className="text-gray-700"
                            >
                              {point}
                            </motion.li>
                          ))}
                        </ul>
                      </motion.div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <p className="mb-4">
                  Please briefly describe the emergency situation. This will be sent to an AI-powered 911 operator for dispatch.
                </p>
              </div>

              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Describe the emergency situation here..."
                className="h-24 mb-4"
                disabled={isSubmitting || isRecording}
              />
              {!location && (
                <p className="mt-2 text-amber-600 text-sm mb-2">
                  ⚠️ Please allow location access for faster response.
                </p>
              )}
              {voiceError && (
                <p className="text-red-500 text-sm mb-2">Error: {voiceError}</p>
              )}
            </>
          ) : (
            <div className="py-8 text-center">
              <div className="text-green-600 text-5xl mb-4">✓</div>
              <h3 className="text-xl font-medium mb-2">Report Submitted</h3>
              <p>
                Your emergency report has been received. Help is being dispatched.
              </p>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex flex-col space-y-2">
          {!isSubmitted ? (
            <>
              <Button 
                onClick={handleTextSubmit} 
                disabled={!message.trim() || isSubmitting || isRecording}
                className="w-full bg-red-600 hover:bg-red-700"
              >
                {isSubmitting && !isRecording ? "Submitting Text..." : "Submit Text Report"}
              </Button>
              {!isRecording ? (
                <Button 
                  onClick={startRecording}
                  disabled={isSubmitting}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                >
                  Start Voice Report
                </Button>
              ) : (
                <Button 
                  onClick={stopRecordingAndSend} 
                  disabled={isSubmitting} // isSubmitting will be true if auto-stopped & sending
                  className="w-full bg-yellow-500 hover:bg-yellow-600"
                >
                  {isSubmitting ? "Sending Voice..." : "Stop & Send Voice Report"}
                </Button>
              )}
            </>
          ) : (
            <Button 
              onClick={() => {
                setIsSubmitted(false);
                setMessage(''); // Clear text message
                setAudioChunks([]); // Clear any residual audio chunks
                setVoiceError(null);
              }}
              className="w-full"
            >
              Submit Another Report
            </Button>
          )}
        </CardFooter>
      </Card>
    </motion.div>
  );
};

export default EmergencyChat; 