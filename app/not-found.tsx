import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">404</h1>
        <h2 className="text-2xl font-semibold">Trip Not Found</h2>
        <p className="text-muted-foreground">The trip you're looking for doesn't exist or has been removed.</p>
        <Link href="/">
          <Button>Create New Trip</Button>
        </Link>
      </div>
    </div>
  )
}
