"use server"

import { generateText } from "ai"
import { getOpenAIClient } from "./openai-config"

export async function checkOpenAICredentials() {
  try {
    console.log("Checking OpenAI credentials...")
    console.log(
      "API Key format check:",
      process.env.OPENAI_API_KEY?.substring(0, 7) + "..." + process.env.OPENAI_API_KEY?.slice(-4),
    )
    console.log("Organization ID:", process.env.OPENAI_ORG_ID)

    // Simple test to verify the credentials work
    const { text } = await generateText({
      model: getOpenAIClient("gpt-4o"),
      prompt: "Respond with 'OK' if you can read this message.",
      maxTokens: 10,
    })

    return {
      success: true,
      message: "OpenAI credentials are valid",
      response: text,
    }
  } catch (error) {
    console.error("Error checking OpenAI credentials:", error)

    // Provide more detailed error information
    let errorMessage = "Unknown error occurred"
    if (error instanceof Error) {
      errorMessage = error.message

      // Check for common error patterns
      if (errorMessage.includes("Incorrect API key")) {
        errorMessage = "Invalid API key format or key has been revoked. Please check your API key."
      } else if (errorMessage.includes("organization")) {
        errorMessage = "Organization ID issue. Please verify your organization ID is correct."
      } else if (errorMessage.includes("rate limit")) {
        errorMessage = "Rate limit exceeded. Please try again later."
      }
    }

    return {
      success: false,
      message: errorMessage,
      response: null,
    }
  }
}
