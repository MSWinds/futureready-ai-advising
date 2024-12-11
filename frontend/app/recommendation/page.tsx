'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import LoadingOverlay from '../components/Loading';
import RecommendationCard from '../components/RecommendationCard';
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '../components/alert';

// Recommendation Types remain the same
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

type WebSocketMessage =
  | { type: 'status'; payload: { message: string } }
  | { type: 'recommendations'; payload: RecommendationsResponse }
  | { type: 'error'; payload: string };

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

export default function RecommendationPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('id');

  const [isLoading, setIsLoading] = useState(true);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState<string>('Retrieving recommendations...');

  useEffect(() => {
    let ws: WebSocket;

    const setupWebSocket = () => {
      if (!sessionId) {
        setError('Session ID is missing. Please try again.');
        setIsLoading(false);
        return;
      }

      // First check localStorage for existing recommendations
      const cachedRecommendations = localStorage.getItem(`recommendations_${sessionId}`);
      if (cachedRecommendations) {
        try {
          const data = JSON.parse(cachedRecommendations);
          setRecommendations(
            data.recommendations.map((rec: any) => ({
              ...rec,
              type: normalizeRecommendationType(rec.type),
            }))
          );
          setIsLoading(false);
          // Clear the cache after successful retrieval
          localStorage.removeItem(`recommendations_${sessionId}`);
          return;
        } catch (err) {
          console.error('Failed to parse cached recommendations:', err);
        }
      }

      // If no cached data or cache parsing failed, establish WebSocket connection
      ws = new WebSocket('ws://localhost:8000/ws/verify_session');

      ws.onopen = () => {
        console.log('WebSocket connected');
        setCurrentStatus('Connecting to server...');
        ws.send(JSON.stringify({ 
          session_id: sessionId,
          summary: 'fetch_from_db'
        }));
      };

      ws.onmessage = (event) => {
        try {
          const response = JSON.parse(event.data) as WebSocketMessage;

          switch (response.type) {
            case 'status':
              setCurrentStatus(response.payload.message);
              break;

            case 'recommendations':
              setRecommendations(
                response.payload.recommendations.map((rec) => ({
                  ...rec,
                  type: normalizeRecommendationType(rec.type),
                }))
              );
              setIsLoading(false);
              // Close WebSocket after receiving recommendations
              if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
              }
              break;

            case 'error':
              setError(response.payload);
              setIsLoading(false);
              // Close WebSocket on error
              if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
              }
              break;

            default:
              console.warn('Unexpected message type:', response);
          }
        } catch (err) {
          console.error('Failed to process message:', err);
          setError('An error occurred while processing recommendations.');
          setIsLoading(false);
          // Close WebSocket on error
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error. Please try again.');
        setIsLoading(false);
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };
    };

    setupWebSocket();

    // Cleanup function
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        console.log('Cleaning up WebSocket connection');
        ws.close();
      }
    };
  }, [sessionId]);


  return (
    <main className="min-h-screen bg-gradient-to-r from-[#0f172a] to-[#334155] py-12 px-4">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="bg-gray-50/95 backdrop-blur-md rounded-2xl shadow-xl p-8 mb-8">
          <h1 className="text-4xl font-extrabold text-center mb-4 bg-clip-text text-transparent bg-gradient-to-r from-[#0f172a] to-[#334155]">
            Your Personalized Career Recommendations
          </h1>
          <p className="text-center text-xl text-gray-600 mb-2">
            AI-Enhanced Career Guidance Based on StudentProfile
          </p>
          <p className="text-center text-gray-500 italic">
            Discover pathways aligned with student interests and strengths
          </p>
        </div>

        {isLoading ? (
          <LoadingOverlay isVisible={true} currentMessage={currentStatus} />
        ) : error ? (
          <Alert variant="destructive" className="bg-red-50 border-red-200">
            <div className="flex items-center">
              <AlertCircle className="h-4 w-4 mr-2" />
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </div>
          </Alert>
        ) : recommendations.length > 0 ? (
          <div className="space-y-6 animate-fade-in">
            {recommendations.map((rec) => (
              <RecommendationCard key={rec.id} {...rec} totalCount={recommendations.length} />
            ))}
          </div>
        ) : (
          <Alert className="bg-gray-50 border-gray-200">
            <AlertDescription className="text-gray-600">
              No recommendations available at this time.
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && (
          <div className="bg-gray-50/95 backdrop-blur-md rounded-2xl shadow-xl p-8">
            <div className="flex gap-4">
              <button
                onClick={() => window.history.back()}
                className="flex-1 py-3 bg-gradient-to-r from-[#0f172a] to-[#334155] text-white font-bold rounded-lg hover:from-[#1e293b] hover:to-[#475569] shadow-lg transform hover:scale-105 transition-all"
              >
                Back to Student Profile
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}