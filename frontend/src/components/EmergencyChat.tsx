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

interface LocationData {
  latitude: number;
  longitude: number;
}

interface VoiceChatResponse {
  transcript: string;
  response_text: string;
  audio: string; // base64 encoded audio
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
  
  // Voice chat state
  const [isRecording, setIsRecording] = useState(false);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [userTranscript, setUserTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  
  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  const lastAudioTimeRef = useRef<number>(Date.now());

  // Request location access when component mounts
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation(position.coords);
        },
        (error) => {
          console.error('Error getting location:', error);
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

    // Fetch immediately
    fetchCount();

    // Then fetch every 2 seconds
    const interval = setInterval(fetchCount, 2000);

    return () => clearInterval(interval);
  }, []);

  // Audio recording effect
  useEffect(() => {
    // Clean up function to stop recording and release media stream
    const cleanupRecording = () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      
      if (silenceTimeoutRef.current) {
        window.clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
    };

    // Start recording when isRecording becomes true
    if (isRecording) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          streamRef.current = stream;
          const mediaRecorder = new MediaRecorder(stream);
          mediaRecorderRef.current = mediaRecorder;
          
          // Reset audio chunks
          setAudioChunks([]);
          
          // Handle audio data
          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              setAudioChunks(prev => [...prev, event.data]);
              lastAudioTimeRef.current = Date.now();
              
              // Reset silence timeout on new audio
              if (silenceTimeoutRef.current) {
                window.clearTimeout(silenceTimeoutRef.current);
              }
              
              // Set new silence timeout - stop after 1.5s of silence
              silenceTimeoutRef.current = window.setTimeout(() => {
                if (isRecording) {
                  setIsRecording(false);
                }
              }, 1500);
            }
          };
          
          // Start recording
          mediaRecorder.start(100); // Collect data every 100ms
        })
        .catch(error => {
          console.error('Error accessing microphone:', error);
          setIsRecording(false);
        });
    } 
    // Handle cleanup when recording stops
    else if (audioChunks.length > 0) {
      sendAudioToBackend();
    }

    // Cleanup on unmount or when recording state changes
    return cleanupRecording;
  }, [isRecording]);

  const sendAudioToBackend = async () => {
    if (audioChunks.length === 0) return;
    
    setIsProcessingAudio(true);
    
    try {
      // Create blob from audio chunks
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      
      // Create FormData and append audio
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      formData.append('school', school);
      formData.append('building', building);
      
      if (location) {
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
      }
      
      // Send to backend
      const response = await fetch('http://localhost:8000/voice-chat', {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const data: VoiceChatResponse = await response.json();
        
        // Display transcript and response
        setUserTranscript(data.transcript);
        setAiResponse(data.response_text);
        
        // Play audio response
        if (data.audio) {
          const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
          audio.play();
        }
      } else {
        console.error('Error processing voice:', await response.text());
      }
    } catch (error) {
      console.error('Error sending audio to backend:', error);
    } finally {
      setIsProcessingAudio(false);
      setAudioChunks([]);
    }
  };

  const toggleRecording = () => {
    setIsRecording(prevState => !prevState);
  };

  const handleSubmit = async () => {
    if (!message.trim()) return;
    
    setIsSubmitting(true);
    console.log('Submitting emergency report with data:', { school, building, message, location, timestamp: new Date().toISOString() });
    
    try {
      // Send the emergency report
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

      console.log('Fetch response status:', response.status);
      if (response.ok) {
        const responseData = await response.json();
        console.log('Emergency report submitted successfully:', responseData);
        setBuildingStats({ count: responseData.building_count });
        setIsSubmitted(true);
      } else {
        const errorBodyText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorBodyText);
        } catch (e) {
          errorData = errorBodyText;
        }
        console.error('Error submitting emergency: Server responded with status', response.status, errorData);
        alert(`Error submitting report: ${response.status} - ${typeof errorData === 'string' ? errorData : JSON.stringify(errorData)}`);
      }
    } catch (error: any) {
      console.error('Network error or other issue submitting emergency:', error);
      alert(`Network error or other issue: ${error.message}`);
    } finally {
      setIsSubmitting(false);
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
      className="w-full max-w-[90%] md:max-w-6xl mx-auto"
    >
      <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20">
        <CardHeader>
          <CardTitle className="text-3xl font-bold text-primary">Emergency Report</CardTitle>
          <CardDescription>
            {school} - {building}
          </CardDescription>
          <div className="flex flex-wrap gap-2 text-sm mt-2">
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
              <div className="mb-4 md:grid md:grid-cols-2 md:gap-6">
                <div className="space-y-4">
                  <Button
                    onClick={handleTalkingPointsClick}
                    disabled={isLoadingTalkingPoints}
                    className="w-full bg-blue-600 hover:bg-blue-700 flex items-center justify-center gap-2"
                  >
                    {isLoadingTalkingPoints ? (
                      "Loading..."
                    ) : (
                      <>
                        {talkingPoints ? (
                          <>
                            {isTalkingPointsVisible ? "Hide" : "Show"} Talking Points
                            <motion.span
                              animate={{ rotate: isTalkingPointsVisible ? 180 : 0 }}
                              transition={{ duration: 0.3 }}
                              className="text-xl"
                            >
                              ▼
                            </motion.span>
                          </>
                        ) : (
                          "Tell me What to Say"
                        )}
                      </>
                    )}
                  </Button>

                  <AnimatePresence>
                    {talkingPoints && isTalkingPointsVisible && (
                      <motion.div
                        initial={{ opacity: 0, height: 0, scale: 0.95, transformOrigin: "top" }}
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

                  <p className="text-base">
                    Please briefly describe the emergency situation. This will be sent to an AI-powered 911 operator for dispatch.
                  </p>
                </div>

                <div className="space-y-4">
                  <Textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Describe the emergency situation here..."
                    className="h-full min-h-[200px]"
                    disabled={isSubmitting || isRecording || isProcessingAudio}
                  />
                  {!location && (
                    <p className="mt-2 text-amber-600 text-sm">
                      ⚠️ Please allow location access for faster response
                    </p>
                  )}
                </div>
              </div>

              {/* Voice chat UI */}
              {(userTranscript || aiResponse) && (
                <div className="mt-4 p-4 bg-background/80 rounded-lg border border-border/50 md:grid md:grid-cols-2 md:gap-4">
                  {userTranscript && (
                    <div className="mb-2 md:mb-0">
                      <p className="text-sm font-medium text-primary">You said:</p>
                      <p className="text-sm">{userTranscript}</p>
                    </div>
                  )}
                  {aiResponse && (
                    <div>
                      <p className="text-sm font-medium text-green-600">Dispatcher:</p>
                      <p className="text-sm">{aiResponse}</p>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="py-8 text-center">
              <div className="text-green-600 text-5xl mb-4">✓</div>
              <h3 className="text-xl font-medium mb-2">Report Submitted</h3>
              <p>
                Your emergency has been reported. Help is on the way.
              </p>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex flex-col md:flex-row gap-2">
          {!isSubmitted ? (
            <>
              <Button 
                onClick={handleSubmit} 
                disabled={!message.trim() || isSubmitting || isRecording || isProcessingAudio}
                className="w-full bg-red-600 hover:bg-red-700"
              >
                {isSubmitting ? "Submitting..." : "Submit Emergency Report"}
              </Button>
              
              <Button
                onClick={toggleRecording}
                disabled={isSubmitting || isProcessingAudio}
                className={`w-full ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-blue-600 hover:bg-blue-700'}`}
                type="button"
              >
                {isRecording 
                  ? "Stop Recording (auto-stops after 1.5s silence)" 
                  : isProcessingAudio 
                    ? "Processing your voice..." 
                    : "Talk to 911 Dispatcher"}
              </Button>
            </>
          ) : (
            <Button 
              onClick={() => setIsSubmitted(false)}
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