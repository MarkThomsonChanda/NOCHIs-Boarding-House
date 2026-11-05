const SUPABASE_URL = "https://eshxmvgbsjusohpmuesb.supabase.co";

const SUPABASE_ANON_KEY = "sb_publishable_8a2VYT2RoH4PPCR8R9IJCA_JZFhSa2J";

const supabaseClient = window.supabase.createClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
);

async function registerUser(email, password, fullName) {
    const { data, error } = await supabaseClient.auth.signUp({
        email: email,
        password: password,
        options: {
            data: {
                full_name: fullName
            }
        }
    });

    if (error) throw error;
    return data;
}

async function loginUser(email, password) {
    const { data, error } = await supabaseClient.auth.signInWithPassword({
        email: email,
        password: password
    });

    if (error) throw error;

    localStorage.setItem(
        "nochis_access_token",
        data.session.access_token
    );

    return data;
}

async function logoutUser() {
    await supabaseClient.auth.signOut();
    localStorage.removeItem("nochis_access_token");
    location.href = "login.html";
}