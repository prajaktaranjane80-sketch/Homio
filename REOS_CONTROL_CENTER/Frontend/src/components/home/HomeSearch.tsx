"use client";

import { FormEvent, useState } from "react";

const propertyTypes = [
  "Any property",
  "Apartment",
  "Villa",
  "House",
  "Plot",
  "Office",
  "Shop",
];

const bhkOptions = [
  "Any BHK",
  "1 BHK",
  "2 BHK",
  "3 BHK",
  "4 BHK",
  "5+ BHK",
];

const budgets = [
  "Any budget",
  "Under ₹25 L",
  "₹25–50 L",
  "₹50 L–₹1 Cr",
  "₹1–2 Cr",
  "₹2 Cr+",
];

export function HomeSearch() {
  const [message, setMessage] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setMessage(
      "Search binding will connect to the verified HOMIO search capability in F03.",
    );
  }

  return (
    <div id="home-search" className="home-search-panel">
      <div className="home-search-panel__intro">
        <div>
          <span className="home-eyebrow">SEARCH HOMIO</span>

          <h2>Find property by place, project or need.</h2>
        </div>

        <span className="home-search-panel__hint">
          Search first. Refine later.
        </span>
      </div>

      <form onSubmit={submit} className="home-search-form">
        <label className="home-search-field home-search-field--wide">
          <span>City, locality, project or landmark</span>

          <input
            name="location"
            placeholder="Try Pune, Baner, Kharadi, a project or landmark"
            autoComplete="off"
          />
        </label>

        <label className="home-search-field">
          <span>Property type</span>

          <select name="propertyType" defaultValue={propertyTypes[0]}>
            {propertyTypes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="home-search-field">
          <span>BHK</span>

          <select name="bhk" defaultValue={bhkOptions[0]}>
            {bhkOptions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="home-search-field">
          <span>Budget</span>

          <select name="budget" defaultValue={budgets[0]}>
            {budgets.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <button className="home-search-submit" type="submit">
          Search
        </button>
      </form>

      <div className="home-search-panel__status" aria-live="polite">
        {message}
      </div>
    </div>
  );
}
