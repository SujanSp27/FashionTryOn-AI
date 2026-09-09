/**
 * Virtual Try-On State Management Hook
 * Manages files, previews, object URLs, request lifecycle, and cleanup.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { tryOnGarment } from '../services/api';

export function useTryOn() {
  const [personFile, setPersonFile] = useState(null);
  const [garmentFile, setGarmentFile] = useState(null);

  const [personPreview, setPersonPreview] = useState(null);
  const [garmentPreview, setGarmentPreview] = useState(null);

  const [resultBlob, setResultBlob] = useState(null);
  const [resultUrl, setResultUrl] = useState(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processTime, setProcessTime] = useState(null);

  // Synchronize Person Object URL Preview
  useEffect(() => {
    if (!personFile) {
      setPersonPreview(null);
      return;
    }
    const url = URL.createObjectURL(personFile);
    setPersonPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [personFile]);

  // Synchronize Garment Object URL Preview
  useEffect(() => {
    if (!garmentFile) {
      setGarmentPreview(null);
      return;
    }
    const url = URL.createObjectURL(garmentFile);
    setGarmentPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [garmentFile]);

  // Synchronize Result Object URL
  useEffect(() => {
    if (!resultBlob) {
      setResultUrl(null);
      return;
    }
    const url = URL.createObjectURL(resultBlob);
    setResultUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [resultBlob]);

  // Compute state machine status
  const status = useMemo(() => {
    if (isLoading) return 'LOADING';
    if (error) return 'ERROR';
    if (resultUrl) return 'SUCCESS';
    if (personFile && garmentFile) return 'READY';
    if (personFile) return 'PERSON_SELECTED';
    if (garmentFile) return 'GARMENT_SELECTED';
    return 'IDLE';
  }, [isLoading, error, resultUrl, personFile, garmentFile]);

  const isReady = useMemo(() => {
    return Boolean(personFile && garmentFile && !isLoading);
  }, [personFile, garmentFile, isLoading]);

  // Select Person image
  const handlePersonSelect = useCallback((file) => {
    setError(null);
    setResultBlob(null);
    setPersonFile(file);
  }, []);

  // Select Garment image
  const handleGarmentSelect = useCallback((file) => {
    setError(null);
    setResultBlob(null);
    setGarmentFile(file);
  }, []);

  // Remove Person
  const handleRemovePerson = useCallback(() => {
    setPersonFile(null);
    setResultBlob(null);
    setError(null);
  }, []);

  // Remove Garment
  const handleRemoveGarment = useCallback(() => {
    setGarmentFile(null);
    setResultBlob(null);
    setError(null);
  }, []);

  // Execute Try-On
  const handleTryOn = useCallback(async (bgMode = 'ai') => {
    if (!personFile || !garmentFile) {
      setError('Please upload both your photo and a garment image before trying on.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResultBlob(null);
    setProcessTime(null);

    try {
      const { blob, timing } = await tryOnGarment(personFile, garmentFile, bgMode);
      setResultBlob(blob);
      if (timing && timing.totalElapsed) {
        setProcessTime(timing.totalElapsed);
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during virtual try-on.');
    } finally {
      setIsLoading(false);
    }
  }, [personFile, garmentFile]);

  // Reset all state to IDLE
  const handleReset = useCallback(() => {
    setPersonFile(null);
    setGarmentFile(null);
    setResultBlob(null);
    setError(null);
    setIsLoading(false);
    setProcessTime(null);
  }, []);

  return {
    personFile,
    garmentFile,
    personPreview,
    garmentPreview,
    resultUrl,
    resultBlob,
    isLoading,
    error,
    processTime,
    status,
    isReady,
    handlePersonSelect,
    handleGarmentSelect,
    handleRemovePerson,
    handleRemoveGarment,
    handleTryOn,
    handleReset,
    setError
  };
}
