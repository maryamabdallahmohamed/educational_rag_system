# Iris - AI Vision Assistant

**Iris** is an advanced AI-powered chat application designed to help blind and visually impaired students interact with documents through natural language. The application provides document upload, question-answering, summarization, and advanced AI agent processing capabilities.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [API Integration](#api-integration)
- [Components Overview](#components-overview)
- [Styling & Design](#styling--design)

---

## 🎯 Overview

Iris is a Next.js-based web application that serves as a frontend for a RAG (Retrieval-Augmented Generation) backend system. It allows users to:

- Upload documents (PDF, TXT, DOC, DOCX, MD, JSON)
- Ask questions about uploaded documents
- Get automatic document summaries
- Process documents with a CPA (Content Processing Agent)
- Maintain conversation history
- Experience a modern, accessible UI with dark mode aesthetics

---

## ✨ Features

### 1. **Document Upload**
- Drag-and-drop file upload interface
- Support for multiple file formats
- Automatic JSON to TXT conversion
- Real-time upload status feedback

### 2. **Chat Interface**
- Real-time question answering
- Message history with timestamps
- Auto-scrolling to latest messages
- Loading indicators for AI responses

### 3. **Quick Actions**
- **Summarize Document**: Get instant document summaries
- **Run CPA Agent**: Advanced content analysis

### 4. **Responsive Design**
- Mobile-friendly sidebar navigation
- Adaptive layouts for all screen sizes
- Touch-optimized interactions

### 5. **Modern UI/UX**
- Glassmorphism effects
- Smooth animations with Framer Motion
- Gradient accents and hover effects
- Dark mode optimized

---

## 🛠 Technology Stack

### Frontend Framework
- **Next.js 15.5.6** - React framework with App Router
- **React 18.3.1** - UI library
- **TypeScript 5** - Type safety

### Styling
- **Tailwind CSS 4.1.9** - Utility-first CSS framework
- **Tailwind Animate** - Animation utilities
- **PostCSS** - CSS processing

### UI Components
- **Radix UI** - Accessible component primitives
  - Dialog, Dropdown, Popover, Tabs, Toast, and more
- **Lucide React** - Icon library
- **Framer Motion** - Animation library
- **GSAP** - Advanced animations

### Forms & Validation
- **React Hook Form 7.60.0** - Form management
- **Zod 3.25.76** - Schema validation
- **@hookform/resolvers** - Form validation integration

### Fonts
- **Geist Sans & Mono** - Modern font families
- **Doto** - Google Font for special typography

### Additional Libraries
- **cmdk** - Command menu
- **date-fns** - Date utilities
- **sonner** - Toast notifications
- **recharts** - Charts (if needed)
- **react-resizable-panels** - Resizable layouts

---

## 📁 Project Structure

```
ai-chat/
├── app/                          # Next.js App Router
│   ├── about/                    # About page
│   ├── chat/                     # Main chat interface
│   │   └── page.tsx              # Chat page with sidebar
│   ├── contact/                  # Contact page
│   ├── services/                 # Services page
│   ├── upload/                   # Document upload page
│   │   └── page.tsx              # Upload interface
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout with Navbar
│   └── page.tsx                  # Landing page
│
├── components/                   # React components
│   ├── ui/                       # Radix UI components (58 files)
│   ├── Navbar.tsx                # Navigation bar
│   ├── chat-card.tsx             # Chat card component
│   ├── chat-interface.tsx        # Chat interface
│   ├── chat-sidebar.tsx          # Sidebar with conversations
│   ├── hero-buttons.tsx          # Landing page CTA buttons
│   ├── simple-chat-interface.tsx # Simplified chat UI
│   └── theme-provider.tsx        # Theme context
│
├── hooks/                        # Custom React hooks
│   ├── use-mobile.ts             # Mobile detection hook
│   ├── use-rag-api.ts            # Backend API integration
│   └── use-toast.ts              # Toast notifications hook
│
├── lib/                          # Utility functions
│   └── utils.ts                  # Helper utilities
│
├── public/                       # Static assets
│   ├── file.svg
│   └── window.svg
│
├── styles/                       # Additional styles
│   └── globals.css
│
├── .env.local                    # Environment variables
├── .gitignore                    # Git ignore rules
├── components.json               # Shadcn/UI config
├── next.config.mjs               # Next.js configuration
├── package.json                  # Dependencies
├── postcss.config.mjs            # PostCSS config
├── SETUP.md                      # Setup instructions
└── tsconfig.json                 # TypeScript config
```

---

## 🚀 Setup Instructions

### Prerequisites
- Node.js 18+ installed
- npm or pnpm package manager
- Backend RAG server running on `http://localhost:8000`

### Installation

1. **Clone the repository** (if applicable)
   ```bash
   cd c:\Users\mohme\Downloads\ai-chat
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   
   Create a `.env.local` file in the root directory:
   ```env
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Open the application**
   
   Navigate to `http://localhost:3000` in your browser

### Build for Production

```bash
npm run build
npm start
```

---

## 💡 Usage

### 1. Upload a Document

1. Navigate to the **Upload** page via the sidebar or direct link
2. Drag and drop a file or click to browse
3. Supported formats: PDF, TXT, DOC, DOCX, MD, JSON
4. Click **Upload Document**
5. Wait for confirmation, then navigate to **Chat**

### 2. Ask Questions

1. Go to the **Chat** page
2. Type your question in the input box
3. Press Enter or click the Send button
4. View the AI's response in the chat interface

### 3. Quick Actions

- **Summarize Document**: Click the "Summarize Document" button for an instant summary
- **Run CPA Agent**: Click "Run CPA Agent" for advanced content processing

### 4. Conversation History

- View past conversations in the sidebar (desktop)
- Click on a conversation to load it (feature placeholder)

---

## 🔌 API Integration

The application communicates with a backend RAG server through the `use-rag-api.ts` hook.

### Backend Endpoints

All API calls are proxied through Next.js to avoid CORS issues:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload` | POST | Upload document files |
| `/api/qa` | POST | Ask questions about documents |
| `/api/summarize` | POST | Get document summaries |
| `/api/cpa_agent` | POST | Run CPA agent processing |

### Next.js API Proxy

Configured in `next.config.mjs`:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ]
}
```

### Hook: `useRAGApi`

Located in `hooks/use-rag-api.ts`, this custom hook provides:

- `uploadDocument(file)` - Upload a document
- `askQuestion(query)` - Ask a question
- `summarizeDocument()` - Get summary
- `runCPAAgent()` - Run CPA agent
- `isLoading` - Loading state
- `error` - Error state

**Example Usage:**

```typescript
const { askQuestion, isLoading } = useRAGApi();

const handleSubmit = async () => {
  const response = await askQuestion("What is this document about?");
  console.log(response.result);
};
```

---

## 🧩 Components Overview

### Pages

#### **Landing Page** (`app/page.tsx`)
- Hero section with gradient backgrounds
- Feature cards showcasing capabilities
- Call-to-action buttons
- Footer with links

#### **Chat Page** (`app/chat/page.tsx`)
- Split layout with sidebar and chat interface
- Uses `ChatSidebar` and `SimpleChatInterface`
- Responsive design with mobile adaptations

#### **Upload Page** (`app/upload/page.tsx`)
- Drag-and-drop file upload
- File type validation
- Upload progress and status feedback
- Navigation to chat after successful upload

### Key Components

#### **Navbar** (`components/Navbar.tsx`)
- Fixed floating navigation bar
- Smooth scroll to sections
- Mobile sheet menu
- Animated hover effects

#### **ChatSidebar** (`components/chat-sidebar.tsx`)
- Conversation history list
- New chat button
- Upload document link
- Settings and profile buttons
- Mobile overlay version

#### **SimpleChatInterface** (`components/simple-chat-interface.tsx`)
- Message display with user/assistant distinction
- Auto-scrolling to latest messages
- Quick action buttons (Summarize, CPA Agent)
- Textarea input with Enter-to-send
- Loading indicators

### UI Components (`components/ui/`)

Built with Radix UI primitives:
- `button.tsx` - Button component
- `textarea.tsx` - Text input
- `dialog.tsx` - Modal dialogs
- `sheet.tsx` - Slide-out panels
- `toast.tsx` - Notifications
- And 50+ more components

---

## 🎨 Styling & Design

### Design System

**Color Palette:**
- Background: `#050505`, `#0A0A0A`, `#1A1A1A`
- Primary: Indigo (`indigo-500`, `indigo-600`)
- Secondary: Purple (`purple-500`)
- Text: White with opacity variations
- Borders: `white/5`, `white/10`, `white/20`

**Typography:**
- Primary: Geist Sans
- Monospace: Geist Mono
- Accent: Doto (Google Font)

**Effects:**
- Glassmorphism: `backdrop-blur-md`, `bg-black/30`
- Gradients: `from-indigo-500/10 via-purple-500/5`
- Shadows: `shadow-lg`, `shadow-indigo-500/20`
- Animations: Framer Motion for smooth transitions

### Accessibility Features

- Semantic HTML structure
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast text
- Focus indicators
- Responsive touch targets

---

## 📝 Configuration Files

### `next.config.mjs`
- Allowed dev origins for network access
- API rewrites for backend proxy

### `tsconfig.json`
- TypeScript compiler options
- Path aliases (`@/*` → `./`)
- Strict mode enabled

### `tailwind.config.js` (via `components.json`)
- Custom color schemes
- Animation utilities
- Plugin configurations

### `package.json`
- Scripts: `dev`, `build`, `start`, `lint`
- Dependencies and versions

---

## 🔧 Development

### Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm start        # Start production server
npm run lint     # Run ESLint
```

### Environment Variables

- `NEXT_PUBLIC_BACKEND_URL` - Backend API URL (optional, uses proxy by default)

### Adding New Features

1. Create components in `components/`
2. Add pages in `app/`
3. Create custom hooks in `hooks/`
4. Update API integration in `use-rag-api.ts`

---

## 🐛 Known Issues & Solutions

### Scroll Issues
- Fixed by using proper flex layout in chat interface
- `min-h-0` on flex containers for proper overflow

### CORS Issues
- Solved using Next.js API rewrites
- Backend calls go through `/api/*` proxy

### JSON File Upload
- Automatically converted to TXT format
- Handled in `use-rag-api.ts` upload function

---

## 📄 License

This project is private and not licensed for public use.

---

## 👥 Contributors

Developed for accessibility and education purposes.

---

## 📞 Support

For issues or questions, refer to the backend documentation or contact the development team.

---

**Built with ❤️ using Next.js, React, and Tailwind CSS**
