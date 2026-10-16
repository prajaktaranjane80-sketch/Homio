import ContentCollection from "./ContentCollection";
import type { AdviceArticleRecord } from "./ContentExperience.types";

type Props = Readonly<{
  title: string;
  description: string;
  articles: readonly AdviceArticleRecord[];
}>;

export default function AdviceCategory({ title, description, articles }: Props) {
  return (
    <ContentCollection
      title={title}
      description={description}
      items={articles}
      emptyMessage="No published articles are available in this category yet."
    />
  );
}
