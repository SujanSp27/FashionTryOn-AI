/**
 * Navigation Bar Component
 */

import React from 'react';
import { NavLink } from 'react-router-dom';
import { Sparkles, Shirt } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Brand Logo */}
          <NavLink to="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl bg-gray-900 flex items-center justify-center text-white shadow-sm transition-transform duration-200 group-hover:scale-105">
              <Sparkles className="w-5 h-5 text-amber-300" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-lg tracking-tight text-gray-900">
                FitFusion
              </span>
              <span className="text-[10px] uppercase font-semibold tracking-wider text-gray-400 -mt-1">
                AI Virtual Try-On
              </span>
            </div>
          </NavLink>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-gray-900 bg-gray-100'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`
              }
            >
              Home
            </NavLink>

            <NavLink
              to="/try-on"
              className={({ isActive }) =>
                `px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors ${
                  isActive
                    ? 'text-white bg-gray-900 shadow-sm'
                    : 'text-gray-900 bg-gray-100 hover:bg-gray-200'
                }`
              }
            >
              <Shirt className="w-4 h-4" />
              <span>Try On</span>
            </NavLink>
          </nav>
        </div>
      </div>
    </header>
  );
}
