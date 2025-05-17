"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Check, Copy, Share2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

export default function SuccessPage() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")
  const [copied, setCopied] = useState(false)
  const [shareSupported, setShareSupported] = useState(false)

  const tripUrl = token ? `${window.location.origin}/trip/${token}` : ""

  useEffect(() => {
    setShareSupported(!!navigator.share)
  }, [])

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(tripUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy: ", err)
    }
  }

  const shareLink = async () => {
    try {
      await navigator.share({
        title: "Join my hiking trip",
        text: "Please select your availability for our hiking trip!",
        url: tripUrl,
      })
    } catch (err) {
      console.error("Error sharing: ", err)
    }
  }

  if (!token) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Invalid Link</CardTitle>
            <CardDescription>This link appears to be invalid or expired.</CardDescription>
          </CardHeader>
          <CardFooter>
            <Link href="/" className="w-full">
              <Button className="w-full">Create New Trip</Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Trip Created!</CardTitle>
          <CardDescription>Share this link with your friends to plan your hiking trip</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <div className="rounded-md border px-3 py-2 text-sm font-medium w-full truncate">{tripUrl}</div>
            <Button size="icon" variant="outline" onClick={copyToClipboard}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-2">
          <Button className="w-full" onClick={copyToClipboard}>
            {copied ? "Copied!" : "Copy Link"}
          </Button>

          {shareSupported && (
            <Button variant="outline" className="w-full" onClick={shareLink}>
              <Share2 className="mr-2 h-4 w-4" />
              Share
            </Button>
          )}

          <Link href={`/trip/${token}`} className="w-full">
            <Button variant="secondary" className="w-full">
              View Trip Page
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}
