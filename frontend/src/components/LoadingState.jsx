/**
 * AI Processing Loading State Component
 */

import React from 'react';
import { Sparkles } from 'lucide-react';

export default function LoadingState() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full flex flex-col items-center justify-center p-8 sm:p-12 text-center"
    >
      {/* Animated Pulser */}
      <div className="relative w-20 h-20 mb-6 flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-amber-200/50 animate-ping opacity-75" />
        <div className="relative w-16 h-16 rounded-full bg-gray-900 text-amber-300 flex items-center justify-center shadow-lg">
          <Sparkles className="w-8 h-8 animate-pulse" />
        </div>
      </div>

      <h3 className="text-lg sm:text-xl font-bold text-gray-900 tracking-tight">
        Creating your look...
      </h3>
      <p className="text-sm text-gray-500 mt-1 max-w-sm">
        AI is isolating the garment, warping appearance flow, and tailoring it to your silhouette.
      </p>

      {/* Decorative skeleton preview container */}
      <div className="mt-8 w-48 aspect-[3/4] rounded-2xl bg-gradient-to-b from-gray-100 to-gray-200 animate-pulse border border-gray-200 shadow-inner flex items-center justify-center">
        <span className="text-xs font-medium text-gray-400">Synthesizing...</span>
      </div>
    </div>
  );
}
