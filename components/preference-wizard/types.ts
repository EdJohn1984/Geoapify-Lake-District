export interface AttendeePreferences {
  name: string
  location: string
  availability: Record<string, boolean>
  selectedRegions: string[] // Add this line for destination preferences
}

export interface WizardStepProps {
  preferences: AttendeePreferences
  updatePreferences: (updates: Partial<AttendeePreferences>) => void
  onNext: () => void
  onBack?: () => void
  isLastStep?: boolean
}

export interface Weekend {
  saturday: Date
  sunday: Date
  formatted: string
}
