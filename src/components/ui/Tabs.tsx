export type TabItem = {
  id: string;
  label: string;
};

export function Tabs({
  items,
  activeId,
  onChange,
}: Readonly<{
  items: TabItem[];
  activeId?: string;
  onChange?: (id: string) => void;
}>) {
  return (
    <div className="tabs" role="tablist" aria-label="Section tabs">
      {items.map((item) => {
        const active = item.id === activeId;

        return (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={active}
            className={`tab${active ? " tab--active" : ""}`}
            onClick={() => onChange?.(item.id)}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
