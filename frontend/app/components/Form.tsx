// app/components/Form.tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

interface FormFields {
  academic_interests: string;
  career_paths: string;
  course_preferences: string;
  experience: string;
  skills: string;
  extracurriculars: string;
  decision_factors: string;
  advisor_notes: string;
}

export default function StudentForm() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [summary, setSummary] = useState<string | null>(null)
  const [formData, setFormData] = useState<FormFields>({
    academic_interests: '',
    career_paths: '',
    course_preferences: '',
    experience: '',
    skills: '',
    extracurriculars: '',
    decision_factors: '',
    advisor_notes: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!Object.values(formData).some(value => value.trim() !== '')) {
      alert('Please fill in at least one question to proceed.')
      return
    }
    setIsLoading(true)
    setSummary(null)

    try {
      const ws = new WebSocket('ws://localhost:8000/ws/profile')

      ws.onopen = () => {
        console.log('WebSocket opened')
        ws.send(JSON.stringify(formData))
      }

      ws.onmessage = (event) => {
        console.log('Received message:', event.data)
        const response = JSON.parse(event.data)
        if (response.type === 'profile_summary') {
          setSummary(response.payload)
          document.getElementById('summary-section')?.scrollIntoView({ behavior: 'smooth' })
          ws.close()
        } else if (response.type === 'error') {
          alert('Error: ' + response.payload)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        alert('Connection error occurred')
        setIsLoading(false)
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
        setIsLoading(false)
      }
    } catch (error) {
      console.error('Error:', error)
      alert('An error occurred')
      setIsLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const proceedToNext = () => {
    if (summary) {
      router.push(`/recommendation?summary=${encodeURIComponent(summary)}`)
    }
  }

  return (
        <div className="space-y-6">
        <form className="bg-gray-50/95 backdrop-blur-md rounded-2xl shadow-xl p-8">
            <div className="mb-8">
            <h2 className="text-2xl font-bold text-[#0f172a] mb-2">
                Student Profile Collection
            </h2>
            <p className="text-gray-600">
                Enter student information to generate AI-enhanced recommendations
            </p>
            </div>
            {/* Form Fields */}
            {[
            { 
                name: 'academic_interests', 
                question: "Student's primary academic interests and strengths"
            },
            { 
                name: 'career_paths', 
                question: "Career paths or industries of interest to the student"
            },
            { 
                name: 'course_preferences', 
                question: "Student's favorite and least favorite courses"
            },
            { 
                name: 'experience', 
                question: "Student's relevant experience"
            },
            { 
                name: 'skills', 
                question: "Notable skills or achievements"
            },
            { 
                name: 'extracurriculars', 
                question: "Key extracurricular activities or passion projects"
            },
            { 
                name: 'decision_factors', 
                question: "Key factors influencing student's academic/career decisions"
            },
            { 
                name: 'advisor_notes', 
                question: "Additional observations or context about student's goals/challenges"
            }
            ].map(({ name, question }) => (
            <div key={name} className="mb-4 bg-white p-4 rounded-lg shadow-md">
                <label className="block text-md font-semibold text-[#334155] mb-2 text-2xl">
                {question}
                </label>
                <textarea
                name={name}
                value={formData[name as keyof FormFields]}
                onChange={handleChange}
                className="w-full p-4 border border-[#334155] rounded-lg shadow-sm focus:ring-2 focus:ring-[#334155] focus:outline-none text-gray-700"
                rows={3}
                placeholder="Enter information or leave blank if not discussed"
                />
            </div>
            ))}

          {/* Generate Profile Button */}
          {!summary && (
            <div className="w-full">
              {isLoading ? (
                <div className="w-full flex items-center justify-center py-3 text-[#0f172a]">
                  <svg
                    className="animate-spin h-5 w-5 mr-2"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="font-semibold">Generating Student Profile...</span>
                </div>
              ) : (
                // Generate Profile Button
                <button
                  type="submit"
                  onClick={handleSubmit}
                  className="w-full py-3 bg-gradient-to-r from-[#0f172a] to-[#334155] text-white font-bold rounded-lg hover:from-[#1e293b] hover:to-[#475569] shadow-lg transform hover:scale-105 transition-all"
                >
                  Generate Profile
                </button>
              )}
            </div>
          )}
        </form>

        {/* Summary Section */}
        {summary && (
          <div
            id="summary-section"
            className="bg-gray-50/95 backdrop-blur-md rounded-2xl shadow-xl p-8 animate-fade-in"
          >
            <h2 className="text-2xl font-bold text-[#0f172a] mb-4">Student Profile Summary</h2>
            <div className="prose max-w-none mb-6">
              <p className="text-gray-700 whitespace-pre-wrap">{summary}</p>
            </div>
            <div className="flex gap-4">
              {/* Regenerate Profile Button */}
              <button
                onClick={(e) => {
                  e.preventDefault();
                  handleSubmit(e);
                }}
                disabled={isLoading}
                className="flex-1 py-3 bg-gradient-to-r from-[#0f172a] to-[#334155] text-white font-bold rounded-lg hover:from-[#1e293b] hover:to-[#475569] shadow-lg transform hover:scale-105 transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <svg
                      className="animate-spin h-5 w-5 mr-2"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Regenerating...</span>
                  </div>
                ) : (
                  'Regenerate'
                )}
              </button>
              {/* Continue to Next Step Button */}
              <button
                onClick={proceedToNext}
                className="flex-1 py-3 bg-gradient-to-r from-[#0f172a] to-[#334155] text-white font-bold rounded-lg hover:from-[#1e293b] hover:to-[#475569] shadow-lg transform hover:scale-105 transition-all"
              >
                Continue to Next Step
              </button>
            </div>
          </div>
        )}
      </div>
  )
}
