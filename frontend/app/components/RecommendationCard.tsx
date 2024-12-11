// components/RecommendationCard.tsx
'use client'

import { ChevronDown, ChevronUp, Lightbulb, Target, Users } from 'lucide-react';
import { useState } from 'react';
import type { DisplayRecommendation } from '../recommendation/page';

interface RecommendationCardProps extends DisplayRecommendation {
    totalCount: number;
}

export default function RecommendationCard({
    id,
    type,
    quickView,
    detailedView,
    totalCount
}: RecommendationCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    // Color schemes that complement our dark blue gradient background
    const getColors = () => {
        switch (type) {
            case 'Alumni':
                return {
                    badge: 'bg-blue-100 text-blue-800',
                    icon: 'text-blue-600',
                    border: 'border-blue-200',
                    highlight: 'bg-blue-50'
                };
            case 'Trend':
                return {
                    badge: 'bg-emerald-100 text-emerald-800',
                    icon: 'text-emerald-600',
                    border: 'border-emerald-200',
                    highlight: 'bg-emerald-50'
                };
            case 'Inspiration':
                return {
                    badge: 'bg-violet-100 text-violet-800',
                    icon: 'text-violet-600',
                    border: 'border-violet-200',
                    highlight: 'bg-violet-50'
                };
        }
    };

    const colors = getColors();

    const getIcon = () => {
        switch (type) {
            case 'Alumni':
                return <Users className={`w-5 h-5 ${colors.icon}`} />;
            case 'Trend':
                return <Target className={`w-5 h-5 ${colors.icon}`} />;
            case 'Inspiration':
                return <Lightbulb className={`w-5 h-5 ${colors.icon}`} />;
        }
    };

    return (
        <div className={`bg-white rounded-xl shadow-lg border-2 ${colors.border} transition-all duration-300 hover:shadow-xl`}>
            {/* Header */}
            <div className="p-6 border-b border-gray-100">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        {getIcon()}
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors.badge}`}>
                            {type}
                        </span>
                        <span className="text-gray-500 text-sm">
                            {id} of {totalCount}
                        </span>
                    </div>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                    >
                        {isExpanded ? 
                            <ChevronUp className="w-5 h-5" /> : 
                            <ChevronDown className="w-5 h-5" />
                        }
                    </button>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{quickView.title}</h3>
            </div>

            {/* Quick View (Always Visible) */}
            <div className="p-6 border-b border-gray-100">
                <p className="text-gray-600 mb-4">{quickView.summary}</p>

                <div className="mb-4">
                    <h4 className="font-semibold text-gray-700 mb-2">Key Points</h4>
                    <ul className="space-y-2">
                        {quickView.keyPoints.map((point, index) => (
                            <li key={index} className="flex items-start">
                                <span className={`inline-block w-5 h-5 rounded-full ${colors.badge} flex items-center justify-center text-sm font-medium mr-3 mt-0.5`}>
                                    {index + 1}
                                </span>
                                <span className="text-gray-600">{point}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className={`${colors.highlight} rounded-lg p-4`}>
                    <h4 className="font-semibold text-gray-700 mb-2">Next Step</h4>
                    <p className="text-gray-600">{quickView.nextStep}</p>
                </div>
            </div>

            {/* Detailed View (Expandable) */}
            {isExpanded && (
                <div className="p-6 space-y-6">
                    <div>
                        <h4 className="font-semibold text-gray-700 mb-2">Detailed Reasoning</h4>
                        <p className="text-gray-600">{detailedView.reasoning}</p>
                    </div>

                    <div className={`${colors.highlight} rounded-lg p-4`}>
                        <h4 className="font-semibold text-gray-700 mb-3">Evidence</h4>
                        <div className="space-y-3">
                            <div>
                                <h5 className="text-sm font-medium text-gray-700">Alumni Patterns</h5>
                                <p className="text-gray-600">{detailedView.evidence.alumniPatterns}</p>
                            </div>
                            <div>
                                <h5 className="text-sm font-medium text-gray-700">Industry Context</h5>
                                <p className="text-gray-600">{detailedView.evidence.industryContext}</p>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 className="font-semibold text-gray-700 mb-2">Discussion Points</h4>
                        <ul className="space-y-2">
                            {detailedView.discussionPoints.map((point, index) => (
                                <li key={index} className="flex items-start">
                                    <span className={`inline-block w-5 h-5 rounded-full ${colors.badge} flex items-center justify-center text-sm font-medium mr-3 mt-0.5`}>
                                        {index + 1}
                                    </span>
                                    <span className="text-gray-600">{point}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}
        </div>
    );
}
