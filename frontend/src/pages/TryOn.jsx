/**
 * Virtual Try-On Page Component
 * Coordinates uploads, loading state, error display, and result presentation.
 */

import React from 'react';
import { User, Shirt } from 'lucide-react';
import { useTryOn } from '../hooks/useTryOn';

import ImageUploader from '../components/ImageUploader';
import TryOnButton from '../components/TryOnButton';
import LoadingState from '../components/LoadingState';
import ResultViewer from '../components/ResultViewer';
import ErrorMessage from '../components/ErrorMessage';

export default function TryOn() {
  const {
    personFile,
    garmentFile,
    personPreview,
    garmentPreview,
    resultUrl,
    isLoading,
    error,
    processTime,
    isReady,
    handlePersonSelect,
    handleGarmentSelect,
    handleRemovePerson,
    handleRemoveGarment,
    handleTryOn,
    handleReset,
    setError
  } = useTryOn();

  return (
    <main className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
      {/* Page Header */}
      <div className="text-center max-w-2xl mx-auto mb-10">
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-gray-950">
          Virtual Try-On
        </h1>
        <p className="text-sm sm:text-base text-gray-500 mt-2">
          Upload your portrait and a clothing item to synthesize a tailored look.
        </p>
      </div>

      {/* Global Error Banner */}
      <ErrorMessage message={error} onRetry={isReady ? () => handleTryOn('ai') : null} />

      {/* View Switcher based on State */}
      {resultUrl && !isLoading ? (
        /* Result Screen */
        <ResultViewer
          resultUrl={resultUrl}
          personPreview={personPreview}
          garmentPreview={garmentPreview}
          processTime={processTime}
          onReset={handleReset}
        />
      ) : isLoading ? (
        /* Loading Screen */
        <LoadingState />
      ) : (
        /* Upload Workstation Screen */
        <div className="w-full flex flex-col items-center">
          {/* Responsive Two-Column Upload Grid */}
          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 mb-10 max-w-4xl">
            {/* 1. Person Uploader */}
            <ImageUploader
              label="Your Photo"
              helperText="Use a clear, front-facing upper-body photo for best results."
              icon={User}
              file={personFile}
              previewUrl={personPreview}
              onFileSelect={handlePersonSelect}
              onRemove={handleRemovePerson}
              disabled={isLoading}
            />

            {/* 2. Garment Uploader */}
            <ImageUploader
              label="Garment"
              helperText="Upload a photo of the clothing item you want to try."
              icon={Shirt}
              file={garmentFile}
              previewUrl={garmentPreview}
              onFileSelect={handleGarmentSelect}
              onRemove={handleRemoveGarment}
              disabled={isLoading}
            />
          </div>

          {/* Try On Action CTA */}
          <div className="w-full max-w-sm flex flex-col items-center gap-2">
            <TryOnButton
              onClick={() => handleTryOn('ai')}
              disabled={!isReady}
              isLoading={isLoading}
            />
            {!isReady && !isLoading && (
              <p className="text-xs text-gray-400 text-center">
                Upload both images above to enable virtual try-on
              </p>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
