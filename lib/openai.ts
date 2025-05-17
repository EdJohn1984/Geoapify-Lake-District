import { generateText } from "ai"
import { getOpenAIClient } from "./openai-config"
import { getRegionById } from "./destinations"

// Define types for the itinerary generation
interface ItineraryGenerationParams {
  weekend: {
    startDate: Date // Friday
    endDate: Date // Monday
  }
  regionId: string
  attendees: {
    name: string
    location?: string
  }[]
}

interface ItineraryResponse {
  itinerary: string
  error?: string
}

/**
 * Generates a hiking itinerary using OpenAI
 */
export async function generateHikingItinerary({
  weekend,
  regionId,
  attendees,
}: ItineraryGenerationParams): Promise<ItineraryResponse> {
  try {
    // Get region details
    const region = getRegionById(regionId)
    if (!region) {
      return {
        itinerary: "",
        error: `Region with ID ${regionId} not found`,
      }
    }

    // Format dates for the prompt
    const formatDate = (date: Date) =>
      date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
      })

    const fridayDate = formatDate(weekend.startDate)
    const mondayDate = formatDate(weekend.endDate)

    // Format attendees information
    const attendeesList = attendees
      .map((attendee) => {
        if (attendee.location) {
          return `- ${attendee.name} traveling from ${attendee.location}`
        }
        return `- ${attendee.name} (starting location not provided)`
      })
      .join("\n")

    // Construct the prompt
    const prompt = `
Generate a detailed 4-day hiking weekend itinerary for ${region.name} from ${fridayDate} to ${mondayDate}.

Group Information:
${attendeesList}

Please include:
1. Personalized travel recommendations for each attendee (arrival on Friday and departure on Monday)
2. Day-by-day hiking trail recommendations with difficulty levels and approximate hiking times
3. Points of interest along each trail
4. Meal and accommodation suggestions
5. Contingency plans for weather issues

Format the itinerary as follows:

# ${region.name} Hiking Weekend: ${fridayDate} - ${mondayDate}

## Travel Logistics

[Provide personalized travel recommendations for each attendee, including estimated travel times, suggested routes, and transportation options]

## Day 1 (Friday): Arrival Day

[Provide recommendations for arrival day activities, including evening plans and accommodation]

## Day 2 (Saturday): First Hiking Day

[Provide detailed hiking trail recommendations, including:
- Trail name and difficulty level
- Approximate hiking time and distance
- Points of interest along the trail
- Meal suggestions
- Evening activities]

## Day 3 (Sunday): Second Hiking Day

[Provide detailed hiking trail recommendations, following the same format as Day 2]

## Day 4 (Monday): Departure Day

[Provide recommendations for morning activities before departure and travel logistics]

## Additional Recommendations

[Provide any additional recommendations, such as:
- Alternative activities in case of bad weather
- Nearby attractions
- Equipment suggestions specific to this region]

Please ensure the itinerary is realistic, taking into account the travel distances from each attendee's starting location and the hiking difficulty appropriate for a group.
`

    // Call OpenAI API
    const { text } = await generateText({
      model: getOpenAIClient("gpt-4o"),
      prompt,
      temperature: 0.7,
      maxTokens: 2500,
    })

    return {
      itinerary: text,
    }
  } catch (error) {
    console.error("Error generating itinerary:", error)
    return {
      itinerary: "",
      error: error instanceof Error ? error.message : "Unknown error occurred while generating itinerary",
    }
  }
}
