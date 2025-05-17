"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { format, addMonths } from "date-fns"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { createTrip } from "@/lib/actions"

export function CreateTripForm() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [tripName, setTripName] = useState("")
  const [month, setMonth] = useState<Date | undefined>(undefined)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!tripName.trim()) {
      setError("Please enter a trip name")
      return
    }

    if (!month) {
      setError("Please select a month")
      return
    }

    setIsLoading(true)
    setError("")

    try {
      const token = await createTrip({
        name: tripName,
        month: month,
      })

      router.push(`/success?token=${token}`)
    } catch (err) {
      setError("Failed to create trip. Please try again.")
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="tripName">Trip Name</Label>
        <Input
          id="tripName"
          placeholder="Summer Hiking Trip"
          value={tripName}
          onChange={(e) => setTripName(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="month">Select Month</Label>
        <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
          {Array.from({ length: 12 }, (_, i) => {
            const date = addMonths(new Date(new Date().setDate(1)), i)
            return (
              <Button
                key={i}
                type="button"
                variant={
                  month && month.getMonth() === date.getMonth() && month.getFullYear() === date.getFullYear()
                    ? "default"
                    : "outline"
                }
                className={cn(
                  "h-auto py-3 px-2 justify-center",
                  month && month.getMonth() === date.getMonth() && month.getFullYear() === date.getFullYear()
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent hover:text-accent-foreground",
                )}
                onClick={() => setMonth(date)}
              >
                <span className="text-sm font-medium">{format(date, "MMM yyyy")}</span>
              </Button>
            )
          })}
        </div>
      </div>

      {error && <p className="text-sm font-medium text-destructive">{error}</p>}

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating...
          </>
        ) : (
          "Create Trip"
        )}
      </Button>
    </form>
  )
}
