"use server"

import { revalidatePath } from "next/cache"
import { v4 as uuidv4 } from "uuid"
import { createServerClient } from "./supabase/server"

export async function createTrip({ name, month }: { name: string; month: Date }) {
  try {
    const supabase = createServerClient()
    const token = uuidv4()

    const { data, error } = await supabase
      .from("trips")
      .insert({
        name,
        month: month.toISOString().split("T")[0], // Format as YYYY-MM-DD for PostgreSQL date
        access_token: token,
      })
      .select()

    if (error) {
      console.error("Error creating trip:", error)
      throw new Error(`Failed to create trip: ${error.message}`)
    }

    return token
  } catch (err) {
    console.error("Unexpected error creating trip:", err)
    throw new Error("Failed to create trip. Please try again.")
  }
}

export async function getTrip(token: string) {
  try {
    const supabase = createServerClient()

    const { data, error } = await supabase.from("trips").select("*").eq("access_token", token).single()

    if (error) {
      if (error.code === "PGRST116") {
        // No rows returned
        return null
      }
      console.error("Error fetching trip:", error)
      throw new Error(`Failed to fetch trip: ${error.message}`)
    }

    return data
  } catch (err) {
    console.error("Unexpected error fetching trip:", err)
    return null
  }
}

export async function getAttendees(token: string) {
  try {
    const supabase = createServerClient()

    // First get the trip ID
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("id")
      .eq("access_token", token)
      .single()

    if (tripError) {
      console.error("Error fetching trip for attendees:", tripError)
      return []
    }

    if (!trip) {
      return []
    }

    // Get all attendees for this trip
    const { data: attendeesData, error: attendeesError } = await supabase
      .from("attendees")
      .select(`
        id,
        name,
        location,
        created_at
      `)
      .eq("trip_id", trip.id)

    if (attendeesError) {
      console.error("Error fetching attendees:", attendeesError)
      return []
    }

    // For each attendee, get their availability and preferred regions
    const attendeesWithPreferences = await Promise.all(
      attendeesData.map(async (attendee) => {
        // Get availability
        const { data: availabilityData, error: availabilityError } = await supabase
          .from("availability")
          .select("weekend_date, is_available")
          .eq("attendee_id", attendee.id)

        if (availabilityError) {
          console.error(`Error fetching availability for attendee ${attendee.id}:`, availabilityError)
          return {
            ...attendee,
            availability: [],
            preferredRegions: [],
          }
        }

        // Get preferred regions
        const { data: regionsData, error: regionsError } = await supabase
          .from("preferred_regions")
          .select("region")
          .eq("attendee_id", attendee.id)

        if (regionsError) {
          console.error(`Error fetching preferred regions for attendee ${attendee.id}:`, regionsError)
          return {
            ...attendee,
            availability: availabilityData.map((item) => ({
              date: item.weekend_date,
              isAvailable: item.is_available,
            })),
            preferredRegions: [],
          }
        }

        return {
          ...attendee,
          availability: availabilityData.map((item) => ({
            date: item.weekend_date,
            isAvailable: item.is_available,
          })),
          preferredRegions: regionsData.map((item) => item.region),
        }
      }),
    )

    return attendeesWithPreferences
  } catch (err) {
    console.error("Unexpected error fetching attendees:", err)
    return []
  }
}

export async function submitPreferences({
  token,
  name,
  location,
  selectedRegions,
  availability,
}: {
  token: string
  name: string
  location: string
  selectedRegions: string[]
  availability: { date: string; isAvailable: boolean }[]
}) {
  try {
    const supabase = createServerClient()

    // First get the trip ID
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("id")
      .eq("access_token", token)
      .single()

    if (tripError) {
      console.error("Error fetching trip for preferences submission:", tripError)
      throw new Error("Trip not found")
    }

    // Sanitize location input (optional)
    const sanitizedLocation = location ? location.trim() : ""

    // Check if this person already submitted (by name)
    const { data: existingAttendee, error: attendeeError } = await supabase
      .from("attendees")
      .select("id")
      .eq("trip_id", trip.id)
      .eq("name", name)
      .maybeSingle()

    let attendeeId: string

    if (existingAttendee) {
      // Update existing attendee
      attendeeId = existingAttendee.id

      // Update location
      const { error: updateError } = await supabase
        .from("attendees")
        .update({ location: sanitizedLocation })
        .eq("id", attendeeId)

      if (updateError) {
        console.error("Error updating attendee location:", updateError)
        throw new Error("Failed to update attendee information")
      }

      // Delete existing availability entries
      const { error: deleteAvailError } = await supabase.from("availability").delete().eq("attendee_id", attendeeId)

      if (deleteAvailError) {
        console.error("Error deleting existing availability:", deleteAvailError)
        throw new Error("Failed to update availability")
      }

      // Delete existing preferred regions
      const { error: deleteRegionsError } = await supabase
        .from("preferred_regions")
        .delete()
        .eq("attendee_id", attendeeId)

      if (deleteRegionsError) {
        console.error("Error deleting existing preferred regions:", deleteRegionsError)
        throw new Error("Failed to update preferred regions")
      }
    } else {
      // Create new attendee with location
      const { data: newAttendee, error: createError } = await supabase
        .from("attendees")
        .insert({
          trip_id: trip.id,
          name,
          location: sanitizedLocation,
        })
        .select("id")
        .single()

      if (createError) {
        console.error("Error creating attendee:", createError)
        throw new Error("Failed to create attendee")
      }

      attendeeId = newAttendee.id
    }

    // Insert availability entries
    const availabilityRecords = availability.map((item) => ({
      attendee_id: attendeeId,
      weekend_date: item.date,
      is_available: item.isAvailable,
    }))

    const { error: availabilityError } = await supabase.from("availability").insert(availabilityRecords)

    if (availabilityError) {
      console.error("Error inserting availability:", availabilityError)
      throw new Error("Failed to save availability")
    }

    // Insert preferred regions
    if (selectedRegions && selectedRegions.length > 0) {
      const regionRecords = selectedRegions.map((region) => ({
        attendee_id: attendeeId,
        region: region,
      }))

      const { error: regionsError } = await supabase.from("preferred_regions").insert(regionRecords)

      if (regionsError) {
        console.error("Error inserting preferred regions:", regionsError)
        throw new Error("Failed to save preferred regions")
      }
    }

    revalidatePath(`/trip/${token}/results`)

    return attendeeId
  } catch (err) {
    console.error("Unexpected error submitting preferences:", err)
    throw new Error("Failed to submit preferences. Please try again.")
  }
}

// Keep the existing functions
export async function submitAvailability({
  token,
  name,
  availability,
}: {
  token: string
  name: string
  availability: { date: string; isAvailable: boolean }[]
}) {
  try {
    const supabase = createServerClient()

    // First get the trip ID
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("id")
      .eq("access_token", token)
      .single()

    if (tripError) {
      console.error("Error fetching trip for availability submission:", tripError)
      throw new Error("Trip not found")
    }

    // Check if this person already submitted (by name)
    const { data: existingAttendee, error: attendeeError } = await supabase
      .from("attendees")
      .select("id")
      .eq("trip_id", trip.id)
      .eq("name", name)
      .maybeSingle()

    let attendeeId: string

    if (existingAttendee) {
      // Update existing attendee
      attendeeId = existingAttendee.id

      // Delete existing availability entries
      const { error: deleteError } = await supabase.from("availability").delete().eq("attendee_id", attendeeId)

      if (deleteError) {
        console.error("Error deleting existing availability:", deleteError)
        throw new Error("Failed to update availability")
      }
    } else {
      // Create new attendee
      const { data: newAttendee, error: createError } = await supabase
        .from("attendees")
        .insert({
          trip_id: trip.id,
          name,
        })
        .select("id")
        .single()

      if (createError) {
        console.error("Error creating attendee:", createError)
        throw new Error("Failed to create attendee")
      }

      attendeeId = newAttendee.id
    }

    // Insert availability entries
    const availabilityRecords = availability.map((item) => ({
      attendee_id: attendeeId,
      weekend_date: item.date,
      is_available: item.isAvailable,
    }))

    const { error: availabilityError } = await supabase.from("availability").insert(availabilityRecords)

    if (availabilityError) {
      console.error("Error inserting availability:", availabilityError)
      throw new Error("Failed to save availability")
    }

    revalidatePath(`/trip/${token}/results`)

    return attendeeId
  } catch (err) {
    console.error("Unexpected error submitting availability:", err)
    throw new Error("Failed to submit availability. Please try again.")
  }
}

export async function submitAvailabilityWithLocation({
  token,
  name,
  location,
  availability,
}: {
  token: string
  name: string
  location: string
  availability: { date: string; isAvailable: boolean }[]
}) {
  try {
    const supabase = createServerClient()

    // First get the trip ID
    const { data: trip, error: tripError } = await supabase
      .from("trips")
      .select("id")
      .eq("access_token", token)
      .single()

    if (tripError) {
      console.error("Error fetching trip for availability submission:", tripError)
      throw new Error("Trip not found")
    }

    // Sanitize location input (optional)
    const sanitizedLocation = location ? location.trim() : ""

    // Check if this person already submitted (by name)
    const { data: existingAttendee, error: attendeeError } = await supabase
      .from("attendees")
      .select("id")
      .eq("trip_id", trip.id)
      .eq("name", name)
      .maybeSingle()

    let attendeeId: string

    if (existingAttendee) {
      // Update existing attendee
      attendeeId = existingAttendee.id

      // Update location
      const { error: updateError } = await supabase
        .from("attendees")
        .update({ location: sanitizedLocation })
        .eq("id", attendeeId)

      if (updateError) {
        console.error("Error updating attendee location:", updateError)
        throw new Error("Failed to update attendee information")
      }

      // Delete existing availability entries
      const { error: deleteError } = await supabase.from("availability").delete().eq("attendee_id", attendeeId)

      if (deleteError) {
        console.error("Error deleting existing availability:", deleteError)
        throw new Error("Failed to update availability")
      }
    } else {
      // Create new attendee with location
      const { data: newAttendee, error: createError } = await supabase
        .from("attendees")
        .insert({
          trip_id: trip.id,
          name,
          location: sanitizedLocation,
        })
        .select("id")
        .single()

      if (createError) {
        console.error("Error creating attendee:", createError)
        throw new Error("Failed to create attendee")
      }

      attendeeId = newAttendee.id
    }

    // Insert availability entries
    const availabilityRecords = availability.map((item) => ({
      attendee_id: attendeeId,
      weekend_date: item.date,
      is_available: item.isAvailable,
    }))

    const { error: availabilityError } = await supabase.from("availability").insert(availabilityRecords)

    if (availabilityError) {
      console.error("Error inserting availability:", availabilityError)
      throw new Error("Failed to save availability")
    }

    revalidatePath(`/trip/${token}/results`)

    return attendeeId
  } catch (err) {
    console.error("Unexpected error submitting availability:", err)
    throw new Error("Failed to submit availability. Please try again.")
  }
}

// Helper function to get weekends for a month
export async function getWeekends(monthStr: string) {
  const month = new Date(monthStr)
  const year = month.getFullYear()
  const monthIndex = month.getMonth()

  // Get all days in the month
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate()

  // Find all weekends (Saturday and Sunday pairs)
  const weekends = []
  let currentWeekend = null

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, monthIndex, day)
    const dayOfWeek = date.getDay()

    // 6 is Saturday, 0 is Sunday
    if (dayOfWeek === 6) {
      // Start of a weekend (Saturday)
      currentWeekend = {
        saturday: new Date(date),
        formatted: date.toISOString().split("T")[0],
      }
    } else if (dayOfWeek === 0 && currentWeekend) {
      // Complete the weekend with Sunday
      currentWeekend.sunday = new Date(date)
      weekends.push(currentWeekend)
      currentWeekend = null
    }
  }

  // Handle month boundary: if the last day of the month is a Saturday,
  // include the Sunday from the next month
  if (currentWeekend) {
    const lastSaturday = currentWeekend.saturday
    const firstSundayNextMonth = new Date(lastSaturday)
    firstSundayNextMonth.setDate(lastSaturday.getDate() + 1)
    currentWeekend.sunday = firstSundayNextMonth
    weekends.push(currentWeekend)
  }

  // Handle month boundary: if the first day of the month is a Sunday,
  // include it as part of a weekend with the Saturday from the previous month
  const firstDay = new Date(year, monthIndex, 1)
  if (firstDay.getDay() === 0) {
    const lastSaturdayPrevMonth = new Date(firstDay)
    lastSaturdayPrevMonth.setDate(lastSaturdayPrevMonth.getDate() - 1)
    weekends.unshift({
      saturday: lastSaturdayPrevMonth,
      sunday: new Date(firstDay),
      formatted: lastSaturdayPrevMonth.toISOString().split("T")[0],
    })
  }

  return weekends
}
