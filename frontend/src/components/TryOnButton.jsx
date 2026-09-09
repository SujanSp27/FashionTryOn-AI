/**
 * Try-On CTA Button Component
 */

import React from 'react';
import { Sparkles, Loader2 } from 'lucide-react';

export default function TryOnButton({ onClick, disabled, isLoading }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || isLoading}
      aria-label="Generate Virtual Try-On"
      className={`w-full max-w-sm mx-auto h-12 px-6 rounded-xl font-medium text-sm flex items-center justify-center gap-2 shadow-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 ${
        disabled
          ? 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-none'
          : isLoading
          ? 'bg-gray-800 text-gray-300 cursor-wait'
          : 'bg-gray-900 text-white hover:bg-black hover:shadow active:scale-[0.99] cursor-pointer'
      }`}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-amber-300" />
          <span>Fitting Garment...</span>
        </>
      ) : (
        <>
          <Sparkles className="w-4 h-4 text-amber-300" />
          <span>Try On Now</span>
        </>
      )}
    </button>
  );
}
