"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import type {
  SearchCurrency,
  SearchIntent,
} from "@/features/f03_search/search.types";

import AIConversationPreview from "./AIConversationPreview";
import AIErrorState from "./AIErrorState";
import AISearch from "./AISearch";
import AINaturalLanguageInput from "./AINaturalLanguageInput";
import AISuggestionPanel from "./AISuggestionPanel";
import AIRecommendations from "./AIRecommendations";
import AIBudgetGuidance from "./AIBudgetGuidance";
import AIPropertyComparison from "./AIPropertyComparison";
import AILocalityComparison from "./AILocalityComparison";
import AIInvestmentAssistant from "./AIInvestmentAssistant";
import AIRentalAssistant from "./AIRentalAssistant";
import AIMarketAssistant from "./AIMarketAssistant";
import AIPropertySummary from "./AIPropertySummary";
import AIBrokerageHandoff from "./AIBrokerageHandoff";

import {
  AI_LIVE_SERVICE_CONNECTED,
  buildSearchHref,
} from "./ai.constants";

import type { AIConversationMessage } from "./ai.types";
import styles from "./AIWorkspace.module.css";

export default function AIWorkspace() {
  const router = useRouter();

  const [intent, setIntent] = useState<SearchIntent>("buy");
  const [location, setLocation] = useState("");
  const [budget, setBudget] = useState("");
  const [currency, setCurrency] = useState<SearchCurrency>("INR");
  const [prompt, setPrompt] = useState("");
  const [lastBrief, setLastBrief] = useState("");
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<AIConversationMessage[]>([]);

  function choosePrompt(
    value: string,
    nextIntent?: SearchIntent,
  ) {
    setPrompt(value);
    setError("");

    if (nextIntent) {
      setIntent(nextIntent);
    }

    document.getElementById("ai-natural-language-brief")?.focus();
  }

  function submitPrompt() {
    const value = prompt.trim();

    if (!value) {
      setError(
        "Add a short brief first, or choose one of the suggested prompts.",
      );
      return;
    }

    setError("");
    setLastBrief(value);

    const id = `${Date.now()}-${messages.length}`;

    const userMessage: AIConversationMessage = {
      id: `${id}-user`,
      role: "user",
      content: value,
    };

    const workspaceMessage: AIConversationMessage = {
      id: `${id}-workspace`,
      role: "workspace",
      content:
        "Your brief is captured in this page preview. The live HOMIO AI service is not connected, so no property-specific answer, live market analysis or listing verification has been generated. Continue to Search to explore the current catalogue and verify important details with an authorised source.",
    };

    setMessages((current) => [
      ...current,
      userMessage,
      workspaceMessage,
    ]);

    setPrompt("");
  }

  function openSearch() {
    const cleanedBudget = budget.trim();

    if (
      cleanedBudget &&
      (!Number.isFinite(Number(cleanedBudget)) ||
        Number(cleanedBudget) <= 0)
    ) {
      setError(
        "Enter a valid budget greater than zero, or leave the budget blank.",
      );
      return;
    }

    setError("");

    router.push(
      buildSearchHref({
        intent,
        location,
        budget: cleanedBudget,
        currency,
        query: prompt.trim() || lastBrief,
      }),
    );
  }

  function receivePropertyDraft(draft: string) {
    setLastBrief(draft);
    setError("");
  }

  return (
    <main className={styles.workspace}>
      <div className={styles.inner}>
        <header className={styles.hero}>
          <div className={styles.heroMain}>
            <p className={styles.eyebrow}>
              HOMIO AI · PROPERTY DECISION WORKSPACE
            </p>

            <h1 className={styles.heroTitle}>
              Find clarity before you find a{" "}
              <em>place.</em>
            </h1>

            <p className={styles.heroCopy}>
              Bring your goals, budget and questions into one considered
              workspace. Shape a brief, compare what matters and move
              into property discovery with fewer blind spots.
            </p>

            <div className={styles.heroActions}>
              <button
                className={styles.buttonHero}
                type="button"
                onClick={() => {
                  document
                    .getElementById("ai-natural-language-brief")
                    ?.focus();
                }}
              >
                Start with a brief
                <span aria-hidden="true">↓</span>
              </button>

              <span className={styles.heroMeta}>
                Homes · Rentals · Projects · Commercial
              </span>
            </div>
          </div>

          <aside
            className={styles.heroAside}
            aria-label="AI workspace service status"
          >
            <div className={styles.statusTop}>
              <span className={styles.statusDot} aria-hidden="true" />
              <span>
                {AI_LIVE_SERVICE_CONNECTED
                  ? "AI service connected"
                  : "Experience preview"}
              </span>
            </div>

            <h2>
              {AI_LIVE_SERVICE_CONNECTED
                ? "Live assistance enabled"
                : "Your decisions stay transparent"}
            </h2>

            <p>
              {AI_LIVE_SERVICE_CONNECTED
                ? "Status is supplied by the connected service."
                : "The interface is ready for service integration. Live model answers, market feeds and broker handoff are not enabled in this build."}
            </p>

            <div className={styles.heroStatLine}>
              <span>Property discovery</span>
              <strong>F03 connected</strong>
            </div>

            <div className={styles.heroStatLine}>
              <span>Compare board</span>
              <strong>F06 connected</strong>
            </div>
          </aside>
        </header>

        <div className={styles.trustStrip}>
          <span className={styles.trustIcon} aria-hidden="true">
            ✓
          </span>
          <p>
            <strong>Clear boundaries by design.</strong>{" "}
            This workspace does not fabricate property facts, price
            forecasts or broker actions. Drafts remain in page state.
          </p>
        </div>

        {error ? (
          <AIErrorState
            message={error}
            onDismiss={() => setError("")}
          />
        ) : null}

        <div className={styles.workspaceGrid}>
          <div className={styles.mainColumn}>
            <AISearch
              intent={intent}
              location={location}
              onIntentChange={setIntent}
              onLocationChange={setLocation}
              onOpenSearch={openSearch}
            />

            <AINaturalLanguageInput
              value={prompt}
              onChange={setPrompt}
              onSubmit={submitPrompt}
            />

            <AIConversationPreview messages={messages} />

            <div className={styles.twoColumnGrid}>
              <AIPropertySummary onDraftCreated={receivePropertyDraft} />
              <AIPropertyComparison />
            </div>

            <AILocalityComparison />
          </div>

          <aside
            className={styles.sideColumn}
            aria-label="Decision tools"
          >
            <AISuggestionPanel onSelectPrompt={choosePrompt} />

            <AIBudgetGuidance
              budget={budget}
              currency={currency}
              onBudgetChange={setBudget}
              onCurrencyChange={setCurrency}
            />

            <AIRecommendations onSelectPrompt={choosePrompt} />

            <AIInvestmentAssistant onSelectPrompt={choosePrompt} />

            <AIRentalAssistant onSelectPrompt={choosePrompt} />

            <AIMarketAssistant onSelectPrompt={choosePrompt} />

            <AIBrokerageHandoff />
          </aside>
        </div>

        <footer className={styles.footerNote}>
          HOMIO AI is an experience layer. Listing accuracy, legal status,
          availability, costs and market data must come from authorised
          sources. Do not treat this preview as professional financial,
          legal or investment advice.
        </footer>
      </div>
    </main>
  );
}
