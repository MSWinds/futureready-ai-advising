// app/recommendation/page.tsx
'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import LoadingOverlay from '../components/Loading';
import RecommendationCard from '../components/RecommendationCard';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '../components/alert';
import { FC } from 'react';

// Recommendation Types matching Pydantic models
interface QuickView {
  title: string;
  summary: string;
  keyPoints: string[];
  nextStep: string;
}

interface DetailedView {
  reasoning: string;
  evidence: {
    alumniPatterns: string;
    industryContext: string;
  };
  discussionPoints: string[];
}

interface Recommendation {
  id: number;
  type: string;
  quickView: QuickView;
  detailedView: DetailedView;
}

interface RecommendationsResponse {
  recommendations: Recommendation[];
  timestamp: string;
}

// WebSocket Message Types
interface WebSocketStatusMessage {
  type: 'status';
  payload: {
    phase: string;
    message: string;
    progress: number;
  };
}

interface WebSocketRecommendationsMessage {
  type: 'recommendations';
  payload: RecommendationsResponse;
}

interface WebSocketErrorMessage {
  type: 'error';
  payload: string;
}

type WebSocketMessage = 
  | WebSocketStatusMessage 
  | WebSocketRecommendationsMessage 
  | WebSocketErrorMessage;

// Frontend Display Types
interface DisplayRecommendation extends Omit<Recommendation, 'type'> {
  type: 'Alumni' | 'Trend' | 'Inspiration';
}

// Helper Functions
const normalizeRecommendationType = (type: string): 'Alumni' | 'Trend' | 'Inspiration' => {
  switch (type.toLowerCase()) {
    case 'alumni':
      return 'Alumni';
    case 'trend':
      return 'Trend';
    case 'figure':
      return 'Inspiration';
    default:
      console.warn(`Unexpected recommendation type: ${type}`);
      return 'Alumni';
  }
};

const validateRecommendation = (rec: any): rec is Recommendation => {
  return (
    typeof rec?.id === 'number' &&
    typeof rec?.type === 'string' &&
    typeof rec?.quickView?.title === 'string' &&
    typeof rec?.quickView?.summary === 'string' &&
    Array.isArray(rec?.quickView?.keyPoints) &&
    typeof rec?.quickView?.nextStep === 'string' &&
    typeof rec?.detailedView?.reasoning === 'string' &&
    typeof rec?.detailedView?.evidence?.alumniPatterns === 'string' &&
    typeof rec?.detailedView?.evidence?.industryContext === 'string' &&
    Array.isArray(rec?.detailedView?.discussionPoints)
  );
};

export default function RecommendationPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('id');
  const phase = searchParams.get('phase');
  
  const [isLoading, setIsLoading] = useState(true);
  const [recommendations, setRecommendations] = useState<{
    recommendations: DisplayRecommendation[];
    timestamp: string;
  }>({
    recommendations: [],
    timestamp: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState<string>(
    phase === 'recommendation' ? 'Processing recommendations...' : 'Establishing connection...'
  );
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 3;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    const connectWebSocket = async () => {
      if (!sessionId) {
        setError('No session ID provided');
        setIsLoading(false);
        return;
      }

      try {
        // Close existing connection if any
        if (ws) {
          ws.close();
        }

        // Establish new connection
        ws = new WebSocket(`ws://localhost:8000/ws/recommendations/${sessionId}`);

        ws.onopen = () => {
          console.log('WebSocket connected');
          setCurrentStatus('Retrieving recommendations...');
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const response = JSON.parse(event.data) as WebSocketMessage;
            console.log('WebSocket response:', response);

            switch (response.type) {
              case 'status':
                setCurrentStatus(response.payload.message);
                break;

              case 'recommendations':
                const { recommendations: rawRecs, timestamp } = response.payload;
                
                // Validate recommendations
                const validRecommendations = rawRecs.filter(validateRecommendation);
                
                if (validRecommendations.length !== rawRecs.length) {
                  console.warn('Some recommendations failed validation');
                }

                // Transform to display format
                const displayRecommendations = validRecommendations.map(rec => ({
                  ...rec,
                  type: normalizeRecommendationType(rec.type)
                }));

                setRecommendations({
                  recommendations: displayRecommendations,
                  timestamp
                });
                setIsLoading(false);
                setRetryCount(0); // Reset retry count on success
                break;

              case 'error':
                throw new Error(response.payload);
            }
          } catch (err) {
            console.error('Message processing error:', err);
            setError(err instanceof Error ? err.message : 'An unexpected error occurred');
            handleReconnect();
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          handleReconnect();
        };

        ws.onclose = () => {
          console.log('WebSocket closed');
          if (recommendations.recommendations.length === 0 && !error) {
            handleReconnect();
          }
        };
      } catch (err) {
        console.error('WebSocket connection error:', err);
        handleReconnect();
      }
    };

    const handleReconnect = () => {
      if (retryCount < MAX_RETRIES) {
        setCurrentStatus(`Reconnecting... (Attempt ${retryCount + 1}/${MAX_RETRIES})`);
        setRetryCount(prev => prev + 1);
        reconnectTimeout = setTimeout(connectWebSocket, 2000); // Retry after 2 seconds
      } else {
        setError('Failed to connect after multiple attempts');
        setIsLoading(false);
      }
    };

    connectWebSocket();

    // Cleanup function
    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [sessionId, retryCount]);

  return (
    <main className="min-h-screen bg-gradient-to-r from-[#0f172a] to-[#334155] py-12 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="bg-gray-50/95 backdrop-blur-md rounded-2xl shadow-xl p-8 mb-8">
          <h1 className="text-4xl font-extrabold text-center mb-4 bg-clip-text text-transparent bg-gradient-to-r from-[#0f172a] to-[#334155]">
            Your Personalized Career Recommendations
          </h1>
          <p className="text-center text-xl text-gray-600 mb-2">
            AI-Enhanced Career Guidance Based on Your Profile
          </p>
          <p className="text-center text-gray-500 italic">
            Discover pathways aligned with your interests and strengths
          </p>
        </div>

        {isLoading ? (
          <LoadingOverlay
            isVisible={true}
            showProgressMessages={true}
            currentMessage={currentStatus}
          />
        ) : error ? (
          <Alert variant="destructive" className="bg-red-50 border-red-200">
            <div className="flex items-center">
              <AlertCircle className="h-4 w-4 mr-2" />
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </div>
          </Alert>
        ) : recommendations.recommendations.length > 0 ? (
          <div className="space-y-6 animate-fade-in">
            {recommendations.recommendations.map((recommendation) => (
              <RecommendationCard
                key={recommendation.id}
                {...recommendation}
                totalCount={recommendations.recommendations.length}
              />
            ))}
          </div>
        ) : (
          <Alert className="bg-gray-50 border-gray-200">
            <AlertDescription className="text-gray-600">
              No recommendations available.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </main>
  );
}