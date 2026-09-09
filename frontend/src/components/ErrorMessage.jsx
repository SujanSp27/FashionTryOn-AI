/**
 * Error Alert Component
 */

import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

export default function ErrorMessage({ message, onRetry }) {
  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="w-full max-w-xl mx-auto mb-6 p-4 rounded-xl bg-red-50/90 border border-red-200 text-red-900 flex items-start gap-3 shadow-2xs"
    >
      <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
      <div className="flex-1 text-sm">
        <h4 className="font-semibold text-red-950">Virtual Try-On Error</h4>
        <p className="mt-0.5 text-red-800 text-xs sm:text-sm">{message}</p>
      </div>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1 text-xs font-semibold text-red-700 hover:text-red-900 bg-red-100/70 hover:bg-red-200/80 px-2.5 py-1.5 rounded-lg transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
