"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { format } from "date-fns"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { submitAvailability } from "@/lib/actions"

interface Weekend {
  saturday: Date
  sunday: Date
  formatted: string
}

interface AvailabilityFormProps {
  token: string
  weekends: Weekend[]
}

export function AvailabilityForm({ token, weekends }: AvailabilityFormProps) {
  const router = useRouter()
  const [name, setName] = useState("")
  const [availability, setAvailability] = useState<Record<string, boolean>>(
    weekends.reduce(
      (acc, weekend) => {
        acc[weekend.formatted] = false
        return acc
      },
      {} as Record<string, boolean>,
    ),
  )
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      setError("Please enter your name")
      return
    }

    setIsLoading(true)
    setError("")

    try {
      await submitAvailability({
        token,
        name,
        availability: Object.entries(availability).map(([date, isAvailable]) => ({
          date,
          isAvailable,
        })),
      })

      router.push(`/trip/${token}/results`)
    } catch (err) {
      setError("Failed to submit availability. Please try again.")
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleAvailability = (date: string) => {
    setAvailability((prev) => ({
      ...prev,
      [date]: !prev[date],
    }))
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
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="name">Your Name</Label>
        <Input id="name" placeholder="Enter your name" value={name} onChange={(e) => setName(e.target.value)} />
      </div>

      <div className="space-y-4">
        <Label>Select weekends you're available:</Label>
        {weekends.map((weekend) => (
          <Card key={weekend.formatted}>
            <CardHeader className="p-4 pb-2">
              <h3 className="text-sm font-medium">{formatWeekendDates(weekend)}</h3>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id={weekend.formatted}
                  checked={availability[weekend.formatted]}
                  onCheckedChange={() => toggleAvailability(weekend.formatted)}
                />
                <label
                  htmlFor={weekend.formatted}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  I'm available this weekend
                </label>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {error && <p className="text-sm font-medium text-destructive">{error}</p>}

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Submitting...
          </>
        ) : (
          "Submit Availability"
        )}
      </Button>
    </form>
  )
}
