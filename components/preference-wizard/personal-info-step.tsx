"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import type { WizardStepProps } from "./types"
import { MapPin } from "lucide-react"

export function PersonalInfoStep({ preferences, updatePreferences, onNext }: WizardStepProps) {
  const [errors, setErrors] = useState<{ name?: string; location?: string }>({})

  const handleNext = () => {
    const newErrors: { name?: string; location?: string } = {}

    if (!preferences.name.trim()) {
      newErrors.name = "Please enter your name"
    }

    if (!preferences.location.trim()) {
      newErrors.location = "Please enter your starting location"
    }

    setErrors(newErrors)

    if (Object.keys(newErrors).length === 0) {
      onNext()
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Your Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Your Name</Label>
          <Input
            id="name"
            placeholder="Enter your name"
            value={preferences.name}
            onChange={(e) => {
              updatePreferences({ name: e.target.value })
              if (errors.name) setErrors({ ...errors, name: undefined })
            }}
          />
          {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="location">Starting Location</Label>
          <div className="relative">
            <Input
              id="location"
              placeholder="Enter any location (city, address, landmark, etc.)"
              value={preferences.location}
              onChange={(e) => {
                updatePreferences({ location: e.target.value })
                if (errors.location) setErrors({ ...errors, location: undefined })
              }}
              className="pl-10"
            />
            <MapPin className="absolute left-3 top-2.5 h-5 w-5 text-muted-foreground" />
          </div>
          <p className="text-xs text-muted-foreground">Enter your preferred starting point for the hiking trip</p>
          {errors.location && <p className="text-sm text-destructive">{errors.location}</p>}
        </div>
      </CardContent>
      <CardFooter className="flex justify-end">
        <Button onClick={handleNext}>Next</Button>
      </CardFooter>
    </Card>
  )
}
