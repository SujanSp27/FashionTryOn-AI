/**
 * Main Application Component with Router
 */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import Home from './pages/Home';
import TryOn from './pages/TryOn';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-[#FAFAFA]">
        <Navbar />
        <div className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/try-on" element={<TryOn />} />
            <Route path="*" element={<Home />} />
          </Routes>
        </div>
        <footer className="py-6 border-t border-gray-100 text-center text-xs text-gray-400">
          FitFusion AI Virtual Try-On &bull; College Project &bull; Flow-Style-VTON &amp; U²-Net
        </footer>
      </div>
    </BrowserRouter>
  );
}
