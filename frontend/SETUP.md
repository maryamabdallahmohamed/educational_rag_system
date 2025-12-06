# Environment Setup Instructions

## Create .env.local File

You need to create a `.env.local` file in the root of your project with the backend URL.

**Location**: `c:\Users\mohme\Downloads\ai-chat\.env.local`

**Content**:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## How to Create

### Option 1: Using PowerShell
```powershell
cd c:\Users\mohme\Downloads\ai-chat
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > .env.local
```

### Option 2: Manual Creation
1. Open your code editor
2. Create a new file named `.env.local` in `c:\Users\mohme\Downloads\ai-chat\`
3. Add the line: `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`
4. Save the file

## After Creating

Restart your Next.js development server:
```bash
npm run dev
```

The environment variable will now be available to the frontend application.
