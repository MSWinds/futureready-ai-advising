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
  showProgressMessages?: boolean;
  currentMessage?: string;  // Added for custom status messages
}

export default function LoadingOverlay({ 
  isVisible, 
  showProgressMessages = true,
  currentMessage  // New prop for custom messages
}: LoadingOverlayProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  
  useEffect(() => {
    if (isVisible && showProgressMessages && !currentMessage) {
      const interval = setInterval(() => {
        setMessageIndex((prev) => 
          prev === loadingMessages.length - 1 ? prev : prev + 1
        );
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [isVisible, showProgressMessages, currentMessage]);

  if (!isVisible) return null;

  // Determine which message to show
  const displayMessage = currentMessage || loadingMessages[messageIndex];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with blur effect */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
      
      {/* Loading card */}
      <div className="relative bg-white/90 rounded-2xl shadow-2xl p-8 max-w-md mx-4 backdrop-blur-xl">
        {/* Animated dots background */}
        <div className="absolute inset-0 rounded-2xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-[#0f172a]/10 to-[#334155]/10 animate-pulse" />
        </div>
        
        {/* Content */}
        <div className="relative space-y-4">
          {/* Spinner */}
          <div className="flex justify-center">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 border-4 border-t-transparent border-[#0f172a] rounded-full animate-spin animate-pulse-ring" />
              <div className="absolute inset-2 border-4 border-t-transparent border-[#334155] rounded-full animate-spin-reverse" />
            </div>
          </div>
          
          {/* Message */}
          <div className="text-center space-y-2">
            <p className="text-lg font-medium text-gray-800 animate-text-fade">
              {showProgressMessages ? displayMessage : "Processing..."}
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