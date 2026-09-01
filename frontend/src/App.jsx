import { useCallback, useEffect, useState } from "react";

import {
  LINKEDIN_LOGIN_URL,
  fetchMyProfile,
  fetchProfile,
  fetchSession,
  logout
} from "./api";


function isSafeImageUrl(url) {

  if (!url || typeof url !== "string") {
    return false;
  }

  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase();

    return (
      parsed.protocol === "https:" &&
      (host === "licdn.com" ||
        host.endsWith(".licdn.com"))
    );
  } catch {
    return false;
  }
}


function ExperienceList({ items }) {

  if (!items?.length) {
    return null;
  }

  return (
    <section>

      <h3>Experience</h3>

      {items.map(
        (item, index) => (
          <article
            className="item"
            key={`${item.company}-${index}`}
          >

            <strong>
              {item.title || "Position"}
            </strong>

            {item.company && (
              <p>
                {item.company}
              </p>
            )}

            <small>

              {item.start_date || ""}

              {item.start_date &&
                item.end_date &&
                " - "}

              {item.end_date || (
                item.start_date
                  ? "Present"
                  : ""
              )}

            </small>

            {item.description && (
              <p>
                {item.description}
              </p>
            )}

          </article>
        )
      )}

    </section>
  );
}


function EducationList({ items }) {

  if (!items?.length) {
    return null;
  }

  return (
    <section>

      <h3>Education</h3>

      {items.map(
        (item, index) => (
          <article
            className="item"
            key={`${item.school}-${index}`}
          >

            <strong>
              {item.school || "Institution"}
            </strong>

            {item.degree && (
              <p>
                {item.degree}
              </p>
            )}

            {item.field_of_study && (
              <small>
                {item.field_of_study}
              </small>
            )}

          </article>
        )
      )}

    </section>
  );
}


function Skills({ skills }) {

  if (!skills?.length) {
    return null;
  }

  return (
    <section>

      <h3>Skills</h3>

      <div className="skills">

        {skills.map(
          (skill) => (
            <span
              key={skill}
              className="skill"
            >
              {skill}
            </span>
          )
        )}

      </div>

    </section>
  );
}


function App() {

  const [
    profileUrl,
    setProfileUrl
  ] = useState("");

  const [
    profile,
    setProfile
  ] = useState(null);

  const [
    loading,
    setLoading
  ] = useState(false);

  const [
    error,
    setError
  ] = useState("");

  const [
    session,
    setSession
  ] = useState({
    authenticated: false,
    oauth_configured: false
  });


  const loadSession = useCallback(
    async () => {

      try {
        setSession(await fetchSession());
      } catch {
        setSession({
          authenticated: false,
          oauth_configured: false
        });
      }
    },
    []
  );


  useEffect(
    () => {
      loadSession();
    },
    [loadSession]
  );


  const loadMyProfile = useCallback(
    async () => {

      setError("");
      setProfile(null);
      setLoading(true);

      try {
        setProfile(await fetchMyProfile());
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Something went wrong"
        );
      } finally {
        setLoading(false);
      }
    },
    []
  );


  useEffect(
    () => {

      const params =
        new URLSearchParams(
          window.location.search
        );

      if (params.get("auth") === "failed") {
        setError(
          "LinkedIn sign-in did not complete"
        );
      }

      if (params.get("auth") === "success") {
        loadMyProfile();
      }
    },
    [loadMyProfile]
  );


  async function handleSignOut() {

    try {
      await logout();
    } catch {
      // Cookie is cleared server-side even
      // if the response is unavailable.
    }

    setProfile(null);
    setError("");

    await loadSession();
  }


  async function handleSubmit(event) {

    event.preventDefault();

    setError("");
    setProfile(null);
    setLoading(true);

    try {

      const result =
        await fetchProfile(
          profileUrl.trim()
        );

      setProfile(result);

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong"
      );

    } finally {

      setLoading(false);

    }
  }


  return (

    <main className="container">

      <header className="hero">

        <h1>
          LinkedIn Profile API
        </h1>

        <p>
          Submit a public LinkedIn profile URL.
          The backend calls LinkedIn Voyager
          endpoints over HTTPS — no browser
          automation.
        </p>

      </header>


      <section className="auth">

        {session.authenticated ? (

          <>
            <p>
              Signed in
              {session.name
                ? ` as ${session.name}`
                : ""}
            </p>

            <button
              type="button"
              onClick={loadMyProfile}
              disabled={loading}
            >
              View My Profile
            </button>

            <button
              type="button"
              onClick={handleSignOut}
            >
              Sign Out
            </button>
          </>

        ) : session.oauth_configured ? (

          <a
            className="linkedin-button"
            href={LINKEDIN_LOGIN_URL}
          >
            Sign in with LinkedIn
          </a>

        ) : (

          <p>
            LinkedIn sign-in is not
            configured on the server.
          </p>

        )}

      </section>


      <form
        className="profile-form"
        onSubmit={handleSubmit}
      >

        <label htmlFor="profile-url">
          LinkedIn Profile URL
        </label>

        <input
          id="profile-url"
          type="url"
          placeholder={
            "https://www.linkedin.com/in/..."
          }
          value={profileUrl}
          onChange={(event) =>
            setProfileUrl(
              event.target.value
            )
          }
          required
        />

        <button
          type="submit"
          disabled={loading}
        >

          {loading
            ? "Loading..."
            : "Fetch Profile"}

        </button>

      </form>


      {error && (

        <div
          className="error"
          role="alert"
        >
          {error}
        </div>

      )}


      {profile && (

        <section className="profile">

          <div className="profile-header">

            {isSafeImageUrl(profile.profile_image) ? (

              <img
                className="avatar"
                src={profile.profile_image}
                alt={
                  profile.name ||
                  "Profile"
                }
              />

            ) : (

              <div className="avatar placeholder">
                {(
                  profile.name ||
                  "?"
                )
                  .charAt(0)
                  .toUpperCase()}
              </div>

            )}


            <div>

              <h2>
                {profile.name ||
                  "Unknown Profile"}
              </h2>

              {profile.headline && (
                <p>
                  {profile.headline}
                </p>
              )}

              {profile.location && (
                <small>
                  {profile.location}
                </small>
              )}

            </div>

          </div>


          {profile.about && (

            <section>

              <h3>About</h3>

              <p>
                {profile.about}
              </p>

            </section>

          )}


          <ExperienceList
            items={profile.experience}
          />


          <EducationList
            items={profile.education}
          />


          <Skills
            skills={profile.skills}
          />


          {profile.certifications?.length > 0 && (

            <section>

              <h3>
                Certifications
              </h3>

              {profile.certifications.map(
                (item, index) => (

                  <article
                    className="item"
                    key={`${item.name}-${index}`}
                  >

                    <strong>
                      {item.name}
                    </strong>

                    {item.organization && (
                      <p>
                        {item.organization}
                      </p>
                    )}

                  </article>

                )
              )}

            </section>

          )}


          {profile.languages?.length > 0 && (

            <section>

              <h3>Languages</h3>

              <ul>

                {profile.languages.map(
                  (language) => (

                    <li
                      key={language.name}
                    >

                      {language.name}

                      {language.proficiency &&
                        ` — ${language.proficiency}`}

                    </li>

                  )
                )}

              </ul>

            </section>

          )}


          <footer className="metadata">

            <span>
              Status:
              {" "}
              {profile.metadata.status}
            </span>

            <span>
              Cached:
              {" "}
              {profile.metadata.cached
                ? "Yes"
                : "No"}
            </span>

          </footer>

          <details className="json-preview">
            <summary>
              Raw JSON
            </summary>
            <pre>
              {JSON.stringify(profile, null, 2)}
            </pre>
          </details>

        </section>

      )}

    </main>

  );
}


export default App;
