# SEEK - Future Schools Property Management Platform

## Project Overview

SEEK is a comprehensive property management platform designed for analyzing and managing educational properties. The application provides powerful tools for property search, filtering, visualization, and compliance tracking.

### Key Features

- **Interactive Property Search**: Search by city or address to discover educational properties
- **Advanced Mapping**: MapBox-powered interactive maps with property visualization and heatmap support
- **Smart Filtering**: Multi-criteria filtering with live preview and quick filter overlays
- **Property Management**: Detailed property information including compliance tracking and assignment management  
- **Table View**: Comprehensive data table with selection and export capabilities
- **Data Import**: CSV import functionality with column mapping and validation
- **Analytics Dashboard**: Performance metrics and reporting tools
- **Team Management**: User assignments and collaboration features

## Architecture

### Frontend Structure
```
src/
├── components/           # Reusable UI components
│   ├── filters/         # Filter panels and overlays
│   ├── import/          # Data import components
│   ├── layout/          # Navigation and layout
│   ├── map/             # MapBox integration
│   ├── property/        # Property management UI
│   ├── search/          # Search functionality
│   ├── shared/          # Common components
│   ├── table/           # Data table components
│   └── ui/              # shadcn/ui component library
├── data/                # Mock data and fixtures
├── hooks/               # Custom React hooks
├── lib/                 # Utility functions
├── pages/               # Route components
├── types/               # TypeScript definitions
└── main.tsx            # Application entry point
```

## Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with shadcn/ui components
- **Mapping**: MapBox GL JS
- **Routing**: React Router v6
- **State Management**: React hooks and context
- **Form Handling**: React Hook Form with Zod validation
- **Charts**: Recharts
- **Development**: ESLint, TypeScript compiler

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or bun package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project directory
cd seek-property-platform

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run build:dev    # Build in development mode
npm run lint         # Run ESLint
npm run preview      # Preview production build
```

## Development

### Project Structure
The application follows a modular component architecture with clear separation of concerns:

- **Components**: Organized by feature area (filters, map, property, etc.)
- **Pages**: Route-level components handling page logic
- **Hooks**: Custom hooks for shared logic
- **Types**: Centralized TypeScript definitions
- **Data**: Mock data and API integrations

### Key Components
- `MapView`: Interactive MapBox-powered property visualization
- `PropertyPanel`: Detailed property information and editing
- `FilterPanel`: Advanced filtering with live preview
- `PropertyTable`: Data table with sorting and selection
- `SearchOverlay`: City and address search functionality

## Property Data Model

Properties include comprehensive information:
- Location data (address, coordinates, zoning)
- Compliance tracking (fire sprinklers, occupancy, zoning by right)
- Assignment and workflow status
- External system integration
- Historical tracking and notes

## Contributing

1. Follow the existing code structure and naming conventions
2. Use TypeScript for all new code
3. Implement responsive design with Tailwind CSS
4. Add appropriate error handling and loading states
5. Run linting before submitting changes

## License

This project is private and proprietary.
