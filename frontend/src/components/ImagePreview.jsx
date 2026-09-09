/**
 * Image Preview Component
 * Renders thumbnail, metadata badge, and controls.
 */

import React from 'react';
import { X, RefreshCw } from 'lucide-react';

export default function ImagePreview({ previewUrl, file, onRemove, onReplace, label }) {
  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center p-3">
      {/* Image Display */}
      <div className="relative w-full max-w-[240px] aspect-[3/4] rounded-xl overflow-hidden bg-gray-100 shadow-sm border border-gray-200">
        <img
          src={previewUrl}
          alt={label || 'Uploaded preview'}
          className="w-full h-full object-cover"
        />

        {/* Quick remove button */}
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${label || 'image'}`}
          className="absolute top-2 right-2 w-7 h-7 rounded-full bg-black/60 text-white hover:bg-black flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-900"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Metadata & Actions */}
      <div className="mt-3 w-full max-w-[240px] flex items-center justify-between text-xs text-gray-500">
        <div className="truncate max-w-[140px]" title={file?.name}>
          <span className="font-medium text-gray-700">{file?.name}</span>
          <span className="block text-[10px] text-gray-400">{formatFileSize(file?.size)}</span>
        </div>

        <button
          type="button"
          onClick={onReplace}
          className="inline-flex items-center gap-1 text-xs font-medium text-gray-700 hover:text-gray-900 bg-white border border-gray-200 px-2.5 py-1 rounded-md shadow-2xs hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Change</span>
        </button>
      </div>
    </div>
  );
}
