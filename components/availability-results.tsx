"use client"

import { useMemo } from "react"
import { format } from "date-fns"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { CheckCircle, XCircle, MapPin, MapIcon, Calendar } from "lucide-react"
import { getRegionNamesByIds, getRegionById } from "@/lib/destinations"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

interface Weekend {
  saturday: Date
  sunday: Date
  formatted: string
}

interface Attendee {
  id: string
  name: string
  location?: string
  availability: {
    date: string
    isAvailable: boolean
  }[]
  preferredRegions?: string[]
}

interface AvailabilityResultsProps {
  attendees: Attendee[]
  weekends: Weekend[]
}

export function AvailabilityResults({ attendees, weekends }: AvailabilityResultsProps) {
  // Format weekend dates, handling month transitions
  const formatWeekendDates = (weekend: Weekend) => {
    const satMonth = weekend.saturday.getMonth()
    const sunMonth = weekend.sunday.getMonth()

    if (satMonth === sunMonth) {
      // Same month
      return `${format(weekend.saturday, "MMMM d")} - ${format(weekend.sunday, "d")}, ${format(weekend.sunday, "yyyy")}`
    } else {
      // Different months
      return `${format(weekend.saturday, "MMMM d")} - ${format(weekend.sunday, "MMMM d")}, ${format(weekend.sunday, "yyyy")}`
    }
  }

  // Calculate the best weekend(s)
  const bestWeekends = useMemo(() => {
    // Count votes for each weekend
    const weekendCounts = weekends.map((weekend) => {
      const availableCount = attendees.filter((attendee) => {
        const availability = attendee.availability.find((a) => a.date === weekend.formatted)
        return availability?.isAvailable
      }).length

      return {
        weekend,
        count: availableCount,
        percentage: Math.round((availableCount / attendees.length) * 100),
        formattedDate: formatWeekendDates(weekend),
      }
    })

    // Filter weekends with more than one vote
    const filteredWeekends = weekendCounts.filter((w) => w.count > 1)

    if (filteredWeekends.length === 0) {
      return []
    }

    // Find the maximum vote count
    const maxCount = Math.max(...filteredWeekends.map((w) => w.count))

    // Return all weekends with the maximum vote count
    return filteredWeekends.filter((w) => w.count === maxCount)
  }, [attendees, weekends])

  // Calculate the best region(s)
  const bestRegions = useMemo(() => {
    // Skip calculation if no attendees have preferred regions
    if (!attendees.some((a) => a.preferredRegions && a.preferredRegions.length > 0)) {
      return []
    }

    // Count votes for each region using a plain object instead of Map
    const regionVotes: Record<string, number> = {}

    attendees.forEach((attendee) => {
      if (attendee.preferredRegions && attendee.preferredRegions.length > 0) {
        attendee.preferredRegions.forEach((regionId) => {
          regionVotes[regionId] = (regionVotes[regionId] || 0) + 1
        })
      }
    })

    // Convert to array and filter regions with more than one vote
    const regionCounts = Object.entries(regionVotes)
      .map(([regionId, count]) => ({
        regionId,
        count,
        percentage: Math.round((count / attendees.length) * 100),
        name: getRegionById(regionId)?.name || regionId,
      }))
      .filter((region) => region.count > 1)

    // Find the maximum vote count
    if (regionCounts.length === 0) {
      return []
    }

    const maxVotes = Math.max(...regionCounts.map((r) => r.count))

    // Return all regions with the maximum vote count
    return regionCounts.filter((r) => r.count === maxVotes)
  }, [attendees])

  // Format weekend dates for table header
  const formatWeekendShort = (weekend: Weekend) => {
    const satMonth = weekend.saturday.getMonth()
    const sunMonth = weekend.sunday.getMonth()

    if (satMonth === sunMonth) {
      // Same month
      return `${format(weekend.saturday, "MMM d")}-${format(weekend.sunday, "d")}`
    } else {
      // Different months
      return `${format(weekend.saturday, "MMM d")}-${format(weekend.sunday, "MMM d")}`
    }
  }

  // Determine if we have any consensus to show
  const hasConsensus = bestWeekends.length > 0 || bestRegions.length > 0

  return (
    <div className="space-y-6">
      {hasConsensus && (
        <Card>
          <CardHeader>
            <CardTitle>Group Consensus</CardTitle>
            <CardDescription>
              Based on everyone's preferences, here are the most popular options for your hiking trip
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {bestWeekends.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  When to Go {bestWeekends.length > 1 ? "(Tied)" : ""}
                </h3>
                {bestWeekends.map((best) => (
                  <div key={best.weekend.formatted} className="flex items-start space-x-3 p-3 bg-muted/50 rounded-md">
                    <Calendar className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                      <p className="font-medium">{best.formattedDate}</p>
                      <p className="text-sm text-muted-foreground">
                        {best.count} out of {attendees.length} people available ({best.percentage}%)
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {bestWeekends.length > 0 && bestRegions.length > 0 && <Separator />}

            {bestRegions.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Where to Go {bestRegions.length > 1 ? "(Tied)" : ""}
                </h3>
                {bestRegions.map((region) => (
                  <div key={region.regionId} className="flex items-start space-x-3 p-3 bg-muted/50 rounded-md">
                    <MapIcon className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                      <p className="font-medium">{region.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {region.count} out of {attendees.length} people selected ({region.percentage}%)
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Availability Table</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[150px]">Name</TableHead>
                <TableHead className="w-[200px]">Location</TableHead>
                <TableHead className="min-w-[200px]">Preferred Destinations</TableHead>
                {weekends.map((weekend) => (
                  <TableHead key={weekend.formatted} className="text-center">
                    {formatWeekendShort(weekend)}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {attendees.map((attendee) => (
                <TableRow key={attendee.id}>
                  <TableCell className="font-medium">{attendee.name}</TableCell>
                  <TableCell>
                    {attendee.location ? (
                      <div className="flex items-center">
                        <MapPin className="h-4 w-4 mr-1 text-muted-foreground flex-shrink-0" />
                        <span className="truncate max-w-[180px]" title={attendee.location}>
                          {attendee.location}
                        </span>
                      </div>
                    ) : (
                      <span className="text-muted-foreground italic">Not provided</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {attendee.preferredRegions && attendee.preferredRegions.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {getRegionNamesByIds(attendee.preferredRegions).map((region, index) => (
                          <Badge key={index} variant="outline" className="flex items-center">
                            <MapIcon className="h-3 w-3 mr-1" />
                            {region}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted-foreground italic">None selected</span>
                    )}
                  </TableCell>
                  {weekends.map((weekend) => {
                    const availability = attendee.availability.find((a) => a.date === weekend.formatted)
                    return (
                      <TableCell key={weekend.formatted} className="text-center">
                        {availability?.isAvailable ? (
                          <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500 mx-auto" />
                        )}
                      </TableCell>
                    )
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
