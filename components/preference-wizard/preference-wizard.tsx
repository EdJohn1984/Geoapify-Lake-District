"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { PreferenceWizardProvider, useWizard } from "./wizard-context"
import { StepIndicator } from "./step-indicator"
import { PersonalInfoStep } from "./personal-info-step"
import { DestinationStep } from "./destination-step" // Import the new step
import { AvailabilityStep } from "./availability-step"
import type { Weekend, AttendeePreferences } from "./types"
import { Loader2 } from "lucide-react"
import { submitPreferences } from "@/lib/actions" // We'll update this action

interface PreferenceWizardProps {
  token: string
  weekends: Weekend[]
  initialPreferences?: AttendeePreferences
}

function WizardSteps({ token, weekends }: { token: string; weekends: Weekend[] }) {
  const { currentStep, preferences, updatePreferences, nextStep, prevStep } = useWizard()
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (
    token: string,
    name: string,
    location: string,
    selectedRegions: string[],
    availability: { date: string; isAvailable: boolean }[],
  ) => {
    setIsSubmitting(true)
    try {
      await submitPreferences({
        token,
        name,
        location,
        selectedRegions,
        availability,
      })
      router.push(`/trip/${token}/results`)
    } catch (err) {
      console.error("Error submitting preferences:", err)
      throw err
    }
  }

  // Render the current step
  switch (currentStep) {
    case 0:
      return <PersonalInfoStep preferences={preferences} updatePreferences={updatePreferences} onNext={nextStep} />
    case 1:
      return (
        <DestinationStep
          preferences={preferences}
          updatePreferences={updatePreferences}
          onNext={nextStep}
          onBack={prevStep}
        />
      )
    case 2:
      return (
        <AvailabilityStep
          preferences={preferences}
          updatePreferences={updatePreferences}
          onBack={prevStep}
          weekends={weekends}
          token={token}
          onSubmit={(token, name, location, availability) =>
            handleSubmit(token, name, location, preferences.selectedRegions, availability)
          }
          isLastStep
        />
      )
    default:
      return (
        <div className="flex justify-center items-center p-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      )
  }
}

export function PreferenceWizard({ token, weekends, initialPreferences }: PreferenceWizardProps) {
  return (
    <PreferenceWizardProvider initialPreferences={initialPreferences} totalSteps={3}>
      <div className="w-full max-w-md mx-auto">
        <StepIndicator />
        <WizardSteps token={token} weekends={weekends} />
      </div>
    </PreferenceWizardProvider>
  )
}
