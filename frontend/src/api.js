const API_BASE_URL =
  import.meta.env.VITE_API_URL || "";


export const LINKEDIN_LOGIN_URL =
  `${API_BASE_URL}/api/v1/auth/linkedin/login`;


async function parseResponse(
  response,
  fallbackMessage
) {

  const body = await response.text();

  let data = null;

  if (body) {
    try {
      data = JSON.parse(body);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    throw new Error(
      data?.detail ||
      `${fallbackMessage} ` +
      `(${response.status})`
    );
  }

  if (data === null) {
    throw new Error(
      "Server returned an empty response"
    );
  }

  return data;
}


export async function fetchProfile(
  profileUrl
) {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/profile`,
    {
      method: "POST",

      credentials: "include",

      headers: {
        "Content-Type":
          "application/json"
      },

      body: JSON.stringify({
        profile_url: profileUrl
      })
    }
  );

  return parseResponse(
    response,
    "Unable to retrieve profile"
  );
}


export async function fetchSession() {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/auth/session`,
    {
      credentials: "include"
    }
  );

  return parseResponse(
    response,
    "Unable to read session"
  );
}


export async function fetchMyProfile() {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/me`,
    {
      credentials: "include"
    }
  );

  return parseResponse(
    response,
    "Unable to retrieve your profile"
  );
}


export async function logout() {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/auth/logout`,
    {
      method: "POST",
      credentials: "include"
    }
  );

  if (!response.ok) {
    throw new Error(
      "Unable to sign out " +
      `(${response.status})`
    );
  }
}


export async function fetchCachedProfiles() {

  const response = await fetch(
    `${API_BASE_URL}/api/v1/cache`,
    {
      credentials: "include"
    }
  );

  return parseResponse(
    response,
    "Unable to list cached profiles"
  );
}


export async function fetchCachedProfile(
  profileUrl
) {

  const params = new URLSearchParams({
    profile_url: profileUrl
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/cache/profile?${params}`,
    {
      credentials: "include"
    }
  );

  return parseResponse(
    response,
    "Unable to retrieve cached profile"
  );
}
