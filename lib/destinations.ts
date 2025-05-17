export interface Region {
  id: string
  name: string
}

export interface Area {
  id: string
  name: string
  regions: Region[]
}

export const destinations: Area[] = [
  {
    id: "wales",
    name: "Wales",
    regions: [
      { id: "brecon_beacons", name: "Brecon Beacons" },
      { id: "west_wales", name: "West Wales" },
      { id: "snowdonia", name: "Snowdonia" },
    ],
  },
  {
    id: "south",
    name: "South",
    regions: [
      { id: "south_downs", name: "South Downs" },
      { id: "dorset", name: "Dorset" },
      { id: "devon", name: "Devon" },
      { id: "cornwall", name: "Cornwall" },
    ],
  },
  {
    id: "north",
    name: "North",
    regions: [
      { id: "lake_district", name: "Lake District" },
      { id: "peak_district", name: "Peak District" },
    ],
  },
  {
    id: "scotland",
    name: "Scotland",
    regions: [
      { id: "isle_of_skye", name: "Isle of Skye" },
      { id: "loch_lomond", name: "Loch Lomond" },
    ],
  },
  {
    id: "europe",
    name: "Europe",
    regions: [
      { id: "maderia", name: "Maderia" },
      { id: "alps", name: "Alps" },
      { id: "sweden", name: "Sweden" },
      { id: "spain", name: "Spain" },
    ],
  },
]

// Helper function to get all regions as a flat array
export function getAllRegions(): Region[] {
  return destinations.flatMap((area) => area.regions)
}

// Helper function to get region by ID
export function getRegionById(regionId: string): Region | undefined {
  return getAllRegions().find((region) => region.id === regionId)
}

// Helper function to get region names from region IDs
export function getRegionNamesByIds(regionIds: string[]): string[] {
  return regionIds
    .map((id) => {
      const region = getRegionById(id)
      return region ? region.name : null
    })
    .filter((name): name is string => name !== null)
}
