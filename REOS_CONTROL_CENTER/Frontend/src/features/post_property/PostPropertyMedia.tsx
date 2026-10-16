"use client";

import { useState } from "react";

import styles from "./PostProperty.module.css";

type Props = Readonly<{
  files: readonly File[];
  onChange: (files: File[]) => void;
  disabled?: boolean;
}>;

const MAX_FILES = 12;
const MAX_FILE_BYTES = 20 * 1024 * 1024;
const ACCEPTED_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export default function PostPropertyMedia({ files, onChange, disabled = false }: Props) {
  const [error, setError] = useState("");

  function handleFiles(fileList: FileList | null) {
    if (!fileList) return;

    const selected = Array.from(fileList);
    if (files.length + selected.length > MAX_FILES) {
      setError(`Choose no more than ${MAX_FILES} files in total.`);
      return;
    }

    const invalid = selected.find(
      (file) => !ACCEPTED_TYPES.has(file.type) || file.size > MAX_FILE_BYTES,
    );

    if (invalid) {
      setError("Use JPG, PNG or WebP images. Each file must be 20 MB or smaller.");
      return;
    }

    setError("");
    onChange([...files, ...selected]);
  }

  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Property media</h2>
        <p className={styles.postPanelDescription}>Select image files for a future upload step.</p>
      </header>

      <div className={styles.postField}>
        <label className={styles.postLabel} htmlFor="post-property-media">Images</label>
        <input
          id="post-property-media"
          className={styles.postInput}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          disabled={disabled}
          onChange={(event) => handleFiles(event.currentTarget.files)}
        />
        <span className={styles.postHint}>Up to {MAX_FILES} files · 20 MB per file · JPEG, PNG or WebP.</span>
      </div>

      {error ? <p className={styles.postError} role="alert">{error}</p> : null}

      {files.length > 0 ? (
        <ul className={styles.postFileList} aria-label="Selected local media files">
          {files.map((file, index) => (
            <li className={styles.postFile} key={`${file.name}-${file.size}-${index}`}>
              <span className={styles.postFileName}>{file.name}</span>
              <span className={styles.postFileSize}>{(file.size / (1024 * 1024)).toFixed(1)} MB</span>
              {!disabled ? (
                <button type="button" className={styles.postStep} onClick={() => onChange(files.filter((_, fileIndex) => fileIndex !== index))}>
                  Remove
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className={styles.postNotice}>No files selected. Nothing has been uploaded.</p>
      )}

      <p className={styles.postHint}>Selected files remain local to this form until an approved upload service is connected and confirms the upload.</p>
    </section>
  );
}
