# SEEK Property Platform

A comprehensive Texas property search platform designed for real estate investment analysis. Search by city name to find parcels with enhanced FOIA data including zoning by right, occupancy class, and fire sprinkler information.

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
    ├── README.md               # This file
    ├── CLAUDE.md              # Project memory
    └── PROJECT_MEMORY.md      # Technical details
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

- **700k+ parcels** imported and indexed
- **182 Texas counties** with normalized data
- **Sub-second search** performance
- **Row Level Security** implemented
- **Automated backups** configured

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

- **Search Speed**: Sub-second property search across 700k records
- **Import Speed**: ~10k records per minute with optimization
- **Memory Usage**: Efficient batch processing with progress tracking
- **Database Size**: ~50GB with indexes and normalized data

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