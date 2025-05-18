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
  const [direction, setDirection] = useState(1); // 1 for forward, -1 for backward
  
  const handleBack = () => {
    setDirection(-1);
    if (step === 'building') {
      setStep('school');
      setBuilding('');
    } else if (step === 'school') {
      setStep('welcome');
      setSchool('');
    }
  };

  const handleForward = (nextStep: OnboardingStep) => {
    setDirection(1);
    setStep(nextStep);
  };

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? '100%' : '-100%',
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction > 0 ? '-100%' : '100%',
      opacity: 0,
    }),
  };

  const buttonVariants = {
    hover: {
      scale: 1.02,
      transition: {
        duration: 0.2,
        ease: 'easeInOut',
      },
    },
    tap: {
      scale: 0.98,
      transition: {
        duration: 0.1,
      },
    },
    initial: {
      scale: 1,
    },
  };

  return (
    <AnimatePresence mode="wait" custom={direction}>
      {step === 'welcome' && (
        <motion.div
          key="welcome"
          custom={direction}
          initial="enter"
          animate="center"
          exit="exit"
          variants={slideVariants}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="w-full max-w-lg mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20 p-4">
            <CardHeader>
              <CardTitle className="text-4xl font-bold text-center text-primary">Welcome</CardTitle>
              <CardDescription className="text-center text-lg mt-2">
                Campus Emergency Response System
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center py-4">
              <p className="text-center mb-4 text-base max-w-md">
                This system will help you quickly report emergencies on campus. 
                Our AI-powered system will dispatch the appropriate response team.
              </p>
              <div className="h-32 w-32 rounded-full bg-primary/30 flex items-center justify-center mb-4">
                <span className="text-6xl">🚨</span>
              </div>
            </CardContent>
            <CardFooter className="flex justify-center">
              <motion.div
                className="w-full"
                variants={buttonVariants}
                initial="initial"
                whileHover="hover"
                whileTap="tap"
              >
                <Button 
                  onClick={() => handleForward('school')} 
                  className="w-full text-base py-4 transition-colors hover:bg-purple-600"
                >
                  Get Started
                </Button>
              </motion.div>
            </CardFooter>
          </Card>
          
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-4 text-center"
          >
            <Link to="/video-feed" className="block">
              <motion.div
                variants={buttonVariants}
                initial="initial"
                whileHover="hover"
                whileTap="tap"
              >
                <Button
                  variant="outline"
                  className="w-full text-base py-4 transition-colors hover:bg-purple-600 hover:text-white"
                >
                  Go to Video Surveillance Feed
                </Button>
              </motion.div>
            </Link>
          </motion.div>
        </motion.div>
      )}

      {step === 'school' && (
        <motion.div
          key="school"
          custom={direction}
          initial="enter"
          animate="center"
          exit="exit"
          variants={slideVariants}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="w-full max-w-lg mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20 p-4">
            <CardHeader>
              <CardTitle className="text-3xl font-bold text-primary">Select Your School</CardTitle>
              <CardDescription className="text-lg mt-2">
                Please select your school from the options below
              </CardDescription>
            </CardHeader>
            <CardContent className="py-4 space-y-3">
              {['ucsd', 'stanford', 'cmu'].map((schoolOption) => (
                <motion.div
                  key={schoolOption}
                  variants={buttonVariants}
                  initial="initial"
                  whileHover="hover"
                  whileTap="tap"
                >
                  <Button 
                    variant={school === schoolOption ? 'default' : 'outline'}
                    className={`w-full text-base py-4 transition-colors ${
                      school === schoolOption ? '' : 'hover:bg-purple-600 hover:text-white'
                    }`}
                    onClick={() => {
                      setSchool(schoolOption);
                      handleForward('building');
                    }}
                  >
                    {schoolOption.toUpperCase()}
                  </Button>
                </motion.div>
              ))}
            </CardContent>
            <CardFooter className="flex justify-start">
              <motion.div
                variants={buttonVariants}
                initial="initial"
                whileHover="hover"
                whileTap="tap"
              >
                <Button 
                  variant="ghost" 
                  onClick={handleBack}
                  className="text-sm transition-colors hover:bg-purple-600 hover:text-white"
                >
                  ← Back
                </Button>
              </motion.div>
            </CardFooter>
          </Card>
        </motion.div>
      )}

      {step === 'building' && (
        <motion.div
          key="building"
          custom={direction}
          initial="enter"
          animate="center"
          exit="exit"
          variants={slideVariants}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="w-full max-w-lg mx-auto"
        >
          <Card className="bg-gradient-to-br from-primary/10 to-secondary/20 border-2 border-primary/20 p-4">
            <CardHeader>
              <CardTitle className="text-3xl font-bold text-primary">Select Building</CardTitle>
              <CardDescription className="text-lg mt-2">
                Please select the building you are in
              </CardDescription>
            </CardHeader>
            <CardContent className="py-4 space-y-3">
              {[
                { id: 'hdci', label: 'HDCI' },
                { id: 'cse', label: 'CSE' },
                { id: 'warren', label: 'Warren' }
              ].map((buildingOption) => (
                <motion.div
                  key={buildingOption.id}
                  variants={buttonVariants}
                  initial="initial"
                  whileHover="hover"
                  whileTap="tap"
                >
                  <Button 
                    variant={building === buildingOption.id ? 'default' : 'outline'}
                    className={`w-full text-base py-4 transition-colors ${
                      building === buildingOption.id ? '' : 'hover:bg-purple-600 hover:text-white'
                    }`}
                    onClick={() => {
                      setBuilding(buildingOption.id);
                      onComplete({ school, building: buildingOption.id });
                    }}
                  >
                    {buildingOption.label}
                  </Button>
                </motion.div>
              ))}
            </CardContent>
            <CardFooter className="flex justify-start">
              <motion.div
                variants={buttonVariants}
                initial="initial"
                whileHover="hover"
                whileTap="tap"
              >
                <Button 
                  variant="ghost" 
                  onClick={handleBack}
                  className="text-sm transition-colors hover:bg-purple-600 hover:text-white"
                >
                  ← Back
                </Button>
              </motion.div>
            </CardFooter>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default OnboardingForm; 