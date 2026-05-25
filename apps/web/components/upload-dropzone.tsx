'use client';

import { useCallback, useState } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { cn } from '@/lib/utils';

interface UploadDropzoneProps {
  onFile: (file: File) => void;
  accept?: Record<string, string[]>;
  maxSizeMb?: number;
}

export function UploadDropzone({
  onFile,
  accept = { 'application/pdf': ['.pdf'] },
  maxSizeMb = 10,
}: UploadDropzoneProps) {
  const [filename, setFilename] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      setError(null);
      if (rejected.length > 0) {
        const reason = rejected[0].errors[0]?.message ?? 'File rejected';
        setError(reason);
        return;
      }
      const file = accepted[0];
      if (!file) return;
      setFilename(file.name);
      onFile(file);
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize: maxSizeMb * 1024 * 1024,
    multiple: false,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-muted-foreground/30 bg-muted/20 p-10 text-center transition-colors hover:border-primary/50',
          isDragActive && 'border-primary bg-primary/5'
        )}
      >
        <input {...getInputProps()} />
        {filename ? (
          <>
            <p className="font-medium">{filename}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Click or drop to replace
            </p>
          </>
        ) : isDragActive ? (
          <p className="font-medium text-primary">Drop the PDF here…</p>
        ) : (
          <>
            <p className="font-medium">Drop a PDF here, or click to browse</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Maximum size {maxSizeMb} MB
            </p>
          </>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
    </div>
  );
}
