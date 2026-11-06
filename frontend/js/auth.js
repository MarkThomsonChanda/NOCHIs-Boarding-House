// ======================================
// NOCHIs BOARDING HOUSE - AUTHENTICATION
// ======================================

// Display messages
function showMessage(message, type = "error") {
    const element =
        document.getElementById("registerMessage") ||
        document.getElementById("message") ||
        document.getElementById("authMessage");

    if (element) {
        element.textContent = message;
        element.style.color =
            type === "success" ? "green" : "red";
    }
}


// ======================================
// REGISTER STUDENT
// ======================================

async function registerUser(fullName, email, password) {

    try {
        showMessage("Creating your account...", "success");

        const { data, error } =
            await supabaseClient.auth.signUp({
                email: email,
                password: password,
                options: {
                    data: {
                        full_name: fullName,
                        role: "student"
                    }
                }
            });

        if (error) {
            throw error;
        }

        if (!data.session) {
            showMessage(
                "Registration successful! Please check your email to verify your account.",
                "success"
            );
            return;
        }

        showMessage(
            "Account created successfully!",
            "success"
        );

        window.location.href = "dashboard.html";

    } catch (error) {
        showMessage(error.message);
    }
}


// ======================================
// LOGIN USER
// ======================================

async function loginUser(email, password) {

    try {
        showMessage("Signing in...", "success");

        const { data, error } =
            await supabaseClient.auth.signInWithPassword({
                email: email,
                password: password
            });

        if (error) {
            throw error;
        }

        const token = data.session.access_token;

        localStorage.setItem("nochis_access_token", token);

        const response = await fetch(
            API_URL + "/api/me",
            {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json"
                }
            }
        );

        if (!response.ok) {
            throw new Error(
                "Could not load your profile. Please contact the administrator."
            );
        }

        const result = await response.json();

        const profile = result.profile || result;

        if (profile.role === "owner") {

            window.location.href = "admin.html";

        } else {

            window.location.href = "dashboard.html";

        }

    } catch (error) {
        showMessage(error.message);
    }
}


// ======================================
// LOGOUT USER
// ======================================

async function logoutUser() {

    try {
        await supabaseClient.auth.signOut();

        localStorage.removeItem("nochis_access_token");

        window.location.href = "login.html";

    } catch (error) {
        console.error("Logout error:", error);
    }
}


// ======================================
// REGISTRATION FORM
// ======================================

document.addEventListener("DOMContentLoaded", function () {

    const registerForm =
        document.getElementById("registerForm");

    if (registerForm) {

        registerForm.addEventListener("submit", async function (event) {

            event.preventDefault();

            const fullName =
                document.getElementById("full_name").value.trim();

            const email =
                document.getElementById("email").value.trim();

            const password =
                document.getElementById("password").value;

            const confirmPassword =
                document.getElementById("confirm_password").value;

            if (password !== confirmPassword) {
                showMessage("Passwords do not match.");
                return;
            }

            if (password.length < 8) {
                showMessage("Password must have at least 8 characters.");
                return;
            }

            await registerUser(fullName, email, password);

        });
    }


    // ==================================
    // LOGIN FORM
    // ==================================

    const loginForm =
        document.getElementById("loginForm") ||
        document.getElementById("form");

    if (loginForm) {

        loginForm.addEventListener("submit", async function (event) {

            event.preventDefault();

            const email =
                loginForm.querySelector('[type="email"]').value.trim();

            const password =
                loginForm.querySelector('[type="password"]').value;

            await loginUser(email, password);

        });
    }

})
