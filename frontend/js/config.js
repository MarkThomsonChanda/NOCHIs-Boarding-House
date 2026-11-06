// ======================================
// NOCHIs BOARDING HOUSE CONFIGURATION
// ======================================

// SUPABASE CONNECTION
const SUPABASE_URL = "https://eshxmvgbsjusohpmuesb.supabase.co";

const SUPABASE_ANON_KEY = "sb_publishable_8a2VYT2RoH4PPCR8R9IJCA_JZFhSa2J";

// INITIALIZE SUPABASE
const supabaseClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
);

// RENDER BACKEND CONNECTION
const API_URL = "https://nochis-boarding-house.onrender.com";

// ======================================
// END CONFIGURATION
// ======================================
