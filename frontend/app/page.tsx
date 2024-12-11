// app/page.tsx
'use client'

import { useState } from 'react'
import StudentForm from './components/Form'
import { motion } from 'framer-motion'
import { ChevronRight } from 'lucide-react'

export default function Home() {
  const [showForm, setShowForm] = useState(false)

  return (
    <main className="min-h-screen bg-gradient-to-r from-[#0f172a] to-[#334155] py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {!showForm ? (
          // Welcome Screen
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="min-h-[80vh] flex flex-col items-center justify-center"
          >
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-gray-50/95 backdrop-blur-md rounded-2xl shadow-xl p-12 w-full text-center"
            >
              <motion.h1 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="text-5xl md:text-6xl font-extrabold text-center mb-6 bg-clip-text text-transparent bg-gradient-to-r from-[#0f172a] to-[#334155]"
              >
                Future-Ready AI-Empowered Academic Advising
              </motion.h1>
              
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="space-y-4 mb-12"
              >
                <p className="text-center text-2xl text-gray-600">
                  An Adaptive and Sustainable Tool for Student Success
                </p>
                <p className="text-center text-xl text-gray-500 italic">
                  Empowering students with personalized guidance through AI-enhanced advising
                </p>
              </motion.div>

              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowForm(true)}
                className="group relative inline-flex items-center justify-center px-8 py-4 text-lg font-medium text-white bg-gradient-to-r from-[#0f172a] to-[#334155] rounded-xl shadow-lg hover:from-[#1e293b] hover:to-[#475569] transition-all duration-200 overflow-hidden"
              >
                <span className="relative z-10 flex items-center">
                  Begin Advising Session
                  <ChevronRight className="ml-2 h-5 w-5 transform group-hover:translate-x-1 transition-transform" />
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-[#1e293b] to-[#475569] opacity-0 group-hover:opacity-100 transition-opacity" />
              </motion.button>
            </motion.div>
          </motion.div>
        ) : (
          // Form View (with enter animation)
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
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
          </motion.div>
        )}
      </div>
    </main>
  )
}