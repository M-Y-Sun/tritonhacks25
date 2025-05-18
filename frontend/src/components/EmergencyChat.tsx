import React, { useState, useEffect, type FC } from 'react';
import { motion } from 'framer-motion';
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

const EmergencyChat: FC<EmergencyChatProps> = ({ school, building }) => {
  const [message, setMessage] = useState('');
  const [location, setLocation] = useState<GeolocationCoordinates | null>(null);
  const [buildingStats, setBuildingStats] = useState<BuildingStats>({ count: 0 });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

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

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-md mx-auto"
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
              <p className="mb-4">
                Please briefly describe the emergency situation. This will be sent to an AI-powered 911 operator for dispatch.
              </p>
              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Describe the emergency situation here..."
                className="h-32"
                disabled={isSubmitting}
              />
              {!location && (
                <p className="mt-2 text-amber-600 text-sm">
                  ⚠️ Please allow location access for faster response
                </p>
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
        <CardFooter>
          {!isSubmitted ? (
            <Button 
              onClick={handleSubmit} 
              disabled={!message.trim() || isSubmitting}
              className="w-full bg-red-600 hover:bg-red-700"
            >
              {isSubmitting ? "Submitting..." : "Submit Emergency Report"}
            </Button>
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