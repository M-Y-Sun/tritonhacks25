import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

function VideoFeed() {
  const [university, setUniversity] = useState('');
  const [building, setBuilding] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    return () => {
      if (isStreaming) {
        fetch('http://localhost:8000/stop_stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        }).catch(console.error);
      }
    };
  }, [isStreaming]);

  const handleStartStream = async () => {
    if (!university || !building) {
      setError('Please select both university and building');
      return;
    }

    try {
      setError('');
      
      const response = await fetch('http://localhost:8000/start_stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          university,
          building,
          message
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setIsStreaming(true);
        setError('');
      } else {
        if (response.status === 400 && data.detail === "Stream already active") {
          await handleStopStream();
          setTimeout(() => handleStartStream(), 1000);
        } else {
          setError(data.detail || 'Failed to start stream');
        }
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error(err);
    }
  };

  const handleStopStream = async () => {
    try {
      setError('');
      
      const response = await fetch('http://localhost:8000/stop_stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });
      
      if (response.ok) {
        setIsStreaming(false);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to stop stream');
      }
    } catch (err) {
      console.error(err);
      setError('Failed to stop stream');
    }
  };

  const handleMessageSubmit = async () => {
    if (!message) return;

    try {
      const response = await fetch('http://localhost:8000/update_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ message }),
      });

      if (response.ok) {
        setMessage('');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update message');
      }
    } catch (err) {
      console.error(err);
      setError('Failed to update message');
    }
  };

  return (
    <div className="container mx-auto p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-4xl mx-auto"
      >
        <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-center text-primary">
              Video Surveillance Feed
            </CardTitle>
            <CardDescription className="text-center">
              Monitor and track building occupancy
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Select value={university} onValueChange={setUniversity}>
                <SelectTrigger>
                  <SelectValue placeholder="Select University" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ucsd">UCSD</SelectItem>
                  <SelectItem value="stanford">Stanford</SelectItem>
                  <SelectItem value="cmu">CMU</SelectItem>
                </SelectContent>
              </Select>

              <Select value={building} onValueChange={setBuilding}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Building" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hdci">HDCI</SelectItem>
                  <SelectItem value="cse">CSE</SelectItem>
                  <SelectItem value="warren">Warren</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {isStreaming && (
              <div className="space-y-4">
                <div className="relative aspect-video w-full overflow-hidden rounded-lg border-2 border-primary/20">
                  <img
                    src="http://localhost:8000/video_feed"
                    alt="Live Feed"
                    className="w-full h-full object-contain"
                  />
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Enter emergency message..."
                    className="flex-1 px-3 py-2 rounded border border-gray-300"
                  />
                  <Button onClick={handleMessageSubmit}>Send Message</Button>
                </div>
              </div>
            )}

            {error && (
              <p className="text-red-500 text-center">{error}</p>
            )}
          </CardContent>
          <CardFooter className="flex justify-center">
            <Button
              onClick={isStreaming ? handleStopStream : handleStartStream}
              className="w-full max-w-xs"
            >
              {isStreaming ? 'Stop Stream' : 'Start Stream'}
            </Button>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}

export default VideoFeed; 