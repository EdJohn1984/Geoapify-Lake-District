import { notFound } from "next/navigation"
import { getTrip, getWeekends } from "@/lib/actions"
import { PreferenceWizard } from "@/components/preference-wizard/preference-wizard"

export default async function TripPage({ params }: { params: { token: string } }) {
  const trip = await getTrip(params.token)

  if (!trip) {
    notFound()
  }

  const weekends = await getWeekends(trip.month)

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24">
      <div className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-center">{trip.name}</h1>
        <p className="mb-6 text-center text-muted-foreground">
          Select your availability for the weekends in{" "}
          {new Date(trip.month).toLocaleDateString(undefined, { month: "long", year: "numeric" })}
        </p>
        <PreferenceWizard token={params.token} weekends={weekends} />
      </div>
    </main>
  )
}
