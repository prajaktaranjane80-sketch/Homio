
export type MegaMenuItem = Readonly<{
  label: string;
  description: string;
  href?: string;
  badge?: string;
  disabled?: boolean;
}>;

export type MegaMenuName =
  | "explore"
  | "markets"
  | "intelligence"
  | "services"
  | "my-homio"
  | "professional";
