import { CreateTripForm } from "@/components/create-trip-form"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24">
      <div className="w-full max-w-md">
        <h1 className="mb-6 text-3xl font-bold text-center">Hiking Trip Organizer</h1>
        <p className="mb-8 text-center text-muted-foreground">
          Plan your next adventure with friends - no login required
        </p>
        <CreateTripForm />
      </div>
    </main>
  )
}
