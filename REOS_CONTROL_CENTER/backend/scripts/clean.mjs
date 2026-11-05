import { rm } from "node:fs/promises";

const targets = [
  new URL("../dist/", import.meta.url),
  new URL("../coverage/", import.meta.url)
];

await Promise.all(
  targets.map((target) =>
    rm(target, {
      recursive: true,
      force: true
    })
  )
);
