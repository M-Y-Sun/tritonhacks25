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
          className="w-full max-w-2xl mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20 p-8">
            <CardHeader>
              <CardTitle className="text-5xl font-bold text-center text-primary">Welcome</CardTitle>
              <CardDescription className="text-center text-xl mt-4">
                Campus Emergency Response System
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center py-8">
              <p className="text-center mb-8 text-lg max-w-xl">
                This system will help you quickly report emergencies on campus. 
                Our AI-powered system will dispatch the appropriate response team.
              </p>
              <div className="h-64 w-64 rounded-full bg-primary/30 flex items-center justify-center mb-8">
                <span className="text-8xl">🚨</span>
              </div>
            </CardContent>
            <CardFooter className="flex justify-center">
              <Button onClick={handleContinue} className="w-full text-lg py-6">Continue</Button>
            </CardFooter>
          </Card>
          
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-8 text-center"
          >
            <Link to="/video-feed" className="block">
              <Button
                variant="outline"
                className="w-full text-lg py-6"
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
          className="w-full max-w-2xl mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20 p-8">
            <CardHeader>
              <CardTitle className="text-4xl font-bold text-primary">Select Your School</CardTitle>
              <CardDescription className="text-xl mt-4">
                Please select your school from the options below
              </CardDescription>
            </CardHeader>
            <CardContent className="py-8 space-y-4">
              <Button 
                variant={school === 'ucsd' ? 'default' : 'outline'}
                className="w-full text-lg py-6"
                onClick={() => {
                  setSchool('ucsd');
                  handleContinue();
                }}
              >
                UCSD
              </Button>
              <Button 
                variant={school === 'stanford' ? 'default' : 'outline'}
                className="w-full text-lg py-6"
                onClick={() => {
                  setSchool('stanford');
                  handleContinue();
                }}
              >
                Stanford
              </Button>
              <Button 
                variant={school === 'cmu' ? 'default' : 'outline'}
                className="w-full text-lg py-6"
                onClick={() => {
                  setSchool('cmu');
                  handleContinue();
                }}
              >
                CMU
              </Button>
            </CardContent>
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
          className="w-full max-w-2xl mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20 p-8">
            <CardHeader>
              <CardTitle className="text-4xl font-bold text-primary">Select Building</CardTitle>
              <CardDescription className="text-xl mt-4">
                Please select the building you are in
              </CardDescription>
            </CardHeader>
            <CardContent className="py-8 space-y-4">
              <Button 
                variant={building === 'hdci' ? 'default' : 'outline'}
                className="w-full text-lg py-6"
                onClick={() => {
                  setBuilding('hdci');
                  handleContinue();
                }}
              >
                HDCI
              </Button>
              <Button 
                variant={building === 'cse' ? 'default' : 'outline'}
                className="w-full text-lg py-6"
                onClick={() => {
                  setBuilding('cse');
                  handleContinue();
                }}
              >
                CSE
              </Button>
              <Button 
                variant={building === 'warren' ? 'default' : 'outline'}
                className="w-full text-lg py-6"
                onClick={() => {
                  setBuilding('warren');
                  handleContinue();
                }}
              >
                Warren
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default OnboardingForm; 