"use client"

import { useState, useEffect } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import { Calendar, CheckCircle } from "lucide-react"
import type { WizardStepProps, Weekend } from "./types"

interface AvailabilityStepProps extends WizardStepProps {
  weekends: Weekend[]
  token: string
  onSubmit: (
    token: string,
    name: string,
    location: string,
    availability: { date: string; isAvailable: boolean }[],
  ) => Promise<void>
}

export function AvailabilityStep({
  preferences,
  updatePreferences,
  onBack,
  weekends,
  token,
  onSubmit,
  isLastStep = true,
}: AvailabilityStepProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  // Initialize availability with useEffect to avoid state updates during render
  useEffect(() => {
    if (Object.keys(preferences.availability).length === 0 && weekends.length > 0) {
      const initialAvailability = weekends.reduce(
        (acc, weekend) => {
          acc[weekend.formatted] = false
          return acc
        },
        {} as Record<string, boolean>,
      )
      updatePreferences({ availability: initialAvailability })
    }
  }, [preferences.availability, weekends, updatePreferences])

  const toggleAvailability = (date: string) => {
    updatePreferences({
      availability: {
        ...preferences.availability,
        [date]: !preferences.availability[date],
      },
    })
  }

  const handleSubmit = async () => {
    setIsLoading(true)
    setError("")

    try {
      await onSubmit(
        token,
        preferences.name,
        preferences.location,
        Object.entries(preferences.availability).map(([date, isAvailable]) => ({
          date,
          isAvailable,
        })),
      )
    } catch (err) {
      setError("Failed to submit availability. Please try again.")
      console.error(err)
      setIsLoading(false)
    }
  }

  // Format weekend dates, handling month transitions
  const formatWeekendDates = (weekend: Weekend) => {
    const satMonth = weekend.saturday.getMonth()
    const sunMonth = weekend.sunday.getMonth()

    if (satMonth === sunMonth) {
      // Same month
      return `${format(weekend.saturday, "MMMM d")} - ${format(weekend.sunday, "d")}, ${format(weekend.sunday, "yyyy")}`
    } else {
      // Different months
      return `${format(weekend.saturday, "MMMM d")} - ${format(weekend.sunday, "MMMM d")}, ${format(weekend.sunday, "yyyy")}`
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Your Availability</CardTitle>
        <CardDescription>
          Click on the weekends you're available for the hiking trip. Selected weekends will be highlighted.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-4">
          {weekends.map((weekend) => {
            const isAvailable = preferences.availability[weekend.formatted] || false
            return (
              <Card
                key={weekend.formatted}
                className={cn(
                  "cursor-pointer transition-colors border-2",
                  isAvailable ? "border-primary bg-primary/5" : "hover:border-muted-foreground/20",
                )}
                onClick={() => toggleAvailability(weekend.formatted)}
              >
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Calendar className="h-5 w-5 text-muted-foreground" />
                    <h3 className="text-sm font-medium">{formatWeekendDates(weekend)}</h3>
                  </div>
                  <div className="flex-shrink-0">
                    {isAvailable ? (
                      <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center">
                        <CheckCircle className="h-4 w-4 text-primary-foreground" />
                      </div>
                    ) : (
                      <Checkbox
                        id={weekend.formatted}
                        checked={isAvailable}
                        onCheckedChange={() => toggleAvailability(weekend.formatted)}
                        onClick={(e) => e.stopPropagation()}
                        className="h-6 w-6"
                      />
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {error && <p className="text-sm font-medium text-destructive">{error}</p>}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={handleSubmit} disabled={isLoading}>
          {isLoading ? "Submitting..." : "Submit"}
        </Button>
      </CardFooter>
    </Card>
  )
}
