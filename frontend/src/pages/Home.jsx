/**
 * Home Page Component
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, Wand2, ShieldCheck, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="w-full">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 sm:pt-20 sm:pb-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            {/* Tag */}
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 text-gray-800 text-xs font-semibold mb-6">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Next-Generation Appearance Flow Virtual Try-On</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-950 leading-[1.15]">
              See Yourself in <br className="hidden sm:inline" />
              <span className="bg-gradient-to-r from-gray-950 via-gray-800 to-gray-600 bg-clip-text text-transparent">
                Any Style
              </span>
            </h1>

            {/* Subheading */}
            <p className="mt-6 text-base sm:text-lg text-gray-600 leading-relaxed max-w-2xl mx-auto">
              Upload your photo and a garment to create an AI-powered virtual try-on in seconds.
              Powered by deep appearance flow warping and automated U²-Net background extraction.
            </p>

            {/* Primary Action Button */}
            <div className="mt-8 flex justify-center">
              <Link
                to="/try-on"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gray-900 text-white hover:bg-black font-semibold text-base shadow-md hover:shadow-lg transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <span>Try It Now</span>
                <ArrowRight className="w-5 h-5 text-amber-300" />
              </Link>
            </div>
          </div>

          {/* Visual Composition Showcase */}
          <div className="mt-16 max-w-4xl mx-auto rounded-3xl bg-gradient-to-b from-white to-gray-50/50 p-4 sm:p-8 border border-gray-200/80 shadow-sm">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 items-center">
              {/* Step 1 Card */}
              <div className="p-5 rounded-2xl bg-white border border-gray-100 shadow-2xs flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center text-gray-900 mb-3 border border-gray-100">
                  <span className="text-lg font-bold">1</span>
                </div>
                <h4 className="font-semibold text-gray-900 text-sm">Your Photo</h4>
                <p className="text-xs text-gray-500 mt-1">Upload a front-facing portrait</p>
              </div>

              {/* Step 2 Card */}
              <div className="p-5 rounded-2xl bg-white border border-gray-100 shadow-2xs flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center text-gray-900 mb-3 border border-gray-100">
                  <span className="text-lg font-bold">2</span>
                </div>
                <h4 className="font-semibold text-gray-900 text-sm">Any Garment</h4>
                <p className="text-xs text-gray-500 mt-1">AI automatically strips backdrops</p>
              </div>

              {/* Step 3 Card */}
              <div className="p-5 rounded-2xl bg-gray-900 text-white shadow-md flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-xl bg-gray-800 text-amber-300 flex items-center justify-center mb-3">
                  <Wand2 className="w-6 h-6" />
                </div>
                <h4 className="font-semibold text-white text-sm">Instant Try-On</h4>
                <p className="text-xs text-gray-400 mt-1">Realistic fit synthesized</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Highlights */}
      <section className="py-16 bg-white border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-start p-6 rounded-2xl bg-gray-50/50 border border-gray-100">
              <div className="w-10 h-10 rounded-xl bg-gray-900 text-white flex items-center justify-center mb-4">
                <Zap className="w-5 h-5 text-amber-300" />
              </div>
              <h3 className="font-bold text-gray-900 text-base">Appearance Flow Warping</h3>
              <p className="text-sm text-gray-600 mt-1.5 leading-relaxed">
                Second-order global flow estimation adapts the garment to your body pose without texture stretching.
              </p>
            </div>

            <div className="flex flex-col items-start p-6 rounded-2xl bg-gray-50/50 border border-gray-100">
              <div className="w-10 h-10 rounded-xl bg-gray-900 text-white flex items-center justify-center mb-4">
                <Wand2 className="w-5 h-5 text-amber-300" />
              </div>
              <h3 className="font-bold text-gray-900 text-base">Automated Background Removal</h3>
              <p className="text-sm text-gray-600 mt-1.5 leading-relaxed">
                U²-Net segments product photos on colored walls, floors, or hangers with pristine edge preservation.
              </p>
            </div>

            <div className="flex flex-col items-start p-6 rounded-2xl bg-gray-50/50 border border-gray-100">
              <div className="w-10 h-10 rounded-xl bg-gray-900 text-white flex items-center justify-center mb-4">
                <ShieldCheck className="w-5 h-5 text-amber-300" />
              </div>
              <h3 className="font-bold text-gray-900 text-base">Privacy-First In-Memory Pipeline</h3>
              <p className="text-sm text-gray-600 mt-1.5 leading-relaxed">
                Uploaded portrait photos are processed in RAM and never stored permanently on disks.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
