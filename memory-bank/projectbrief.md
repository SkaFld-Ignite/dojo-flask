# PROJECT BRIEF - DOJO FLASK

> **Foundation document establishing project context and core architecture**

## 🎯 PROJECT OVERVIEW
**Project Name:** dojo-flask  
**Repository:** /Users/mikebelloli/Development/projects/dojo-flask  
**Architecture:** Hybrid Flask API + Next.js Frontend  

## 🏗️ DETECTED ARCHITECTURE

### Backend (API)
- **Framework:** Flask (Python)
- **Location:** `/api/`
- **Entry Point:** `index.py`
- **Purpose:** API endpoints and server-side logic

### Frontend (App)
- **Framework:** Next.js (React/TypeScript)
- **Location:** `/app/`
- **Build Tool:** Likely Vite or Next.js built-in
- **Styling:** Global CSS + Tailwind CSS

## 📁 PROJECT STRUCTURE
```
dojo-flask/
├── api/                 # Flask backend
│   └── index.py
├── app/                 # Next.js frontend
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── public/              # Static assets
├── memory-bank/         # Memory Bank system
└── config files         # Package manifests, build configs
```

## 🎭 PROJECT STAGE
**Current Stage:** Initial Setup/Analysis  
**Development Phase:** Pre-implementation  
**Goal:** Establish clear development workflow and implement requested features  

## 🔧 TECHNICAL STACK

### Confirmed Technologies
- **Backend:** Python + Flask
- **Frontend:** React + Next.js + TypeScript
- **Styling:** Tailwind CSS
- **Package Manager:** npm/pnpm (detected pnpm-lock.yaml)

### Configuration Files Present
- `package.json` - Node.js dependencies
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.js` - Tailwind CSS setup
- `next.config.js` - Next.js configuration
- `requirements.txt` - Python dependencies

## 📋 INITIAL OBSERVATIONS
- Hybrid architecture suggests full-stack development approach
- Both backend and frontend appear to be in early setup stage
- Modern development stack with TypeScript and Tailwind
- Package manager files suggest active Node.js ecosystem 