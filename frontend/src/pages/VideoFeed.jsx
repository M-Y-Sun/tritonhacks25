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

function VideoFeed() {
  const [university, setUniversity] = useState('');
  const [building, setBuilding] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState('');
  const [streamKey, setStreamKey] = useState(0);

  useEffect(() => {
    return () => {
      if (isStreaming) {
        fetch('/stop_stream', {
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
      
      if (isStreaming) {
        await handleStopStream();
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      const response = await fetch('/start_stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          university,
          building
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setStreamKey(prev => prev + 1);
        setIsStreaming(true);
        setError('');
      } else {
        setError(data.detail || 'Failed to start stream');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error(err);
    }
  };

  const handleStopStream = async () => {
    try {
      setError('');
      
      const response = await fetch('/stop_stream', {
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
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h3 className="text-lg font-medium">Select University</h3>
                <div className="space-y-2">
                  <Button 
                    variant={university === 'ucsd' ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() => setUniversity('ucsd')}
                  >
                    UCSD
                  </Button>
                  <Button 
                    variant={university === 'stanford' ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() => setUniversity('stanford')}
                  >
                    Stanford
                  </Button>
                  <Button 
                    variant={university === 'cmu' ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() => setUniversity('cmu')}
                  >
                    CMU
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="text-lg font-medium">Select Building</h3>
                <div className="space-y-2">
                  <Button 
                    variant={building === 'hdci' ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() => setBuilding('hdci')}
                  >
                    HDCI
                  </Button>
                  <Button 
                    variant={building === 'cse' ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() => setBuilding('cse')}
                  >
                    CSE
                  </Button>
                  <Button 
                    variant={building === 'warren' ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() => setBuilding('warren')}
                  >
                    Warren
                  </Button>
                </div>
              </div>
            </div>

            {isStreaming && (
              <div className="relative aspect-video w-full overflow-hidden rounded-lg border-2 border-primary/20">
                <img
                  key={streamKey}
                  src={`/video_feed?t=${streamKey}`}
                  alt="Live Feed"
                  className="w-full h-full object-contain"
                />
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
              disabled={!university || !building}
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