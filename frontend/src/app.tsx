import React, { useState, type FC } from 'react';
import OnboardingForm from './components/OnboardingForm';
import EmergencyChat from './components/EmergencyChat';
import './globals.css';

interface FormData {
  school: string;
  building: string;
}

const App: FC = () => {
  const [formData, setFormData] = useState<FormData | null>(null);

  const handleFormComplete = (data: FormData) => {
    setFormData(data);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 via-background to-secondary/5 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {!formData ? (
          <OnboardingForm onComplete={handleFormComplete} />
        ) : (
          <EmergencyChat school={formData.school} building={formData.building} />
        )}
      </div>
    </div>
  );
}

export default App;
