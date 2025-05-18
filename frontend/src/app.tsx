import React, { useState, type FC } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import OnboardingForm from './components/OnboardingForm';
import EmergencyChat from './components/EmergencyChat';
import VideoFeed from './pages/VideoFeed';
import './globals.css';

interface FormData {
  school: string;
  building: string;
}

const AppContent: FC<{ formData: FormData | null; onComplete: (data: FormData) => void }> = ({ formData, onComplete }) => {
  const location = useLocation();
  const isVideoFeed = location.pathname === '/video-feed';
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 via-background to-secondary/5 flex items-center justify-center p-4">
      <div className={`w-full ${!formData ? 'max-w-6xl' : 'max-w-[150rem]'}`}>
        <Routes>
          <Route 
            path="/" 
            element={
              !formData ? (
                <OnboardingForm onComplete={onComplete} />
              ) : (
                <EmergencyChat school={formData.school} building={formData.building} />
              )
            } 
          />
          <Route path="/video-feed" element={<VideoFeed />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
};

const App: FC = () => {
  const [formData, setFormData] = useState<FormData | null>(null);

  const handleFormComplete = (data: FormData) => {
    setFormData(data);
  };

  return (
    <Router>
      <AppContent formData={formData} onComplete={handleFormComplete} />
    </Router>
  );
}

export default App;
