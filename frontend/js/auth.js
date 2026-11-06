import { supabase, API_URL } from "./config.js";

// REGISTER
export async function registerUser(email, password) {
    const { data, error } = await supabase.auth.signUp({
        email,
        password
    });

    if (error) {
        throw error;
    }

    return data;
}

// LOGIN
export async function loginUser(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
    });

    if (error) {
        throw error;
    }

    return data;
}

// LOGOUT
export async function logoutUser() {
    const { error } = await supabase.auth.signOut();

    if (error) {
        throw error;
    }
}

// GET CURRENT USER
export async function getCurrentUser() {
    const { data, error } = await supabase.auth.getUser();

    if (error) {
        return null;
    }

    return data.user;
}

// GET ACCESS TOKEN
export async function getAccessToken() {
    const { data, error } = await supabase.auth.getSession();

    if (error || !data.session) {
        return null;
    }

    return data.session.access_token;
}

// LOAD MY ROOM
export async function loadMyRoom() {
    const token = await getAccessToken();

    if (!token) {
        throw new Error("Please log in first.");
    }

    const response = await fetch(${API_URL}/api/my-room, {
        method: "GET",
        headers: {
            "Authorization": Bearer ${token},
            "Content-Type": "application/json"
        }
    });

    if (!response.ok) {
        const message = await response.text();
        throw new Error(Error ${response.status}: ${message});
    }

    return await response.json();
  
