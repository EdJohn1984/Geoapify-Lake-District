"use server"

import { revalidatePath } from "next/cache"
import { createServerClient } from "../supabase/server"
import { generateHikingItinerary } from "../openai"
import { getRegionById } from "../destinations"

interface GenerateItineraryParams {
  token: string
  weekendFormatted: string
  regionId: string
}

export async function generateItinerary({ token, weekendFormatted, regionId }: GenerateItineraryParams) {
  try {
    const supabase = createServerClient()

    // Get the trip
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("id")
      .eq("access_token", token)
      .single()

    if (tripError) {
      console.error("Error fetching trip:", tripError)
      return { error: "Trip not found" }
    }

    // Get all attendees for this trip
    const { data: attendees, error: attendeesError } = await supabase
      .from("attendees")
      .select("id, name, location")
      .eq("trip_id", trip.id)

    if (attendeesError) {
      console.error("Error fetching attendees:", attendeesError)
      return { error: "Failed to fetch attendees" }
    }

    // Get the weekend dates
    // The weekendFormatted is in YYYY-MM-DD format for Saturday
    const saturdayDate = new Date(weekendFormatted)

    // Calculate Friday (day before) and Monday (2 days after)
    const fridayDate = new Date(saturdayDate)
    fridayDate.setDate(saturdayDate.getDate() - 1)

    const sundayDate = new Date(saturdayDate)
    sundayDate.setDate(saturdayDate.getDate() + 1)

    const mondayDate = new Date(saturdayDate)
    mondayDate.setDate(saturdayDate.getDate() + 2)

    // Generate the itinerary
    const itineraryResponse = await generateHikingItinerary({
      weekend: {
        startDate: fridayDate,
        endDate: mondayDate,
      },
      regionId,
      attendees: attendees.map((attendee) => ({
        name: attendee.name,
        location: attendee.location || undefined,
      })),
    })

    if (itineraryResponse.error) {
      return { error: itineraryResponse.error }
    }

    // Store the generated itinerary in the database
    const { data: itineraryData, error: itineraryError } = await supabase
      .from("trip_itineraries")
      .upsert({
        trip_id: trip.id,
        weekend_date: weekendFormatted,
        region_id: regionId,
        content: itineraryResponse.itinerary,
        created_at: new Date().toISOString(),
      })
      .select()

    if (itineraryError) {
      console.error("Error storing itinerary:", itineraryError)
      // We'll still return the itinerary even if storing fails
    }

    // Get the region name
    const region = getRegionById(regionId)
    const regionName = region ? region.name : regionId

    revalidatePath(`/trip/${token}/results`)

    return {
      itinerary: itineraryResponse.itinerary,
      weekend: {
        friday: fridayDate.toISOString(),
        saturday: saturdayDate.toISOString(),
        sunday: sundayDate.toISOString(),
        monday: mondayDate.toISOString(),
      },
      region: {
        id: regionId,
        name: regionName,
      },
    }
  } catch (error) {
    console.error("Unexpected error generating itinerary:", error)
    return {
      error: "Failed to generate itinerary. Please try again.",
    }
  }
}

export async function getStoredItinerary(token: string, weekendFormatted: string, regionId: string) {
  try {
    const supabase = createServerClient()

    // Get the trip
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("id")
      .eq("access_token", token)
      .single()

    if (tripError) {
      console.error("Error fetching trip:", tripError)
      return { error: "Trip not found" }
    }

    // Check if we already have a stored itinerary
    const { data: itinerary, error: itineraryError } = await supabase
      .from("trip_itineraries")
      .select("content, created_at")
      .eq("trip_id", trip.id)
      .eq("weekend_date", weekendFormatted)
      .eq("region_id", regionId)
      .order("created_at", { ascending: false })
      .limit(1)
      .single()

    if (itineraryError) {
      if (itineraryError.code === "PGRST116") {
        // No itinerary found
        return { exists: false }
      }
      console.error("Error fetching itinerary:", itineraryError)
      return { error: "Failed to check for existing itinerary" }
    }

    // Get the region name
    const region = getRegionById(regionId)
    const regionName = region ? region.name : regionId

    // Calculate the dates
    const saturdayDate = new Date(weekendFormatted)

    const fridayDate = new Date(saturdayDate)
    fridayDate.setDate(saturdayDate.getDate() - 1)

    const sundayDate = new Date(saturdayDate)
    sundayDate.setDate(saturdayDate.getDate() + 1)

    const mondayDate = new Date(saturdayDate)
    mondayDate.setDate(saturdayDate.getDate() + 2)

    return {
      exists: true,
      itinerary: itinerary.content,
      createdAt: itinerary.created_at,
      weekend: {
        friday: fridayDate.toISOString(),
        saturday: saturdayDate.toISOString(),
        sunday: sundayDate.toISOString(),
        monday: mondayDate.toISOString(),
      },
      region: {
        id: regionId,
        name: regionName,
      },
    }
  } catch (error) {
    console.error("Unexpected error checking for itinerary:", error)
    return {
      error: "Failed to check for existing itinerary",
    }
  }
}
