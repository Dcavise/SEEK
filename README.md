# SEEK Property Platform

A comprehensive Texas property search platform designed for real estate investment analysis. Search by city name to find parcels with enhanced FOIA data including zoning by right, occupancy class, and fire sprinkler information.

**Current Status**: Phase 2 - FOIA Integration (Task 1.1 Complete, Task 1.2 Next)

## 🎯 Purpose

**Target Users**: 5-15 internal real estate team members  
**Mission**: Find investment properties with specific zoning, occupancy, and safety characteristics

## 🚀 Quick Start

### For New Developers

```bash
# Clone the repository  
git clone https://github.com/Dcavise/SEEK.git
cd SEEK

# Run automated setup
./scripts/dev-setup.sh

# Start development servers
make dev
```

Visit http://localhost:5173 to see the frontend.

### Manual Setup

1. **Environment Setup**
   ```bash
   # Create .env file with your Supabase credentials
   cp .env.example .env  # Edit with your credentials
   
   # Install Python dependencies
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd seek-property-platform
   npm install
   cd ..
   ```

2. **Database Setup**
   ```bash
   make setup-db
   ```

3. **Import Data** (Optional)
   ```bash
   make import-data  # Imports all 182 Texas counties
   # or
   make import-single COUNTY=bexar  # Import single county
   ```

## 🏗️ Architecture

### Backend (Python)
- **Database**: Supabase (PostgreSQL) with 700k+ property records
- **Data Pipeline**: Automated import from 182 Texas county CSV files
- **Key Features**: Property search, FOIA data matching, performance monitoring

### Frontend (React + TypeScript)
- **Framework**: React 18.3.1 with Vite
- **UI**: Radix UI + shadcn/ui components
- **Maps**: Mapbox GL integration
- **State**: React Query for data management

### Database Schema
```sql
-- Core hierarchy
states → counties → cities → parcels

-- Key tables
parcels (
  parcel_number, address, city_id, county_id,
  owner_name, property_value, lot_size,
  -- FOIA enhancement columns
  zoned_by_right, occupancy_class, fire_sprinklers
)
```

## 📁 Project Structure

```
SEEK/
├── 🐍 Backend (Python)
│   ├── venv/                    # Virtual environment
│   ├── *.py                     # Data import scripts
│   ├── *.sql                    # Database schemas & queries
│   └── data/                    # Texas county data
│       ├── OriginalCSV/         # 182 county CSV files
│       ├── CleanedCsv/          # Normalized data
│       └── NormalizeLogs/       # Processing logs
│
├── ⚛️ Frontend (React)
│   └── seek-property-platform/
│       ├── src/
│       │   ├── components/      # UI components
│       │   ├── pages/          # Route pages  
│       │   ├── types/          # TypeScript definitions
│       │   └── lib/            # Utilities
│       └── package.json
│
├── 🛠️ Development Tools
│   ├── Makefile                # Development commands
│   ├── scripts/dev-setup.sh    # Automated setup
│   ├── .vscode/                # VS Code configuration
│   └── requirements.txt        # Python dependencies
│
└── 📋 Documentation
    ├── README.md               # This file (main documentation)
    ├── PROJECT_MEMORY.md       # Technical specifications
    ├── CLAUDE.md               # Claude Code session memory
    ├── .clauderc               # Claude Code configuration
    └── docs/archive/           # Historical documentation
```

## 🔧 Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start both backend monitoring and frontend |
| `make install` | Install all dependencies |
| `make test` | Run tests and linting |
| `make build` | Build frontend for production |
| `make import-data` | Import all Texas county data |
| `make health` | Run system health checks |
| `make clean` | Clean build artifacts |
| `make help` | Show all available commands |

## 🗂️ Key Features

### Property Search
- Search by city name across Texas
- Filter by zoning, occupancy class, fire sprinklers
- Interactive map visualization with property markers
- Detailed property information panels

### Data Management
- Import from 182 Texas county CSV files
- FOIA data integration and matching
- Automated data normalization and cleaning
- Performance monitoring and optimization

### Team Collaboration
- User assignment tracking
- Activity audit logs
- Team performance analytics

## 🎨 Technology Stack

### Backend
- **Python 3.13** with virtual environment
- **Supabase** (PostgreSQL) for database
- **Pandas** for data processing
- **Fuzzy matching** for address resolution

### Frontend  
- **React 18.3.1** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **Mapbox GL** for interactive maps
- **React Query** for state management

### Development
- **VS Code** optimized configuration
- **ESLint + Prettier** for code quality
- **Make** for task automation
- **Git** with conventional commits

## 📊 Database Status

- **701,089 parcels** imported and indexed (Bexar County complete)
- **923 cities** across multiple Texas counties  
- **Sub-25ms search** performance with optimized indexes
- **Row Level Security** implemented with role-based access
- **Automated performance monitoring** with health checks
- **FOIA-ready schema** for Phase 2 integration

### Current Performance Metrics
| Query Type | Performance | Status |
|------------|-------------|--------|
| City Search | <25ms | ✅ Optimized |
| Parcel Lookup | <10ms | ✅ Optimized |
| FOIA Filtering | <25ms | ✅ Ready |

## 🔍 Search Capabilities

- **City-based search**: Find properties by Texas city name
- **FOIA filtering**: Filter by zoning by right, occupancy class, fire sprinklers
- **Address matching**: Fuzzy matching for address-based FOIA integration
- **Geospatial queries**: Map-based property discovery
- **Bulk operations**: Team assignment and batch processing

## 🚀 Deployment

```bash
# Prepare for deployment
make deploy-prep

# Build production assets
make prod-build

# Push to repository
git push origin main
```

## 🎯 Current Status & Next Steps

### ✅ Completed (Phase 1)
- Database foundation with 701,089 parcels
- Optimized bulk import pipeline (4,477 records/sec)
- Performance-tuned indexes and queries (<25ms)
- Row Level Security and user authentication ready
- Professional developer experience with Makefile and scripts

### ✅ Phase 2 - FOIA Integration (In Progress)
- **Task 1.1 COMPLETE**: FOIA Data Upload Interface
  - React FileUpload component with drag-and-drop functionality
  - CSV/Excel validation and real-time data preview
  - Integration with column mapping workflow
  - Tested successfully with real FOIA building permit data

### 🚧 Next Phase Tasks
- **Task 1.2 NEXT**: Multi-Tiered Address Matching System
  - Exact parcel number matching (PB01-02745 → parcel records)
  - Normalized address matching with fuzzy logic
  - Confidence scoring and manual review queue
- **Tasks 1.3-1.5**: Property filtering, validation, and database integration
- **Phase 3**: Team collaboration features
- **Phase 4**: Advanced analytics and reporting

## 📝 Development Notes

- **Virtual Environment**: Always activate Python venv before running scripts
- **Environment Variables**: Keep .env file secure and never commit
- **Database Performance**: Monitor query performance with built-in tools
- **FOIA Integration**: Match on parcel number → address → fuzzy matching
- **Data Pipeline**: Supports incremental updates and error recovery

## 🤝 Contributing

1. **Setup**: Run `./scripts/dev-setup.sh` for automated environment setup
2. **Development**: Use `make dev` for active development
3. **Testing**: Run `make test` before committing
4. **Code Quality**: VS Code will auto-format and lint code

## 📈 Performance

- **Search Speed**: Sub-25ms property search across 701k+ records
- **Import Speed**: 4,477 records/second with bulk optimization (221x improvement)
- **Memory Usage**: Efficient batch processing with 10k record batches
- **Database Size**: ~262MB with indexes and normalized data

### Performance Optimization History
- **Original Import**: 4 records/second (48+ hours estimated)
- **Optimized Import**: 4,477 records/second (2.6 minutes actual)
- **Query Performance**: 70-90% improvement with critical indexes

## 🛡️ Security

- **Row Level Security** enabled on all tables
- **Environment variables** for sensitive credentials
- **API key management** through Supabase
- **User authentication** and role-based access

## 📞 Support

For technical questions or setup issues:
1. Check `make help` for available commands
2. Review logs in `data/NormalizeLogs/`
3. Run `make health` for system diagnostics
4. Check VS Code tasks for common operations

---

**Built with**: Python 🐍 + React ⚛️ + Supabase 🗄️ + Love ❤️