# Primer Seek: Microschool Property Intelligence Platform
## Product Requirements Document v2.0

---

## 1. Project Objectives and Vision

### 1.1 Mission Statement

Primer Seek is a specialized property intelligence platform designed to identify and qualify viable microschool locations across Texas, Alabama, and Florida markets. The platform transforms fragmented government data into actionable property insights, enabling Primer's Real Estate team to efficiently locate the rare properties (~0.1% of market) that meet strict educational compliance requirements.

### 1.2 Primary Objectives

#### Property Intelligence Engine
- Consolidate 15+ million Regrid parcel records with targeted FOIA government data
- Implement sophisticated compliance scoring for educational property qualification
- Enable rapid identification of properties suitable for microschool operations

#### Regulatory Compliance Platform
- Track fire sprinkler requirements, occupancy classifications, and zoning by-right status
- Monitor regulatory changes affecting educational property development
- Provide confidence scoring for compliance-critical decisions

#### Off-Market Property Sourcing
- Identify qualified properties before they hit commercial market
- Enable proactive outreach to property owners with viable educational spaces
- Track relationship intelligence for long-term sourcing strategy

### 1.3 Business Impact Goals

#### Market Access Acceleration
- Enable 20 signed leases by December 2025 across Texas markets
- Reduce property qualification time from weeks to hours
- Increase qualified property discovery rate by 10x
- Enable systematic sourcing across 50+ Texas markets simultaneously

#### Risk Mitigation
- Eliminate false positives in property qualification (zero tolerance for sprinkler/zoning errors)
- Provide audit trail for compliance decisions
- Enable rapid response to regulatory changes

#### Competitive Advantage
- Build proprietary intelligence database not available to competitors
- Establish relationships with property owners in advance of market activity
- Create systematic approach to finding "needle in haystack" properties

---

## 2. Target Users and Core Workflows

### 2.1 Primary User: Primer Real Estate Team

#### User Profile
- **Role:** Real Estate Analysts and Directors at Primer Education
- **Mission:** Source asset-light properties for microschool lease agreements
- **Challenge:** Finding properties that meet strict educational compliance requirements
- **Success Metric:** Enable 20 signed leases by December 2025

#### Key Characteristics
- Deep knowledge of educational real estate requirements
- Comfortable with complex data analysis and compliance verification
- Need to move quickly on rare qualified opportunities
- Manage relationships with property owners and government officials

### 2.2 Core Use Cases

#### UC-001: Microschool Property Discovery

```
Actor: Real Estate Analyst
Goal: Identify all potentially viable microschool properties in target market
Precondition: City has been prioritized for Primer expansion

Flow:
1. Analyst searches for city (e.g., "Plano, TX")
2. System displays compliance-focused map with property qualification scoring
3. Analyst applies microschool-specific filters (no sprinklers required, E-occupancy compatible)
4. System shows ~12 qualified properties from 50,000+ total city properties
5. Analyst reviews compliance confidence scores and regulatory risk assessments
6. System provides property owner intelligence for off-market outreach strategy

Success Criteria:
- Sub-10 second response time for any Texas city
- 95%+ accuracy in compliance qualification
- Clear risk indicators for each property
```

#### UC-002: Compliance Verification Deep Dive

```
Actor: Real Estate Director
Goal: Verify property compliance before lease negotiations
Precondition: Property identified as potentially qualified

Flow:
1. Director selects high-priority property from qualified pipeline
2. System displays comprehensive compliance dashboard with data source attribution
3. Director reviews fire code analysis, zoning verification, and occupancy requirements
4. System shows FOIA data freshness and confidence indicators
5. Director identifies any compliance barriers or required approvals
6. System generates compliance summary for legal/facilities review

Success Criteria:
- Complete compliance picture with source attribution
- Clear identification of any regulatory barriers
- Confidence scoring for compliance decisions
```

#### UC-003: Regulatory Intelligence Monitoring

```
Actor: Real Estate Team
Goal: Stay ahead of regulatory changes affecting qualified properties
Precondition: Properties in pipeline across multiple jurisdictions

Flow:
1. System monitors fire code, zoning, and educational regulation changes
2. Automated alerts identify properties potentially affected by regulatory updates
3. Team reviews impact analysis for properties in acquisition pipeline
4. System provides recommended actions (re-verification, stakeholder outreach)
5. Team updates property risk assessments based on regulatory intelligence

Success Criteria:
- Real-time alerts for relevant regulatory changes
- Impact analysis for properties in pipeline
- Proactive risk management capabilities
```

#### UC-004: Off-Market Property Sourcing

```
Actor: Real Estate Analyst
Goal: Identify and contact owners of qualified properties before market listing
Precondition: Qualified properties identified through platform analysis

Flow:
1. Analyst identifies qualified property not currently for lease
2. System provides property owner intelligence (contact info, portfolio analysis)
3. Analyst reviews owner's leasing history and decision-making patterns
4. System suggests outreach strategy based on owner profile
5. Analyst initiates relationship building with long-term sourcing approach
6. System tracks relationship progress and follow-up scheduling

Success Criteria:
- Complete property owner intelligence
- Relationship tracking and follow-up management
- Higher success rate for off-market lease negotiations
```

---

## 3. Core Platform Features

### 3.1 Microschool Property Intelligence Engine

#### Compliance-First Property Scoring
- **Sprinkler Analysis:** Definitive determination of fire sprinkler requirements for E-occupancy conversion
- **Zoning Verification:** By-right educational use confirmation with conditional use permit analysis
- **Occupancy Classification:** Current occupancy assessment and E-occupancy conversion pathway
- **Building Code Compliance:** ADA accessibility, egress requirements, square footage analysis

#### Qualification Pipeline Management

```
Tier 1: Existing Educational Occupancy, Zoned by Right, over 6,000 Square Feet
- Highest priority properties ready for immediate lease negotiations
- Minimal conversion requirements for microschool operation

Tier 2: Zoned by Right, Not Existing Educational Occupancy, Has Fire Sprinkler
- Viable properties requiring occupancy conversion
- Fire safety infrastructure already in place

Tier 3: Zoned by Right, Not Existing Educational Occupancy, Unknown Fire Sprinklers
- Properties requiring sprinkler system investigation
- Potential qualification pending fire safety verification
```

#### Risk Assessment Dashboard
- **Compliance Confidence Scoring:** 0-100 score based on data completeness and verification
- **Regulatory Risk Indicators:** Pending zoning changes, fire code updates, educational regulations
- **Data Freshness Tracking:** Age of critical compliance data with refresh recommendations

### 3.2 Advanced FOIA Data Integration System

#### Intelligent Column Mapping
- **Template-Based Mapping:** Saved configurations for recurring FOIA sources (Dallas Fire Dept, Austin Building Permits)
- **Semantic Recognition:** AI-assisted mapping of non-standard column names to canonical schema
- **Conflict Resolution:** Handling contradictory data from multiple government sources

#### Government Data Source Management

```
Fire Department FOIAs:
- Sprinkler system requirements and installation records
- Fire alarm compliance and inspection history
- Occupancy classifications and capacity limitations
- Emergency access and egress documentation

Building Department FOIAs:
- Square footage verification and floor plans
- ADA compliance modifications and accessibility features
- Structural engineering reports and building condition
- HVAC capacity and mechanical systems documentation

Planning Department FOIAs:
- Zoning by-right educational use confirmation
- Conditional use permit requirements and history
- Future zoning change proposals and timeline
- Variance applications and approval likelihood
```

#### Property Matching Intelligence
- **Fuzzy Address Matching:** Handle variations in government record formatting
- **Coordinate-Based Verification:** Cross-reference property locations using lat/lng data
- **Multi-Source Reconciliation:** Combine data from multiple government departments per property

### 3.3 Address-Based Property Intelligence

#### Instant Property Lookup
- **Address Search Interface:** Quick property lookup by street address
- **Zoning Information Display:** Immediate zoning classification and by-right educational use status
- **Compliance Summary:** Fire sprinkler requirements, occupancy type, and square footage data
- **Data Source Attribution:** Clear indication of information sources and data freshness

#### Quick Intelligence Features

```
Address Search Results Display:
- Current zoning classification and educational use permissions
- Fire sprinkler system requirements for educational occupancy
- Building square footage and ADA accessibility status
- Historical occupancy types and recent permits
- Property owner contact information (when available)
- Tier classification based on microschool suitability criteria
```

### 3.4 Specialized Mapping and Visualization

#### Compliance-Focused Map Interface
- **Qualification Heat Mapping:** Color coding based on Primer compatibility scoring
- **Regulatory Overlay System:** Visual indicators for zoning restrictions, fire code requirements
- **Market Intelligence Layers:** Demographic data, competitor locations, transportation access

#### Property Marker System

```
Color Coding by Qualification Tier:
🟢 Green: Tier 1 - Existing Educational Occupancy, Zoned by Right, over 6,000 Sq Ft
🟡 Yellow: Tier 2 - Zoned by Right, Not Educational Occupancy, Has Fire Sprinkler
🔵 Blue: Tier 3 - Zoned by Right, Not Educational Occupancy, Unknown Fire Sprinklers
🔴 Red: Disqualified (not zoned by right or other disqualifying factors)
⚫ Gray: Insufficient Data (zoning or compliance data missing)
```

#### Progressive Zoom Intelligence
- **Regional View (Zoom 1-7):** City-level qualification rates and market opportunities
- **District View (Zoom 8-11):** Neighborhood-level clustering with demographic overlays
- **Property View (Zoom 12+):** Individual property compliance scoring and tier classification

### 3.5 Advanced Pipeline and Workflow Management

#### Property Status Tracking
- **Tier-Based Organization:** Properties automatically classified into Tier 1, 2, or 3 based on qualification criteria
- **Status Update Workflows:** Team members can update investigation status and add notes
- **Bulk Operations:** Update multiple properties simultaneously for efficient workflow management

#### Data Export and Integration
- **Filtered Exports:** Export property lists based on tier classification and custom filters
- **CRM Integration:** Push qualified properties to external customer relationship management systems
- **Report Generation:** Automated market analysis and pipeline performance reports

---

## 4. Technical Architecture

### 4.1 Configurable Business Logic Foundation

#### Qualification Engine Architecture
- Generic qualification framework with user-configurable business rules
- Support for multi-tiered property classification based on compliance criteria
- Flexible rule engine allowing modification without code changes
- Business logic templates specific to microschool requirements

#### Flexible Data Schema
- Core property foundation with extensible attribute system
- User-configurable business attributes stored in flexible format
- Support for multiple data sources with confidence scoring
- Temporal data tracking for compliance monitoring

### 4.2 Regrid Base Layer Data Ingestion

#### Overview
The Regrid parcel data serves as the foundational property dataset for the platform. This data arrives as county-separated CSV files that require normalization, cleaning, and selective import into the platform database.

#### Data Processing Requirements
- **Source Format:** Individual CSV files for each Texas county (~254 files)
- **Schema Variability:** Different column structures across county files
- **Schema Reference:** RegridSchema.xlsx defines the canonical mapping structure
- **Selective Import:** Only required columns will be imported to optimize storage
- **File Management:** CSV files uploaded to project directory for bulk processing

#### Normalization Process
- **Column Mapping:** Map varying county-specific column names to standardized schema
- **Data Cleaning:** Apply consistent formatting and validation rules
- **Quality Scoring:** Assign confidence scores based on data completeness
- **Error Handling:** Log and report issues for manual review

#### Import Workflow Stages
1. **File Validation:** Verify CSV format and basic structure
2. **Schema Detection:** Identify column patterns in each county file
3. **Mapping Application:** Apply RegridSchema.xlsx mappings to normalize data
4. **Data Cleaning:** Standardize addresses, validate coordinates, enforce data types
5. **Quality Assessment:** Calculate completeness and accuracy scores
6. **Batch Import:** Process files in optimized batches for performance
7. **Verification:** Post-import validation and reconciliation

#### Performance Considerations
- Process 15M+ records across all Texas counties
- Handle files ranging from 10K to 1M+ records per county
- Maintain sub-30 minute total import time
- Support incremental updates for data refreshes

### 4.3 High-Performance Data Processing

#### DuckDB Integration for Massive Datasets
- **Bulk Processing:** Handle 15M+ Regrid records with sub-30-minute import times
- **FOIA Integration:** Process 30K-300K row city department datasets
- **Memory Optimization:** Efficient processing within 8GB RAM constraints
- **Incremental Updates:** Handle ongoing data refreshes without full rebuilds

#### Import Pipeline Architecture
- Multi-source data integration orchestration
- Standardized Regrid format processing
- Variable FOIA format handling with column mapping
- Property data reconciliation across sources

### 4.4 API Architecture

#### Business-Context Aware Endpoints
- Generic property operations (foundation)
- Microschool-specific intelligence endpoints
- FOIA data management and column mapping
- Address-based property intelligence lookup
- Pipeline and workflow management APIs

### 4.5 Frontend Architecture

#### Component-Based Design with Business Context
- Generic, reusable property components
- Microschool-specific UI compositions
- Configuration-driven filter and display behavior
- Responsive map and list interfaces

---

## 5. Performance and Scale Requirements

### 5.1 Data Processing Performance

#### Import Performance Targets
- **Regrid Bulk Import:** 15M records processed in <30 minutes
- **FOIA Processing:** 300K records processed in <5 minutes
- **Real-time Updates:** Property status changes reflected in <2 seconds
- **Column Mapping:** Interactive preview for 100K+ row datasets in <10 seconds

#### Memory and Resource Optimization
- **Memory Efficiency:** Process largest county datasets within 8GB RAM
- **Batch Processing:** Optimal 1,000-row batches for sustained throughput
- **Error Recovery:** Resume capability for failed imports with minimal data loss

### 5.2 User Experience Performance

#### Map Rendering Performance
- **Initial Load:** <3 seconds for application startup
- **City View Rendering:** <2 seconds for any Texas city visualization
- **Property Detail Loading:** <500ms for comprehensive property information
- **Filter Application:** <1 second for complex multi-criteria filtering

#### Search and Discovery Performance
- **City Autocomplete:** <200ms response with property count previews
- **Qualification Scoring:** <100ms for individual property compliance analysis
- **Pipeline Updates:** Real-time status changes without page refresh

### 5.3 Database Performance

#### Query Performance Targets
- Property search: <50ms for basic filters
- Geospatial queries: <200ms for map viewport queries
- Compliance analysis: <100ms for individual property scoring
- Pipeline aggregation: <500ms for qualification pipeline statistics
- Support for 50+ concurrent users
- Cache hit ratio >90% for frequently accessed data

---

## 6. Data Requirements and Quality Standards

### 6.1 Data Sources and Coverage

#### Primary Data Sources

```
Regrid Parcel Data:
- Coverage: All Texas counties (15M+ properties initially)
- Future: Alabama and Florida (additional 15M+ properties)
- Update Frequency: Quarterly refreshes
- Data Quality: County-specific formats requiring normalization

Government FOIA Sources:
- Fire Departments: Sprinkler requirements, occupancy classifications
- Building Departments: Square footage, ADA compliance, structural data
- Planning Departments: Zoning verification, conditional use permits
- Update Frequency: Monthly to quarterly depending on jurisdiction
```

### 6.2 Data Quality Standards

#### Accuracy and Completeness Requirements
- **Property Identification:** 99%+ accuracy in address and coordinate data
- **Compliance Data:** 95%+ accuracy in fire/zoning compliance determination
- **Contact Intelligence:** 85%+ accuracy in property owner contact information
- **Data Freshness:** <180 days for critical compliance data

#### Validation and Verification Processes
- **Cross-Source Verification:** Validate compliance data across multiple government sources
- **Automated Quality Scoring:** 0-100 confidence scores for all property attributes
- **Manual Review Triggers:** Flag properties with conflicting or uncertain compliance data

### 6.3 Security and Privacy

#### Data Protection Standards
- **Access Control:** Role-based permissions for sensitive property and owner data
- **Audit Logging:** Complete audit trail of data access and modifications
- **Data Retention:** Compliance with government records retention requirements
- **Privacy Protection:** Anonymization of personal information where appropriate

---

## 7. Success Criteria and Metrics

### 7.1 Business Success Metrics

#### Property Sourcing Efficiency
- **Primary Goal:** 20 signed leases by December 2025
- **Qualification Pipeline:** Maintain 100+ qualified properties across Texas markets
- **Success Rate:** 20% conversion from qualified property to signed lease

#### Market Intelligence Impact
- **Market Coverage:** Comprehensive analysis for top 50 Texas expansion markets
- **Regulatory Intelligence:** Zero surprises from fire code or zoning changes
- **Off-Market Success:** 30%+ of lease negotiations from off-market property sourcing
- **Competitive Advantage:** Access to property intelligence unavailable to competitors

### 7.2 Technical Performance Metrics

#### Platform Performance
- **Import Performance:** 300K+ records processed per minute
- **Map Rendering:** <2 seconds for any city view
- **Search Response:** <500ms for autocomplete and filtering
- **System Uptime:** 99.5% availability during business hours

#### Data Quality Metrics
- **Accuracy Rate:** 95%+ validated compliance information
- **Completeness:** <5% missing critical compliance fields
- **Data Freshness:** 90%+ of compliance data <90 days old
- **Confidence Scoring:** Clear confidence indicators for all critical decisions

### 7.3 User Experience Success Criteria

#### Platform Adoption and Efficiency
- **Learning Curve:** New users productive within 30 minutes
- **Task Completion:** 95%+ success rate for property qualification workflows
- **Error Prevention:** <1% user errors in compliance assessment
- **Feature Utilization:** 90%+ usage of core qualification features

#### Decision Support Effectiveness
- **Confidence in Decisions:** Users express high confidence in platform-provided compliance analysis
- **Workflow Integration:** Platform becomes primary tool for property sourcing decisions
- **Time Savings:** Measurable reduction in property research and qualification time

---

## 8. Risk Assessment and Mitigation Strategies

### 8.1 Business Risks

#### Compliance Accuracy Risks
- **Risk:** False positive in property qualification leading to wasted lease negotiations
- **Impact:** HIGH - Could result in months of wasted effort and damaged relationships
- **Mitigation:** Multi-source verification, confidence scoring, manual review triggers

#### Regulatory Change Risks
- **Risk:** Fire code or zoning changes affecting qualified property pipeline
- **Impact:** MEDIUM - Could disqualify properties mid-negotiation
- **Mitigation:** Automated regulatory monitoring, impact analysis, proactive stakeholder communication

### 8.2 Technical Risks

#### Data Quality and Integration Risks
- **Risk:** FOIA data quality varies significantly across jurisdictions
- **Impact:** MEDIUM - Could affect qualification accuracy and confidence
- **Mitigation:** Robust validation frameworks, quality scoring, manual review processes

#### Scale and Performance Risks
- **Risk:** Platform performance degrades with expansion to Alabama and Florida
- **Impact:** MEDIUM - Could affect user experience and adoption
- **Mitigation:** Horizontal scaling architecture, performance monitoring, optimization strategies

### 8.3 Market and Competitive Risks

#### Data Access Risks
- **Risk:** Government entities restrict FOIA data access or format changes
- **Impact:** HIGH - Could eliminate competitive advantage
- **Mitigation:** Diversified data sources, government relationship building, alternative data strategies

---

This PRD establishes Primer Seek as a specialized microschool property intelligence platform that transforms the challenge of finding compliant educational properties from a manual, time-intensive process into a systematic, data-driven competitive advantage.
