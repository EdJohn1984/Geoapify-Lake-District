import type { Weekend } from "@/components/preference-wizard/types"

interface ConsensusData {
  bestWeekends: {
    weekend: Weekend
    count: number
    percentage: number
    formattedDate: string
  }[]
  bestRegions: {
    regionId: string
    count: number
    percentage: number
    name: string
  }[]
}

export function canGenerateItinerary(consensusData: ConsensusData): boolean {
  // We need at least one best weekend and one best region to generate an itinerary
  return consensusData.bestWeekends.length > 0 && consensusData.bestRegions.length > 0
}

export function getItineraryParams(consensusData: ConsensusData) {
  // If there are multiple best weekends or regions, we'll use the first one
  const bestWeekend = consensusData.bestWeekends[0]
  const bestRegion = consensusData.bestRegions[0]

  if (!bestWeekend || !bestRegion) {
    return null
  }

  return {
    weekendFormatted: bestWeekend.weekend.formatted,
    regionId: bestRegion.regionId,
  }
}

// Format the itinerary content for display
export function formatItineraryContent(content: string): string {
  // The content is already in Markdown format from the OpenAI response
  // We could do additional formatting here if needed
  return content
}
