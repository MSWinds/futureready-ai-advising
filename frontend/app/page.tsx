// app/page.tsx
'use client'

import StudentForm from './components/Form'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-r from-[#0f172a] to-[#334155] py-12 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="bg-gray-50/95 backdrop-blur-md rounded-2xl shadow-xl p-8 mb-8">
          <h1 className="text-4xl md:text-4xl font-extrabold text-center text-[#0f172a] mb-4 bg-clip-text text-transparent bg-gradient-to-r from-[#0f172a] to-[#334155]">
            Future-Ready AI-Empowered Academic Advising
          </h1>
          <p className="text-center text-xl text-gray-600 mb-2">
            An Adaptive and Sustainable Tool for Student Success
          </p>
          <p className="text-center text-gray-500 italic">
            Empowering students with personalized guidance through AI-enhanced advising
          </p>
        </div>
        <StudentForm />
      </div>
    </main>
  )
}
