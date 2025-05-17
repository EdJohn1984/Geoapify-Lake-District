"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { destinations } from "@/lib/destinations"
import type { WizardStepProps } from "./types"
import { Badge } from "@/components/ui/badge"
import { MapPin } from "lucide-react"

export function DestinationStep({ preferences, updatePreferences, onNext, onBack }: WizardStepProps) {
  const [errors, setErrors] = useState<{ destinations?: string }>({})

  // Get the count of selected regions
  const selectedCount = (preferences.selectedRegions || []).length

  const toggleRegion = (regionId: string) => {
    const currentSelected = [...(preferences.selectedRegions || [])]

    if (currentSelected.includes(regionId)) {
      // Remove region if already selected
      updatePreferences({
        selectedRegions: currentSelected.filter((id) => id !== regionId),
      })
    } else {
      // Add region if not selected
      updatePreferences({
        selectedRegions: [...currentSelected, regionId],
      })
    }
  }

  const handleNext = () => {
    // Validation is optional - we could allow users to proceed without selecting destinations
    onNext()
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Preferred Destinations</CardTitle>
          <Badge variant={selectedCount > 0 ? "default" : "outline"} className="ml-2">
            <MapPin className="h-3.5 w-3.5 mr-1" />
            {selectedCount} {selectedCount === 1 ? "region" : "regions"} selected
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-muted-foreground mb-2">
          Select the regions you'd like to hike in. You can choose multiple options.
        </p>

        {destinations.map((area) => (
          <div key={area.id} className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-base border-b pb-2">{area.name}</h3>
              <span className="text-xs text-muted-foreground">
                {
                  (preferences.selectedRegions || []).filter((id) => area.regions.some((region) => region.id === id))
                    .length
                }{" "}
                of {area.regions.length} selected
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 pl-1">
              {area.regions.map((region) => (
                <div key={region.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={region.id}
                    checked={(preferences.selectedRegions || []).includes(region.id)}
                    onCheckedChange={() => toggleRegion(region.id)}
                  />
                  <label
                    htmlFor={region.id}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {region.name}
                  </label>
                </div>
              ))}
            </div>
          </div>
        ))}

        {errors.destinations && <p className="text-sm text-destructive">{errors.destinations}</p>}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={handleNext}>Next</Button>
      </CardFooter>
    </Card>
  )
}
