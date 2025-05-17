"use client"

import { useState } from "react"
import { generateItinerary, getStoredItinerary } from "./itinerary"

export function useItineraryGeneration() {
  const [isGenerating, setIsGenerating] = useState(false)
  const [itinerary, setItinerary] = useState<{
    content: string
    weekend: {
      friday: string
      saturday: string
      sunday: string
      monday: string
    }
    region: {
      id: string
      name: string
    }
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const checkForExistingItinerary = async (token: string, weekendFormatted: string, regionId: string) => {
    try {
      setIsGenerating(true)
      setError(null)

      const response = await getStoredItinerary(token, weekendFormatted, regionId)

      if (response.error) {
        setError(response.error)
        return false
      }

      if (response.exists && response.itinerary) {
        setItinerary({
          content: response.itinerary,
          weekend: response.weekend,
          region: response.region,
        })
        return true
      }

      return false
    } catch (err) {
      setError("Failed to check for existing itinerary")
      console.error(err)
      return false
    } finally {
      setIsGenerating(false)
    }
  }

  const generateNewItinerary = async (token: string, weekendFormatted: string, regionId: string) => {
    try {
      setIsGenerating(true)
      setError(null)

      // First check if we already have a stored itinerary
      const existingItinerary = await checkForExistingItinerary(token, weekendFormatted, regionId)
      if (existingItinerary) {
        return
      }

      // If not, generate a new one
      const response = await generateItinerary({
        token,
        weekendFormatted,
        regionId,
      })

      if (response.error) {
        setError(response.error)
        return
      }

      setItinerary({
        content: response.itinerary,
        weekend: response.weekend,
        region: response.region,
      })
    } catch (err) {
      setError("Failed to generate itinerary")
      console.error(err)
    } finally {
      setIsGenerating(false)
    }
  }

  return {
    isGenerating,
    itinerary,
    error,
    generateNewItinerary,
    checkForExistingItinerary,
  }
}
