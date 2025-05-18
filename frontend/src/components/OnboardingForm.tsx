import React, { useState, type FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/button';
import { Link } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from './ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

type OnboardingStep = 'welcome' | 'school' | 'building' | 'complete';

interface FormData {
  school: string;
  building: string;
}

interface OnboardingFormProps {
  onComplete: (data: FormData) => void;
}

const OnboardingForm: FC<OnboardingFormProps> = ({ onComplete }) => {
  const [step, setStep] = useState<OnboardingStep>('welcome');
  const [school, setSchool] = useState('');
  const [building, setBuilding] = useState('');
  
  const handleContinue = () => {
    if (step === 'welcome') {
      setStep('school');
    } else if (step === 'school' && school) {
      setStep('building');
    } else if (step === 'building' && building) {
      setStep('complete');
      onComplete({ school, building });
    }
  };

  const slideVariants = {
    enter: {
      x: '100%',
      opacity: 0,
    },
    center: {
      x: 0,
      opacity: 1,
    },
    exit: {
      x: '-100%',
      opacity: 0,
    },
  };

  return (
    <AnimatePresence mode="wait">
      {step === 'welcome' && (
        <motion.div
          key="welcome"
          initial="enter"
          animate="center"
          exit="exit"
          variants={slideVariants}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="w-full max-w-md mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="text-3xl font-bold text-center text-primary">Welcome</CardTitle>
              <CardDescription className="text-center">
                Campus Emergency Response System
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              <p className="text-center mb-4">
                This system will help you quickly report emergencies on campus. 
                Our AI-powered system will dispatch the appropriate response team.
              </p>
              <div className="h-32 w-32 rounded-full bg-primary/30 flex items-center justify-center mb-4">
                <span className="text-5xl">🚨</span>
              </div>
            </CardContent>
            <CardFooter className="flex justify-center">
              <Button onClick={handleContinue} className="w-full">Continue</Button>
            </CardFooter>
          </Card>
          
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-4 text-center"
          >
            <Link to="/video-feed" className="block">
              <Button
                variant="outline"
                className="w-full"
              >
                Go to Video Surveillance Feed
              </Button>
            </Link>
          </motion.div>
        </motion.div>
      )}

      {step === 'school' && (
        <motion.div
          key="school"
          initial="enter"
          animate="center"
          exit="exit"
          variants={slideVariants}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="w-full max-w-md mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-primary">Select Your School</CardTitle>
              <CardDescription>
                Please select your school from the list below
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Select value={school} onValueChange={setSchool}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a school" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ucsd">UCSD</SelectItem>
                  <SelectItem value="stanford">Stanford</SelectItem>
                  <SelectItem value="cmu">CMU</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
            <CardFooter>
              <Button 
                onClick={handleContinue} 
                className="w-full"
                disabled={!school}
              >
                Continue
              </Button>
            </CardFooter>
          </Card>
        </motion.div>
      )}

      {step === 'building' && (
        <motion.div
          key="building"
          initial="enter"
          animate="center"
          exit="exit"
          variants={slideVariants}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="w-full max-w-md mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-primary">Select Building</CardTitle>
              <CardDescription>
                Please select the building you are in
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Select value={building} onValueChange={setBuilding}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a building" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hdci">HDCI</SelectItem>
                  <SelectItem value="cse">CSE</SelectItem>
                  <SelectItem value="warren">Warren</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
            <CardFooter>
              <Button 
                onClick={handleContinue} 
                className="w-full"
                disabled={!building}
              >
                Done
              </Button>
            </CardFooter>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default OnboardingForm; 