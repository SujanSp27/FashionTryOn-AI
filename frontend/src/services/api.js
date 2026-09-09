/**
 * FitFusion API Client
 * Interfaces with the Node.js Express Backend Gateway.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

/**
 * Checks backend gateway health.
 */
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed with HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    throw new Error('Unable to connect to the try-on backend service.');
  }
}

/**
 * Submits person and garment images for AI Virtual Try-On.
 * Sends multipart/form-data directly to Node.js backend.
 * Returns raw image Blob.
 */
export async function tryOnGarment(personFile, garmentFile, bgMode = 'ai') {
  if (!personFile || !garmentFile) {
    throw new Error('Both person and garment images are required.');
  }

  const formData = new FormData();
  formData.append('person', personFile);
  formData.append('garment', garmentFile);
  formData.append('bg_mode', bgMode);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/tryon`, {
      method: 'POST',
      body: formData // Let browser generate boundary header
    });
  } catch (networkErr) {
    throw new Error('Unable to connect to the try-on service. Please make sure the backend is running.');
  }

  // Handle errors from backend / AI service
  if (!response.ok) {
    let errorMsg = 'Failed to generate virtual try-on.';
    try {
      const errJson = await response.json();
      if (errJson.message) errorMsg = errJson.message;
      else if (errJson.error) errorMsg = errJson.error;
    } catch {
      if (response.status === 502) {
        errorMsg = 'The AI try-on service is temporarily unavailable. Please ensure the AI engine is running.';
      } else if (response.status === 504) {
        errorMsg = 'The virtual try-on service took too long to respond. Please try again.';
      } else if (response.status === 400) {
        errorMsg = 'Please upload valid image files (JPG, PNG, WEBP, or BMP).';
      } else if (response.status === 413) {
        errorMsg = 'Uploaded image file exceeds the 10 MB limit.';
      }
    }
    throw new Error(errorMsg);
  }

  // Extract timing headers if present
  const totalElapsed = response.headers.get('X-Gateway-Elapsed-Sec');
  const aiProcessTime = response.headers.get('X-AI-Process-Time-Total');
  const requestId = response.headers.get('X-Request-ID');
  const historyId = response.headers.get('X-History-ID');

  // Read raw binary JPEG blob
  const imageBlob = await response.blob();

  return {
    blob: imageBlob,
    timing: {
      totalElapsed: totalElapsed ? parseFloat(totalElapsed) : null,
      aiProcessTime: aiProcessTime ? parseFloat(aiProcessTime) : null
    },
    requestId,
    historyId
  };
}
