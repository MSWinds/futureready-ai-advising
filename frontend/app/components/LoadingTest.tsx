// components/LoadingTest.tsx
'use client'

import { useState } from 'react'

export default function LoadingTest() {
  const [isLoading, setIsLoading] = useState(false)

  const handleClick = () => {
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 3000) // Simulate 3s loading
  }

  return (
    <div className="p-8">
      <button
        onClick={handleClick}
        disabled={isLoading}
        className="w-48 py-3 bg-blue-500 text-white rounded-lg disabled:opacity-50"
      >
        {isLoading ? (
          <div className="flex items-center justify-center">
            <svg
              className="animate-spin h-5 w-5 mr-2"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Loading...
          </div>
        ) : (
          'Test Button'
        )}
      </button>
    </div>
  )
}