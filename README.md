# 🌐 ZeroTrace Landing Page

<div align="center">

![ZeroTrace Banner](https://via.placeholder.com/800x200/1a1a2e/00d9ff?text=ZeroTrace+Landing+Page)

**Modern Landing Page for Professional Data Wiping Solution**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/zerotrace)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB?logo=react)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-4.4.0-646CFF?logo=vite)](https://vitejs.dev/)

[Live Demo](https://zerotrace.vercel.app) • [Documentation](../windows_tool/README.md) • [Download](../windows_tool/dist)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Deployment](#-deployment-on-vercel)
- [Components](#-components)
- [Styling](#-styling)
- [SEO](#-seo-optimization)
- [Performance](#-performance)

---

## 🎯 Overview

A stunning, modern landing page built with React and Vite, showcasing the ZeroTrace data wiping tool. Features a cyber-security aesthetic with neon accents, smooth animations, and responsive design.

### 🌟 Live Preview

Visit **[zerotrace.vercel.app](https://zerotrace.vercel.app)** to see it in action!

---

## ✨ Features

### 🎨 Design Features

✅ **Modern Cyber-Security Aesthetic**

- Dark theme with neon blue/purple gradients
- Glassmorphism effects
- Smooth hover animations
- Responsive mobile-first design

✅ **Premium UI Elements**

- Hero section with animated badge
- Feature cards with icons
- Multi-platform download buttons
- Sticky navigation (if implemented)

✅ **Micro-Interactions**

- Hover effects on buttons
- Card elevation on hover
- Smooth scroll animations
- Responsive transitions

### 📱 Responsive Design

- ✅ Desktop (1920px+)
- ✅ Laptop (1024px - 1920px)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (320px - 768px)

---

## 🛠️ Tech Stack

<div align="center">

### Frontend Framework

![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

### Styling & Design

![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![Google Fonts](https://img.shields.io/badge/Google_Fonts-4285F4?style=for-the-badge&logo=google&logoColor=white)

### Deployment

![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

</div>

### 📦 Dependencies

| Package       | Version | Purpose                 |
| ------------- | ------- | ----------------------- |
| **React**     | 18.2.0  | UI library              |
| **React-DOM** | 18.2.0  | DOM rendering           |
| **Vite**      | 4.4.0   | Build tool & dev server |

### 🎨 Fonts

- **Primary:** Inter (Google Fonts)
- **Fallback:** system-ui, -apple-system, BlinkMacSystemFont

---

## 🚀 Getting Started

### Prerequisites

- Node.js (v16.0.0 or higher)
- npm or yarn

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/zerotrace.git
cd zerotrace/website

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:5173` to see the site!

### Available Scripts

```json
{
  "dev": "vite", // Start dev server
  "build": "vite build", // Build for production
  "preview": "vite preview" // Preview production build
}
```

---

## 🌐 Deployment on Vercel

### Why Vercel?

**Vercel** is the perfect platform for React apps:

✅ **Zero Configuration**

- Auto-detects Vite/React
- Optimizes builds automatically
- No setup required

✅ **Lightning Fast**

- Global CDN (Edge Network)
- Sub-second cold starts
- HTTP/3 support

✅ **Developer Experience**

- Git integration (auto-deploy on push)
- Preview deployments for PRs
- Instant rollbacks

✅ **Free Tier Includes:**

- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Analytics

---

### Deployment Steps

#### Method 1: Deploy via GitHub (Recommended)

1. **Push to GitHub:**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/zerotrace.git
   git push -u origin main
   ```

2. **Connect to Vercel:**

   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Select `website/` as root directory
   - Click **Deploy**!

3. **Done!**
   - Your site is live at `https://zerotrace.vercel.app`
   - Every push to `main` auto-deploys
   - Preview URLs for each PR

#### Method 2: Deploy via CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to website folder
cd website

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: zerotrace
# - Directory: ./
# - Build command: npm run build
# - Output directory: dist
```

#### Method 3: One-Click Deploy

Click this button:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/zerotrace/tree/main/website)

---

### Vercel Configuration

Create `vercel.json` in `website/` folder:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

---

### Custom Domain Setup

1. Go to Vercel Dashboard → Your Project
2. Settings → Domains
3. Add your domain (e.g., `zerotrace.com`)
4. Update DNS records as instructed
5. HTTPS enabled automatically!

---

## 🧩 Components

### Component Architecture

```
src/
├── App.jsx               # Main app container
├── index.css             # Global styles & design tokens
└── components/
    ├── Hero.jsx          # Hero section with title & CTA
    ├── Features.jsx      # Feature grid (3 cards)
    ├── DownloadSection.jsx # Platform download buttons
    └── Footer.jsx        # Copyright & credits
```

### 📄 Detailed Component Breakdown

#### 1. **Hero Component** (`Hero.jsx`)

**Purpose:** First impression - captures attention

**Features:**

- Large title with gradient text
- "Open Source" badge with pulse animation
- Subtitle explaining the product
- Primary CTA button ("Download for Windows")
- Background gradient overlay

**Key CSS:**

```css
.hero-title {
  font-size: 4rem;
  background: linear-gradient(to right, #00d9ff, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

---

#### 2. **Features Component** (`Features.jsx`)

**Purpose:** Showcase key benefits in scannable format

**Structure:**

```
┌─────────────────────────────────────┐
│          FEATURES SECTION           │
├──────────┬──────────┬───────────────┤
│ Card 1   │ Card 2   │ Card 3       │
│ 🔒      │ 📜      │ 🌐          │
│ Secure  │ Proof   │ Cross-       │
│ Erase   │         │ Platform     │
└──────────┴──────────┴───────────────┘
```

**Each Card Includes:**

- Icon (emoji or SVG)
- Title
- Description
- Hover effect (elevation + glow)

**Key Features:**

- Grid layout (3 columns on desktop, stacks on mobile)
- Card design with backdrop blur
- Smooth hover animations

---

#### 3. **Download Section** (`DownloadSection.jsx`)

**Purpose:** Clear CTAs for each platform

**Platforms:**

```
┌─────────────────┬─────────────────┬─────────────────┐
│  🪟 Windows    │  🐧 Linux      │  📱 Android    │
│  Download MSI   │  Coming Soon    │  Coming Soon    │
└─────────────────┴─────────────────┴─────────────────┘
```

**Button States:**

- **Active** (Windows): Primary blue with hover effect
- **Disabled** (Linux/Android): Grayed out with "Coming Soon"

**Features:**

- Platform icons
- File size/version info
- Responsive stacking on mobile

---

#### 4. **Footer Component** (`Footer.jsx`)

**Purpose:** Credits and legal info

**Content:**

- Copyright notice
- Year auto-update
- Optional links (Privacy, Terms, GitHub)

---

## 🎨 Styling

### Design System

#### Color Palette

```css
:root {
  /* Primary Colors */
  --primary-bg: #0a0a0f; /* Deep space black */
  --secondary-bg: #1a1a2e; /* Dark navy */
  --accent-blue: #00d9ff; /* Neon cyan */
  --accent-purple: #a78bfa; /* Soft purple */

  /* Text Colors */
  --text-primary: #ffffff; /* White */
  --text-secondary: #94a3b8; /* Muted gray */

  /* UI Elements */
  --card-bg: rgba(26, 26, 46, 0.6); /* Semi-transparent */
  --border-color: rgba(0, 217, 255, 0.2);

  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #00d9ff 0%, #a78bfa 100%);
  --gradient-glow: radial-gradient(
    circle,
    rgba(0, 217, 255, 0.1) 0%,
    transparent 70%
  );
}
```

#### Typography

```css
/* Headings */
h1 {
  font-size: 3.5rem;
  font-weight: 800;
}
h2 {
  font-size: 2.5rem;
  font-weight: 700;
}
h3 {
  font-size: 1.75rem;
  font-weight: 600;
}

/* Body */
body {
  font-size: 1rem;
  line-height: 1.6;
}
```

#### Spacing Scale

```css
--space-xs: 0.5rem; /* 8px */
--space-sm: 1rem; /* 16px */
--space-md: 1.5rem; /* 24px */
--space-lg: 2rem; /* 32px */
--space-xl: 3rem; /* 48px */
--space-2xl: 4rem; /* 64px */
```

---

### Animations

#### Hover Effects

```css
/* Button Hover */
.cta-button {
  transition: all 0.3s ease;
}
.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 40px rgba(0, 217, 255, 0.4);
}

/* Card Hover */
.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 60px rgba(0, 217, 255, 0.15);
}
```

#### Pulse Animation

```css
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.badge {
  animation: pulse 2s ease-in-out infinite;
}
```

---

## 🔍 SEO Optimization

### Meta Tags

Already implemented in `index.html`:

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta
    name="description"
    content="ZeroTrace - Professional data wiping tool with military-grade security"
  />
  <meta
    name="keywords"
    content="data wipe, secure erase, DoD, NIST, data destruction"
  />
  <meta property="og:title" content="ZeroTrace - Secure Data Wiping" />
  <meta
    property="og:description"
    content="Professional data destruction software"
  />
  <meta property="og:type" content="website" />
  <title>ZeroTrace - Secure Data Wiping Tool</title>
</head>
```

### Performance SEO

- ✅ Fast initial load (<1s on Vercel)
- ✅ Semantic HTML5 elements
- ✅ Descriptive alt text for images
- ✅ Clean URL structure
- ✅ Mobile-responsive (Google ranking factor)

---

## ⚡ Performance

### Lighthouse Scores (Target)

```
Performance:  95+  🟢
Accessibility: 95+  🟢
Best Practices: 100 🟢
SEO:          100 🟢
```

### Optimization Techniques

✅ **Code Splitting**

- Vite automatically splits vendor and app code
- Lazy loading for components

✅ **Asset Optimization**

- Minified CSS/JS
- Tree-shaking (unused code removed)
- Gzip compression on Vercel

✅ **Caching**

- Vercel CDN caches static assets
- Browser caching headers

✅ **Font Optimization**

- Google Fonts with `font-display: swap`
- Preconnect to fonts.googleapis.com

---

## 📊 Analytics (Optional)

### Add Vercel Analytics

```bash
npm install @vercel/analytics
```

```jsx
// src/main.jsx
import { inject } from "@vercel/analytics";

inject();
```

**Get Insights:**

- Page views
- User locations
- Performance metrics
- Real user monitoring

---

## 🔧 Customization

### Change Colors

Edit `src/index.css`:

```css
:root {
  --accent-blue: #your-color-here;
  --accent-purple: #your-color-here;
}
```

### Add Sections

Create new component:

```jsx
// src/components/Testimonials.jsx
export default function Testimonials() {
  return <section className="testimonials">{/* Your content */}</section>;
}
```

Import in `App.jsx`:

```jsx
import Testimonials from "./components/Testimonials";

// In JSX:
<Testimonials />;
```

---

## 📸 Screenshots

### Desktop View

![Desktop Screenshot](https://via.placeholder.com/800x600/1a1a2e/00d9ff?text=Desktop+View)

### Mobile View

![Mobile Screenshot](https://via.placeholder.com/375x667/1a1a2e/00d9ff?text=Mobile+View)

---

## 🐛 Troubleshooting

### Dev Server Not Starting

```bash
# Clear cache
rm -rf node_modules
npm install
npm run dev
```

### Vercel Deployment Failed

Check:

1. Build command: `npm run build`
2. Output directory: `dist`
3. Node version: 16.x or higher

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) file

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

- 🌐 Website: [zerotrace.vercel.app](https://zerotrace.vercel.app)
- 📧 Email: support@zerotrace.com
- 💬 Discord: [Join our server](https://discord.gg/zerotrace)

---

<div align="center">

**Built with ❤️ using React, Vite, and Vercel**

[![Star on GitHub](https://img.shields.io/github/stars/yourusername/zerotrace?style=social)](https://github.com/yourusername/zerotrace)

[⬆ Back to Top](#-zerotrace-landing-page)

</div>
