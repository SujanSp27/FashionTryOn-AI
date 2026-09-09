/**
 * Result Viewer Component
 * Displays synthesized AI image alongside inputs with download and reset actions.
 */

import React from 'react';
import { Download, RotateCcw, Clock, Sparkles } from 'lucide-react';

export default function ResultViewer({
  resultUrl,
  personPreview,
  garmentPreview,
  processTime,
  onReset
}) {
  const handleDownload = () => {
    if (!resultUrl) return;
    const a = document.createElement('a');
    a.href = resultUrl;
    a.download = `fitfusion-tryon-${Date.now()}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col items-center">
      {/* Result Badge */}
      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-900 text-xs font-semibold mb-6">
        <Sparkles className="w-3.5 h-3.5 text-amber-500" />
        <span>Synthesized with Flow-Style-VTON & U²-Net</span>
      </div>

      <div className="w-full grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Main Centerpiece AI Result */}
        <div className="md:col-span-8 flex flex-col items-center">
          <div className="relative w-full max-w-md aspect-[3/4] rounded-2xl overflow-hidden bg-white shadow-lg border border-gray-200">
            <img
              src={resultUrl}
              alt="AI Generated Virtual Try-On Result"
              className="w-full h-full object-cover"
            />
          </div>

          {/* Performance Badge */}
          {processTime && (
            <div className="mt-3 flex items-center gap-1 text-xs text-gray-400">
              <Clock className="w-3.5 h-3.5" />
              <span>Generated in {processTime.toFixed(2)}s</span>
            </div>
          )}
        </div>

        {/* Input Pair Comparison Sidebar */}
        <div className="md:col-span-4 flex flex-col gap-4 w-full max-w-xs mx-auto">
          <div className="p-4 rounded-xl bg-white border border-gray-200 shadow-2xs">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-2">
              Original Photo
            </span>
            <div className="w-full aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 border border-gray-100">
              <img
                src={personPreview}
                alt="Original person"
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white border border-gray-200 shadow-2xs">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-2">
              Target Garment
            </span>
            <div className="w-full aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 border border-gray-100">
              <img
                src={garmentPreview}
                alt="Selected garment"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
        <button
          type="button"
          onClick={handleDownload}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gray-900 text-white hover:bg-black font-medium text-sm shadow-sm hover:shadow transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900"
        >
          <Download className="w-4 h-4" />
          <span>Download Result</span>
        </button>

        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-gray-800 hover:text-black border border-gray-200 hover:border-gray-300 font-medium text-sm shadow-2xs hover:bg-gray-50 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Try Another Garment</span>
        </button>
      </div>
    </div>
  );
}
