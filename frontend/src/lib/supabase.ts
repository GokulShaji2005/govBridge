import { createClient } from "@supabase/supabase-js";

// Supabase URL & Public Anon Key from Environment Variables or Default Demo Project
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://demo-govbridge.supabase.co";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRlbW8iLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY3MjUxMjAwMCwiZXhwIjoyMDE4MDg4MDAwfQ.demo-key-govbridge";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
