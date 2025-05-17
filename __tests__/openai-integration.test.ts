import { generateHikingItinerary } from "../lib/openai"

describe("OpenAI Integration", () => {
  // This test will only run if the environment variables are set
  // and you explicitly enable it by changing "skip" to "test"
  it.skip("should generate an itinerary using the GPT-4o model", async () => {
    const result = await generateHikingItinerary({
      weekend: {
        startDate: new Date("2023-07-14"), // Friday
        endDate: new Date("2023-07-17"), // Monday
      },
      regionId: "lake_district",
      attendees: [
        { name: "John", location: "London" },
        { name: "Jane", location: "Manchester" },
      ],
    })

    // Check that we got a valid response
    expect(result.itinerary).toBeTruthy()
    expect(result.itinerary.length).toBeGreaterThan(100)
    expect(result.error).toBeUndefined()

    // Log the first 100 characters of the itinerary for manual verification
    console.log("Itinerary preview:", result.itinerary.substring(0, 100) + "...")
  }, 30000) // Allow 30 seconds for the API call
})
