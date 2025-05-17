import Link from "next/link"
import { notFound } from "next/navigation"
import { Button } from "@/components/ui/button"
import { AvailabilityResults } from "@/components/availability-results"
import { getTrip, getAttendees, getWeekends } from "@/lib/actions"

export default async function ResultsPage({ params }: { params: { token: string } }) {
  const trip = await getTrip(params.token)

  if (!trip) {
    notFound()
  }

  const attendees = await getAttendees(params.token)
  const weekends = await getWeekends(trip.month)

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24">
      <div className="w-full max-w-4xl">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold">{trip.name} - Results</h1>
          <p className="text-muted-foreground">
            Availability for {new Date(trip.month).toLocaleDateString(undefined, { month: "long", year: "numeric" })}
          </p>
        </div>

        {attendees.length === 0 ? (
          <div className="text-center p-8 border rounded-lg">
            <h2 className="text-xl font-semibold mb-4">No responses yet</h2>
            <p className="mb-6 text-muted-foreground">Share the link with your friends to collect their availability</p>
            <div className="flex justify-center">
              <Link href={`/trip/${params.token}`}>
                <Button>Add Your Availability</Button>
              </Link>
            </div>
          </div>
        ) : (
          <AvailabilityResults attendees={attendees} weekends={weekends} />
        )}

        <div className="mt-6 text-center">
          <Link href={`/trip/${params.token}`}>
            <Button variant="outline">Add Your Availability</Button>
          </Link>
        </div>
      </div>
    </main>
  )
}
