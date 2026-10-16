import ContentCollection from "./ContentCollection";
import type { AdviceArticleRecord } from "./ContentExperience.types";

type Props = Readonly<{
  articles: readonly AdviceArticleRecord[];
}>;

export default function AdviceIndex({ articles }: Props) {
  return (
    <ContentCollection
      title="Property advice, made clearer."
      description="Practical education for buyers, sellers, renters and property professionals. Article availability depends on the published content source."
      items={articles}
      emptyMessage="Advice content is not connected yet. No placeholder articles are presented as published guidance."
    />
  );
}
