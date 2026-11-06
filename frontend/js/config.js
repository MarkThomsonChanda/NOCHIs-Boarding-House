const API_BASE = "https://nochis-boarding-house.onrender.com";

const OWNER_CONTACTS = ["0977 204 572", "0979 324 363"];

async function getToken() {
    const { data, error } = await supabaseClient.auth.getSession();

    if (error || !data.session) {
        localStorage.removeItem("nochis_access_token");
        throw new Error("Your login session has expired. Please log in again.");
    }

    let session = data.session;

    if (session.expires_at * 1000 < Date.now() + 60000) {
        const refreshed = await supabaseClient.auth.refreshSession();

        if (refreshed.error || !refreshed.data.session) {
            localStorage.removeItem("nochis_access_token");
            throw new Error("Session expired. Please log in again.");
        }

        session = refreshed.data.session;
    }

    localStorage.setItem("nochis_access_token", session.access_token);

    return session.access_token;
}

async function api(path, options = {}) {
    const token = await getToken();

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
        "Authorization": Bearer ${token}
    };

    const response = await fetch(${API_BASE}${path}, {
        ...options,
        headers
    });

    const data = await response.json().catch(() => ({
        detail: "Unexpected server response"
    }));

    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}
