export function recordRecentView(
  view: Readonly<{
    id: string;
    kind: "property" | "project";
    title: string;
    href: string;
    subtitle?: string;
  }>,
): void {
  if (
    !ensureBrowserSession() ||
    !isText(view.id, 180) ||
    !isText(view.title, 240) ||
    !isInternalHref(view.href) ||
    (view.kind !== "property" && view.kind !== "project")
  ) {
    return;
  }

  const identity = `${view.kind}:${view.id}`;

  const record: MyHomioRecentView = {
    ...view,
    id: identity,
    viewedAt: new Date().toISOString(),
  };

  publish({
    ...snapshot,
    recentViews: [
      record,
      ...snapshot.recentViews.filter(
        (item) => item.id !== identity,
      ),
    ].slice(0, MAX_RECENT_VIEWS),
  });
}
