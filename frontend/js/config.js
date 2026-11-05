// Set this to your deployed API URL after hosting the backend.
const API_BASE = "http://127.0.0.1:8000";
const OWNER_CONTACTS = ["0977 204 572", "0979 324 363"];

function getToken() { return localStorage.getItem("nochis_access_token"); }
async function api(path, options = {}) {
  const headers = {"Content-Type":"application/json", ...(options.headers || {})};
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`;
  const response = await fetch(`${API_BASE}${path}`, {...options, headers});
  const data = await response.json().catch(()=>({detail:"Unexpected server response"}));
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}
