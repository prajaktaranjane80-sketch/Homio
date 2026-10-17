"use client";

import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import styles from "./MotionReveal.module.css";

export interface MotionRevealProps {
  children: ReactNode;
  className?: string;
  delayMs?: number;
  once?: boolean;
}

export default function MotionReveal({
  children,
  className,
  delayMs = 0,
  once = true,
}: MotionRevealProps) {
  const elementRef = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const element = elementRef.current;

    if (!element) {
      return;
    }

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    );

    if (reduceMotion.matches || !("IntersectionObserver" in window)) {
      setVisible(true);
      return;
    }

    let observer: IntersectionObserver | undefined;

    observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];

        if (!entry?.isIntersecting) {
          return;
        }

        setVisible(true);

        if (once) {
          observer?.unobserve(entry.target);
        }
      },
      {
        threshold: 0.12,
        rootMargin: "0px 0px -32px 0px",
      },
    );

    observer.observe(element);

    return () => {
      observer?.disconnect();
    };
  }, [once]);

  const delay = Math.max(0, Math.min(delayMs, 1000));

  const style = {
    "--motion-reveal-delay": `${delay}ms`,
  } as CSSProperties;

  const classNames = [
    styles.reveal,
    visible ? styles.revealVisible : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={elementRef} className={classNames} style={style}>
      {children}
    </div>
  );
}
