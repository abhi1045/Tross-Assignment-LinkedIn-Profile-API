const API_BASE_URL =
  import.meta.env.VITE_API_URL || "";

export async function fetchProfile(profileUrl) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/profile`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        profile_url: profileUrl
      })
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "Unable to retrieve profile"
    );
  }

  return data;
}
