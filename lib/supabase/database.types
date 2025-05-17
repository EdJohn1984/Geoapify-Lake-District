export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]

export interface Database {
  public: {
    Tables: {
      trips: {
        Row: {
          id: string
          name: string
          month: string
          access_token: string
          created_at: string
        }
        Insert: {
          id?: string
          name: string
          month: string
          access_token: string
          created_at?: string
        }
        Update: {
          id?: string
          name?: string
          month?: string
          access_token?: string
          created_at?: string
        }
      }
      attendees: {
        Row: {
          id: string
          trip_id: string
          name: string
          location?: string
          created_at: string
        }
        Insert: {
          id?: string
          trip_id: string
          name: string
          location?: string
          created_at?: string
        }
        Update: {
          id?: string
          trip_id?: string
          name?: string
          location?: string
          created_at?: string
        }
      }
      availability: {
        Row: {
          id: string
          attendee_id: string
          weekend_date: string
          is_available: boolean
          created_at: string
        }
        Insert: {
          id?: string
          attendee_id: string
          weekend_date: string
          is_available: boolean
          created_at?: string
        }
        Update: {
          id?: string
          attendee_id?: string
          weekend_date?: string
          is_available?: boolean
          created_at?: string
        }
      }
      preferred_regions: {
        Row: {
          id: string
          attendee_id: string
          region: string
          created_at: string
        }
        Insert: {
          id?: string
          attendee_id: string
          region: string
          created_at?: string
        }
        Update: {
          id?: string
          attendee_id?: string
          region?: string
          created_at?: string
        }
      }
      trip_itineraries: {
        Row: {
          id: string
          trip_id: string
          weekend_date: string
          region_id: string
          content: string
          created_at: string
        }
        Insert: {
          id?: string
          trip_id: string
          weekend_date: string
          region_id: string
          content: string
          created_at?: string
        }
        Update: {
          id?: string
          trip_id?: string
          weekend_date?: string
          region_id?: string
          content?: string
          created_at?: string
        }
      }
    }
  }
}
