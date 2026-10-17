import type { ReactNode } from "react";

export interface MotionRevealProps {
  children: ReactNode;
  className?: string;
  delayMs?: number;
  once?: boolean;
}
