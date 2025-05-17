"use client"

import { createContext, useContext, useState, type ReactNode } from "react"
import type { AttendeePreferences } from "./types"

interface WizardContextType {
  preferences: AttendeePreferences
  updatePreferences: (updates: Partial<AttendeePreferences>) => void
  currentStep: number
  goToStep: (step: number) => void
  nextStep: () => void
  prevStep: () => void
  totalSteps: number
}

const defaultPreferences: AttendeePreferences = {
  name: "",
  location: "",
  availability: {},
  selectedRegions: [], // Add this line for destination preferences
}

const WizardContext = createContext<WizardContextType | undefined>(undefined)

export function PreferenceWizardProvider({
  children,
  initialPreferences = defaultPreferences,
  totalSteps = 3, // Update to 3 steps
}: {
  children: ReactNode
  initialPreferences?: AttendeePreferences
  totalSteps?: number
}) {
  const [preferences, setPreferences] = useState<AttendeePreferences>(initialPreferences)
  const [currentStep, setCurrentStep] = useState(0)

  const updatePreferences = (updates: Partial<AttendeePreferences>) => {
    setPreferences((prev) => ({ ...prev, ...updates }))
  }

  const goToStep = (step: number) => {
    if (step >= 0 && step < totalSteps) {
      setCurrentStep(step)
    }
  }

  const nextStep = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  return (
    <WizardContext.Provider
      value={{
        preferences,
        updatePreferences,
        currentStep,
        goToStep,
        nextStep,
        prevStep,
        totalSteps,
      }}
    >
      {children}
    </WizardContext.Provider>
  )
}

export function useWizard() {
  const context = useContext(WizardContext)
  if (context === undefined) {
    throw new Error("useWizard must be used within a PreferenceWizardProvider")
  }
  return context
}
