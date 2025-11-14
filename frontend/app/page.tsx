'use client'

import { useState } from 'react'
import LoginScreen from '@/components/login-screen'
import MainDashboard from '@/components/main-dashboard'

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  if (!isLoggedIn) {
    return <LoginScreen onLogin={() => setIsLoggedIn(true)} />
  }

  return <MainDashboard onLogout={() => setIsLoggedIn(false)} />
}
