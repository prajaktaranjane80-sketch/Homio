"use client";

import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import styles from "./MotionReveal.module.css";
import type { MotionRevealProps } from "./motion.types";

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

    if (reduceMotion.matches) {
      return;
    }

    // Keep the window object correctly typed for TypeScript.
    if (typeof window.IntersectionObserver !== "function") {
      const frameId = window.requestAnimationFrame(() => {
        setVisible(true);
      });

      return () => {
        window.cancelAnimationFrame(frameId);
      };
    }

    let observer: IntersectionObserver | undefined;

    observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];

        if (!entry) {
          return;
        }

        if (entry.isIntersecting) {
          setVisible(true);

          if (once) {
            observer?.unobserve(entry.target);
          }
        } else if (!once) {
          setVisible(false);
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

  const requestedDelay = Number.isFinite(delayMs) ? delayMs : 0;
  const delay = Math.max(0, Math.min(requestedDelay, 1000));

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
