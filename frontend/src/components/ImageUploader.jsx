/**
 * Accessible Drag & Drop Image Uploader Component
 */

import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, AlertCircle } from 'lucide-react';
import ImagePreview from './ImagePreview';

const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp'];
const MAX_BYTES = 10 * 1024 * 1024; // 10MB limit

export default function ImageUploader({
  label,
  helperText,
  icon: Icon = ImageIcon,
  file,
  previewUrl,
  onFileSelect,
  onRemove,
  disabled = false
}) {
  const inputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [localError, setLocalError] = useState(null);

  const validateAndPassFile = (selectedFile) => {
    setLocalError(null);
    if (!selectedFile) return;

    // Check size limit
    if (selectedFile.size > MAX_BYTES) {
      setLocalError('File size exceeds 10 MB limit.');
      return;
    }

    // Check file type
    const validMimes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp'];
    if (!validMimes.includes(selectedFile.type.toLowerCase())) {
      setLocalError('Please select a JPG, PNG, WEBP, or BMP image.');
      return;
    }

    onFileSelect(selectedFile);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !file) setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (disabled || file) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndPassFile(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndPassFile(e.target.files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled && inputRef.current) {
      inputRef.current.value = '';
      inputRef.current.click();
    }
  };

  return (
    <div className="w-full flex flex-col">
      {/* Label and Helper */}
      <div className="mb-2">
        <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-1.5">
          <Icon className="w-4 h-4 text-gray-600" />
          <span>{label}</span>
        </h3>
        {helperText && (
          <p className="text-xs text-gray-500 mt-0.5">{helperText}</p>
        )}
      </div>

      {/* Main Upload Drop Box */}
      <div
        onClick={!file ? handleClick : undefined}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        role="button"
        tabIndex={disabled || file ? -1 : 0}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !file && !disabled) {
            e.preventDefault();
            handleClick();
          }
        }}
        aria-label={`Upload ${label}`}
        className={`relative w-full aspect-[3/4] min-h-[300px] max-h-[380px] rounded-2xl border-2 transition-all flex items-center justify-center overflow-hidden bg-white ${
          file
            ? 'border-solid border-gray-200'
            : isDragOver
            ? 'border-gray-900 bg-gray-50 cursor-copy ring-4 ring-gray-100'
            : 'border-dashed border-gray-300 hover:border-gray-400 hover:bg-gray-50/70 cursor-pointer shadow-2xs'
        } ${disabled ? 'opacity-60 pointer-events-none' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
        />

        {file && previewUrl ? (
          <ImagePreview
            previewUrl={previewUrl}
            file={file}
            label={label}
            onRemove={onRemove}
            onReplace={handleClick}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-center p-6 space-y-3">
            <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 group-hover:scale-105 transition-transform">
              <UploadCloud className="w-7 h-7 text-gray-700" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">
                Click to upload <span className="font-normal text-gray-500">or drag & drop</span>
              </p>
              <p className="text-xs text-gray-400 mt-1">
                JPG, PNG, WEBP, BMP up to 10MB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Inline Local Validation Error */}
      {localError && (
        <div className="mt-2 flex items-center gap-1 text-xs text-red-600">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{localError}</span>
        </div>
      )}
    </div>
  );
}
