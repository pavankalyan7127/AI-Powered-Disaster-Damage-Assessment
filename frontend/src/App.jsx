import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navbar from './components/Navbar';
import LandingPage from './components/LandingPage';
import { LoginModal, SignupModal } from './components/AuthModals';
import InputSelector from './components/InputSelector';
import ProcessingScreen from './components/ProcessingScreen';
import ResultsPage from './components/ResultsPage';
import AssessmentHistory from './components/AssessmentHistory';
import AdminDashboard from './components/AdminDashboard';
import { API_BASE_URL } from './config';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('geo_damage_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [currentView, setCurrentView] = useState('home'); // 'home', 'results', 'history', 'admin'
  const [activeAssessment, setActiveAssessment] = useState(null);

  // Modals
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isSignupOpen, setIsSignupOpen] = useState(false);

  // Processing state
  const [processing, setProcessing] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const steps = [
    'Uploading disaster imagery...',
    'Validating raster CRS & geospatial metadata...',
    'Extracting building footprints...',
    'Generating 128x128 PRE/POST building crop pairs...',
    'Running Siamese ResNet-50 AI inference...',
    'Calculating damage statistics...',
    'Saving assessment results...'
  ];

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem('geo_damage_user', JSON.stringify(currentUser));
      if (currentUser.role === 'admin') {
        setCurrentView('admin');
      }
    } else {
      localStorage.removeItem('geo_damage_user');
    }
  }, [currentUser]);

  const handleAuthSuccess = (user) => {
    setCurrentUser(user);
    if (user.role === 'admin') {
      setCurrentView('admin');
    } else {
      setCurrentView('home');
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setCurrentView('home');
  };

  // Run Satellite Assessment
  const handleStartSatellite = async ({ pre_file, post_file, geojson_file }) => {
    if (!currentUser) return;
    setProcessing(true);
    setStepIndex(0);

    const formData = new FormData();
    formData.append('user_id', currentUser.id);
    formData.append('pre_file', pre_file);
    formData.append('post_file', post_file);
    formData.append('geojson_file', geojson_file);

    try {
      // Simulate visual progress increments
      const interval = setInterval(() => {
        setStepIndex((prev) => (prev < steps.length - 2 ? prev + 1 : prev));
      }, 800);

      const res = await axios.post(`${API_BASE_URL}/api/assessment/satellite`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      clearInterval(interval);
      setStepIndex(steps.length - 1);

      setTimeout(() => {
        setActiveAssessment(res.data);
        setProcessing(false);
        setCurrentView('results');
      }, 500);

    } catch (err) {
      alert(err.response?.data?.detail || 'Satellite assessment failed.');
      setProcessing(false);
    }
  };

  // Run Building Assessment
  const handleStartBuilding = async ({ pre_image, post_image }) => {
    if (!currentUser) return;
    setProcessing(true);
    setStepIndex(3);

    const formData = new FormData();
    formData.append('user_id', currentUser.id);
    formData.append('pre_image', pre_image);
    formData.append('post_image', post_image);

    try {
      const res = await axios.post(`${API_BASE_URL}/api/assessment/building`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setStepIndex(steps.length - 1);
      setTimeout(() => {
        setActiveAssessment(res.data);
        setProcessing(false);
        setCurrentView('results');
      }, 500);

    } catch (err) {
      alert(err.response?.data?.detail || 'Building crop assessment failed.');
      setProcessing(false);
    }
  };

  // Run Nepal Quick Ready Demo
  const handleStartNepalDemo = async () => {
    if (!currentUser) return;
    setProcessing(true);
    setStepIndex(0);

    const formData = new FormData();
    formData.append('user_id', currentUser.id);
    formData.append('is_nepal_demo', 'true');

    try {
      const interval = setInterval(() => {
        setStepIndex((prev) => (prev < steps.length - 2 ? prev + 1 : prev));
      }, 400);

      const res = await axios.post(`${API_BASE_URL}/api/assessment/satellite`, formData);

      clearInterval(interval);
      setStepIndex(steps.length - 1);

      setTimeout(() => {
        setActiveAssessment(res.data);
        setProcessing(false);
        setCurrentView('results');
      }, 400);

    } catch (err) {
      alert(err.response?.data?.detail || 'Nepal demo execution failed.');
      setProcessing(false);
    }
  };

  // Unauthenticated Public Landing Page
  if (!currentUser) {
    return (
      <>
        <LandingPage
          onOpenLogin={() => setIsLoginOpen(true)}
          onOpenSignup={() => setIsSignupOpen(true)}
        />
        <LoginModal
          isOpen={isLoginOpen}
          onClose={() => setIsLoginOpen(false)}
          onSuccess={handleAuthSuccess}
          onSwitchToSignup={() => setIsSignupOpen(true)}
        />
        <SignupModal
          isOpen={isSignupOpen}
          onClose={() => setIsSignupOpen(false)}
          onSuccess={handleAuthSuccess}
          onSwitchToLogin={() => setIsLoginOpen(true)}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      <Navbar
        currentUser={currentUser}
        currentView={currentView}
        onNavigate={(view) => setCurrentView(view)}
        onLogout={handleLogout}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {processing ? (
          <ProcessingScreen steps={steps} currentStepIndex={stepIndex} />
        ) : (
          <>
            {currentView === 'home' && (
              <InputSelector
                onStartSatellite={handleStartSatellite}
                onStartBuilding={handleStartBuilding}
                onStartNepalDemo={handleStartNepalDemo}
                loading={processing}
              />
            )}

            {currentView === 'results' && activeAssessment && (
              <ResultsPage
                assessment={activeAssessment}
                currentUser={currentUser}
                onBack={() => setCurrentView('home')}
              />
            )}

            {currentView === 'history' && (
              <AssessmentHistory
                currentUser={currentUser}
                onSelectAssessment={(item) => {
                  setActiveAssessment(item);
                  setCurrentView('results');
                }}
              />
            )}

            {currentView === 'admin' && (
              <AdminDashboard currentUser={currentUser} />
            )}
          </>
        )}

      </main>

      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <p>© 2026 GeoDamageAI Emergency Disaster Assessment Engine</p>
      </footer>
    </div>
  );
}
