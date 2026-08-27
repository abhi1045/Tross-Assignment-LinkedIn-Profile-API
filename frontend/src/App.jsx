import { useState } from "react";

import { fetchProfile } from "./api";

function App() {

  const [profileUrl, setProfileUrl] =
    useState("");

  const [profile, setProfile] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);


  async function handleSubmit(event) {

    event.preventDefault();

    setLoading(true);
    setError(null);
    setProfile(null);

    try {

      const result =
        await fetchProfile(profileUrl);

      setProfile(result);

    } catch (err) {

      setError(
        err.message ||
        "Something went wrong"
      );

    } finally {

      setLoading(false);

    }
  }


  return (
    <main className="container">

      <header>
        <h1>
          LinkedIn Profile API
        </h1>

        <p>
          Enter a profile URL to retrieve
          structured information.
        </p>
      </header>


      <form onSubmit={handleSubmit}>

        <label htmlFor="profile-url">
          Profile URL
        </label>

        <input
          id="profile-url"
          type="url"
          placeholder="https://www.linkedin.com/in/..."
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
        <div className="error">
          {error}
        </div>
      )}


      {profile && (
        <section className="profile">

          <div className="profile-header">

            {profile.profile_image && (
              <img
                src={profile.profile_image}
                alt={profile.name}
                className="avatar"
              />
            )}

            <div>
              <h2>
                {profile.name ||
                  "Unknown"}
              </h2>

              <p>
                {profile.headline}
              </p>

              <small>
                {profile.location}
              </small>
            </div>

          </div>


          {profile.about && (
            <section>
              <h3>About</h3>
              <p>{profile.about}</p>
            </section>
          )}


          {profile.experience.length > 0 && (
            <section>

              <h3>Experience</h3>

              {profile.experience.map(
                (item, index) => (

                  <article key={index}>

                    <strong>
                      {item.title}
                    </strong>

                    <p>
                      {item.company}
                    </p>

                    <small>
                      {item.start_date}
                      {" - "}
                      {item.end_date ||
                        "Present"}
                    </small>

                  </article>
                )
              )}

            </section>
          )}


          {profile.education.length > 0 && (
            <section>

              <h3>Education</h3>

              {profile.education.map(
                (item, index) => (

                  <article key={index}>

                    <strong>
                      {item.school}
                    </strong>

                    <p>
                      {item.degree}
                    </p>

                  </article>
                )
              )}

            </section>
          )}


          {profile.skills.length > 0 && (
            <section>

              <h3>Skills</h3>

              <div className="skills">

                {profile.skills.map(
                  (skill) => (
                    <span key={skill}>
                      {skill}
                    </span>
                  )
                )}

              </div>

            </section>
          )}


          <section className="metadata">

            <small>
              Status: {profile.metadata.status}
            </small>

            <small>
              Cached:{" "}
              {profile.metadata.cached
                ? "Yes"
                : "No"}
            </small>

          </section>

        </section>
      )}

    </main>
  );
}

export default App;
