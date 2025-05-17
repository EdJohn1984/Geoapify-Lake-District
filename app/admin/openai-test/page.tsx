"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { checkOpenAICredentials } from "@/lib/check-openai-credentials"
import { Loader2, CheckCircle, XCircle, AlertCircle } from "lucide-react"

export default function OpenAITestPage() {
  const [isChecking, setIsChecking] = useState(false)
  const [result, setResult] = useState<{
    success: boolean
    message: string
    response: string | null
  } | null>(null)

  const handleCheckCredentials = async () => {
    setIsChecking(true)
    try {
      const checkResult = await checkOpenAICredentials()
      setResult(checkResult)
    } catch (error) {
      setResult({
        success: false,
        message: error instanceof Error ? error.message : "Unknown error occurred",
        response: null,
      })
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>OpenAI Integration Test</CardTitle>
          <CardDescription>Verify that your OpenAI credentials are working correctly</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 rounded-md bg-yellow-50 border border-yellow-200">
            <div className="flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <p className="text-sm text-yellow-700">
                  Make sure your OpenAI API key starts with <code className="bg-yellow-100 px-1 rounded">sk-</code> and
                  your Organization ID starts with <code className="bg-yellow-100 px-1 rounded">org-</code>.
                </p>
                <p className="text-xs text-yellow-600 mt-1">
                  Environment variables must be set in your Vercel project settings or .env.local file.
                </p>
              </div>
            </div>
          </div>

          {result && (
            <div
              className={`p-4 rounded-md ${result.success ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}
            >
              <div className="flex items-center space-x-2">
                {result.success ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                <span className={result.success ? "text-green-700" : "text-red-700"}>{result.message}</span>
              </div>
              {result.response && (
                <div className="mt-2 p-2 bg-white rounded border">
                  <p className="text-sm font-mono">{result.response}</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Button onClick={handleCheckCredentials} disabled={isChecking} className="w-full">
            {isChecking ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Checking...
              </>
            ) : (
              "Check OpenAI Credentials"
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
