# Web ADB Tool - Frontend

React + TypeScript frontend for the Web ADB Tool, providing a modern web interface for Android device management.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Material-UI (MUI)** - Component library
- **Vite** - Build tool and dev server
- **Zustand** - State management
- **Axios** - HTTP client
- **Socket.IO Client** - WebSocket communication
- **React Router** - Routing
- **Vitest** - Testing framework

## Prerequisites

- Node.js 18+ and npm 9+
- Backend server running on `http://localhost:5000`

## Installation

```bash
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Building

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Testing

Run tests:

```bash
npm test
```

Run tests with UI:

```bash
npm run test:ui
```

Generate coverage report:

```bash
npm run test:coverage
```

## Code Quality

Type checking:

```bash
npm run type-check
```

Linting:

```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── DeviceManager/   # Device management UI
│   │   ├── ScreenOperations/ # Screen mirroring, recording, screenshots
│   │   ├── LogViewer/       # Log display and filtering
│   │   ├── AppManager/      # Application management
│   │   ├── CustomButtons/   # Custom command buttons
│   │   ├── AIAssistant/     # AI assistant chat interface
│   │   └── common/          # Shared components
│   ├── services/            # API and WebSocket clients
│   │   ├── api.ts           # HTTP API client
│   │   └── websocket.ts     # WebSocket client
│   ├── store/               # State management (Zustand)
│   │   ├── deviceStore.ts   # Device state
│   │   ├── configStore.ts   # Configuration state
│   │   └── uiStore.ts       # UI state
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   ├── hooks/               # Custom React hooks
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # Application entry point
│   └── theme.ts             # Material-UI theme configuration
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_BASE_URL=http://localhost:5000
VITE_WS_URL=http://localhost:5000
```

## Features

- **Device Management**: Connect, disconnect, and view device information
- **Screen Operations**: Real-time screen mirroring, recording, and screenshots
- **Log Viewer**: Real-time log streaming with filtering
- **App Management**: Install, uninstall, start, stop applications
- **Custom Commands**: Create and execute custom ADB commands
- **AI Assistant**: Natural language command generation and error analysis
- **Responsive Design**: Works on desktop and tablet devices
- **Dark/Light Theme**: Theme switching support
