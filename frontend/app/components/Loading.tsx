// app/components/Loading.tsx
import React, { useState, useEffect } from 'react';

const loadingMessages = [
  "Analyzing student profile...",
  "Searching alumni database...",
  "Generating career recommendations...",
  "Finding industry trends...",
  "Curating personalized matches...",
  "Almost there..."
];

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  showProgressMessages?: boolean;
}

export default function LoadingOverlay({ 
  isVisible, 
  message,
  showProgressMessages = true 
}: LoadingOverlayProps) {
  const [currentMessage, setCurrentMessage] = useState(0);

  useEffect(() => {
    if (isVisible && showProgressMessages) {
      const interval = setInterval(() => {
        setCurrentMessage((prev) => 
          prev === loadingMessages.length - 1 ? prev : prev + 1
        );
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [isVisible, showProgressMessages]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with blur effect */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
      
      {/* Loading card */}
      <div className="relative bg-white/90 rounded-2xl shadow-2xl p-8 max-w-md mx-4 backdrop-blur-xl">
        {/* Animated dots background */}
        <div className="absolute inset-0 rounded-2xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 animate-pulse" />
        </div>
        
        {/* Content */}
        <div className="relative space-y-4">
          {/* Spinner */}
          <div className="flex justify-center">
            <div className="relative w-16 h-16">
                <div className="absolute inset-0 border-4 border-t-transparent border-blue-500 rounded-full animate-spin animate-pulse-ring" />
                <div className="absolute inset-2 border-4 border-t-transparent border-purple-500 rounded-full animate-spin-reverse" />
            </div>
          </div>
          
          {/* Message */}
          <div className="text-center space-y-2">
            <p className="text-lg font-medium text-gray-800 animate-text-fade">
                {showProgressMessages ? loadingMessages[currentMessage] : message}
            </p>
            <p className="text-sm text-gray-500">
              Please wait while we process your request
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}