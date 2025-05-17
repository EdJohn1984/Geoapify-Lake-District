import { openai } from "@ai-sdk/openai"

// Initialize OpenAI client with organization ID
export function getOpenAIClient(model = "gpt-4o") {
  // Verify that the required environment variables are set
  if (!process.env.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY environment variable is not set")
  }

  // Validate API key format
  const apiKey = process.env.OPENAI_API_KEY
  if (!apiKey.startsWith("sk-")) {
    console.warn("Warning: OpenAI API key doesn't start with 'sk-'. This might cause authentication issues.")
  }

  // Create the OpenAI client with organization ID if available
  if (process.env.OPENAI_ORG_ID) {
    return openai(model, {
      organization: process.env.OPENAI_ORG_ID,
    })
  }

  // Fall back to just using the API key if no org ID is provided
  return openai(model)
}
