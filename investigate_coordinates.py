#!/usr/bin/env python3
"""
Script to investigate coordinate fields in the parcels table to fix Mapbox NaN error.
This script will:
1. Connect to Supabase database
2. Query the parcels table schema to identify coordinate columns
3. Sample coordinate data to analyze data quality and format
4. Provide recommendations for frontend fix
"""

import os
import json
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

def load_environment() -> Dict[str, str]:
    """Load environment variables from .env file"""
    load_dotenv()
    
    env_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_SERVICE_KEY': os.getenv('SUPABASE_SERVICE_KEY')
    }
    
    # Validate required environment variables
    missing_vars = [key for key, value in env_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return env_vars

def create_supabase_client(env_vars: Dict[str, str]) -> Client:
    """Create and return Supabase client"""
    return create_client(env_vars['SUPABASE_URL'], env_vars['SUPABASE_SERVICE_KEY'])

def get_table_schema(supabase: Client, table_name: str = 'parcels') -> List[Dict[str, Any]]:
    """Get the schema information for the specified table"""
    print(f"🔍 Investigating {table_name} table schema...")
    
    # Query to get column information
    schema_query = """
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
    FROM information_schema.columns 
    WHERE table_name = %s 
    ORDER BY ordinal_position;
    """
    
    try:
        # Execute raw SQL query
        result = supabase.rpc('exec_sql', {
            'sql': schema_query.replace('%s', f"'{table_name}'")
        }).execute()
        
        return result.data
    except Exception as e:
        print(f"❌ Error getting schema: {e}")
        # Fallback: try to get first row to understand structure
        try:
            sample = supabase.table(table_name).select("*").limit(1).execute()
            if sample.data:
                columns = list(sample.data[0].keys())
                return [{'column_name': col, 'data_type': 'unknown'} for col in columns]
        except Exception as fallback_error:
            print(f"❌ Fallback schema query also failed: {fallback_error}")
            return []

def identify_coordinate_columns(schema: List[Dict[str, Any]]) -> List[str]:
    """Identify potential coordinate columns from schema"""
    coordinate_keywords = [
        'lat', 'latitude', 'lng', 'longitude', 'lon', 'long',
        'coord', 'coordinates', 'geometry', 'geom', 'location',
        'x', 'y', 'point', 'gps'
    ]
    
    coordinate_columns = []
    
    for column in schema:
        col_name = column['column_name'].lower()
        for keyword in coordinate_keywords:
            if keyword in col_name:
                coordinate_columns.append(column['column_name'])
                break
    
    return coordinate_columns

def sample_coordinate_data(supabase: Client, coordinate_columns: List[str], 
                         sample_size: int = 100) -> Dict[str, Any]:
    """Sample coordinate data to analyze data quality"""
    print(f"📊 Sampling {sample_size} records to analyze coordinate data...")
    
    results = {}
    
    # Always sample all data first to understand the structure
    print("🔍 Sampling all data to understand table structure...")
    try:
        sample = supabase.table('parcels').select("*").limit(sample_size).execute()
        if sample.data:
            # Look for coordinate-like data in the sample
            first_record = sample.data[0]
            all_columns = list(first_record.keys())
            
            results['all_columns'] = all_columns
            results['sample_data'] = sample.data[:5]  # First 5 records for analysis
            
            # Try to identify coordinate columns from actual data
            potential_coords = []
            for col in all_columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['lat', 'lng', 'lon', 'coord', 'x', 'y', 'geom']):
                    potential_coords.append(col)
            
            results['potential_coordinate_columns'] = potential_coords
            
            # Analyze each potential coordinate column
            if potential_coords:
                for col in potential_coords:
                    col_analysis = analyze_coordinate_column(sample.data, col)
                    results[f'{col}_analysis'] = col_analysis
            else:
                # Look for any numeric columns that might be coordinates
                print("🔍 No obvious coordinate columns found. Checking for numeric columns that might be coordinates...")
                numeric_columns = []
                for col in all_columns:
                    # Check first few values to see if they're numeric
                    values = [record.get(col) for record in sample.data[:10] if record.get(col) is not None]
                    if values:
                        try:
                            # Try to convert to float
                            float_vals = [float(v) for v in values]
                            # Check if values could be coordinates (reasonable ranges)
                            if any(-180 <= v <= 180 for v in float_vals):
                                numeric_columns.append(col)
                        except (ValueError, TypeError):
                            pass
                
                results['potential_numeric_columns'] = numeric_columns
                
                for col in numeric_columns:
                    col_analysis = analyze_coordinate_column(sample.data, col)
                    results[f'{col}_analysis'] = col_analysis
            
            return results
    except Exception as e:
        print(f"❌ Error sampling general data: {e}")
        return {'error': str(e)}

def analyze_coordinate_column(data: List[Dict[str, Any]], column_name: str) -> Dict[str, Any]:
    """Analyze a specific coordinate column for data quality"""
    values = [record.get(column_name) for record in data if record.get(column_name) is not None]
    
    analysis = {
        'total_records': len(data),
        'non_null_count': len(values),
        'null_count': len(data) - len(values),
        'sample_values': values[:10],  # First 10 non-null values
    }
    
    if values:
        # Check for numeric values
        numeric_values = []
        non_numeric_values = []
        
        for val in values:
            try:
                float_val = float(val)
                numeric_values.append(float_val)
            except (ValueError, TypeError):
                non_numeric_values.append(val)
        
        analysis.update({
            'numeric_count': len(numeric_values),
            'non_numeric_count': len(non_numeric_values),
            'non_numeric_examples': non_numeric_values[:5],
        })
        
        if numeric_values:
            analysis.update({
                'min_value': min(numeric_values),
                'max_value': max(numeric_values),
                'avg_value': sum(numeric_values) / len(numeric_values),
            })
            
            # Check if values look like latitude/longitude
            if 'lat' in column_name.lower():
                valid_lat = [v for v in numeric_values if -90 <= v <= 90]
                analysis['valid_latitude_count'] = len(valid_lat)
                analysis['invalid_latitude_examples'] = [v for v in numeric_values if not (-90 <= v <= 90)][:5]
            
            elif any(keyword in column_name.lower() for keyword in ['lng', 'lon', 'long']):
                valid_lng = [v for v in numeric_values if -180 <= v <= 180]
                analysis['valid_longitude_count'] = len(valid_lng)
                analysis['invalid_longitude_examples'] = [v for v in numeric_values if not (-180 <= v <= 180)][:5]
    
    return analysis

def generate_recommendations(analysis_results: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on the analysis"""
    recommendations = []
    
    # Check what we found
    coordinate_columns = analysis_results.get('coordinate_columns', [])
    potential_coords = analysis_results.get('potential_coordinate_columns', [])
    potential_numeric = analysis_results.get('potential_numeric_columns', [])
    all_columns = analysis_results.get('all_columns', [])
    
    # Determine what columns we're working with
    working_columns = coordinate_columns or potential_coords or potential_numeric
    
    if not working_columns:
        recommendations.append("❌ CRITICAL: No coordinate columns found in the parcels table!")
        recommendations.append("   📋 Available columns in parcels table:")
        for col in all_columns[:20]:  # Show first 20 columns
            recommendations.append(f"      • {col}")
        if len(all_columns) > 20:
            recommendations.append(f"      ... and {len(all_columns) - 20} more columns")
        
        recommendations.append("\n🚨 ROOT CAUSE: Missing coordinate data")
        recommendations.append("   • The parcels table does not contain latitude/longitude coordinates")
        recommendations.append("   • This explains the Mapbox NaN error - no coordinate data to display")
        
        recommendations.append("\n🔧 SOLUTIONS:")
        recommendations.append("   1. ADD COORDINATE COLUMNS to parcels table:")
        recommendations.append("      • ALTER TABLE parcels ADD COLUMN latitude DECIMAL(10, 8);")
        recommendations.append("      • ALTER TABLE parcels ADD COLUMN longitude DECIMAL(11, 8);")
        
        recommendations.append("   2. GEOCODE EXISTING ADDRESSES:")
        recommendations.append("      • Use address field to get coordinates via geocoding API")
        recommendations.append("      • Services: Google Maps API, Mapbox Geocoding, OpenStreetMap Nominatim")
        
        recommendations.append("   3. IMMEDIATE FRONTEND FIX:")
        recommendations.append("      • Add null checks before rendering map markers")
        recommendations.append("      • Hide map or show 'No location data' message for properties without coordinates")
        recommendations.append("      • Set default center coordinates for map when no property coordinates exist")
        
        return recommendations
    
    # We found some potential coordinate columns
    if potential_coords:
        recommendations.append(f"✅ Found potential coordinate columns: {potential_coords}")
    elif potential_numeric:
        recommendations.append(f"⚠️  Found numeric columns that might be coordinates: {potential_numeric}")
    else:
        recommendations.append(f"🤔 Found columns identified as coordinates: {working_columns}")
    
    # Analyze each coordinate column
    for col in working_columns:
        col_analysis = analysis_results.get(f'{col}_analysis')
        if col_analysis:
            null_percentage = (col_analysis['null_count'] / col_analysis['total_records']) * 100
            
            if null_percentage > 50:
                recommendations.append(f"⚠️  {col}: High null rate ({null_percentage:.1f}%) - data quality issue")
            
            if col_analysis.get('non_numeric_count', 0) > 0:
                recommendations.append(f"⚠️  {col}: Contains non-numeric values - needs data cleaning")
            
            # Check for invalid coordinate ranges
            if 'invalid_latitude_examples' in col_analysis and col_analysis['invalid_latitude_examples']:
                recommendations.append(f"⚠️  {col}: Contains invalid latitude values (outside -90 to 90 range)")
            
            if 'invalid_longitude_examples' in col_analysis and col_analysis['invalid_longitude_examples']:
                recommendations.append(f"⚠️  {col}: Contains invalid longitude values (outside -180 to 180 range)")
    
    # Frontend-specific recommendations
    recommendations.append("\n🔧 Frontend Fix Recommendations:")
    
    if working_columns:
        lat_cols = [col for col in working_columns if 'lat' in col.lower()]
        lng_cols = [col for col in working_columns if any(keyword in col.lower() for keyword in ['lng', 'lon', 'long'])]
        
        if lat_cols and lng_cols:
            recommendations.append(f"   • Use {lat_cols[0]} and {lng_cols[0]} for Mapbox coordinates")
            recommendations.append(f"   • Add null checks: if ({lat_cols[0]} && {lng_cols[0]} && !isNaN({lat_cols[0]}) && !isNaN({lng_cols[0]}))")
            recommendations.append("   • Filter out records where coordinates are null or NaN before rendering")
        else:
            recommendations.append("   • Could not identify clear latitude/longitude pairs")
            recommendations.append(f"   • Available columns: {working_columns}")
            recommendations.append("   • These may not be actual coordinate columns")
    
    recommendations.append("   • Add default coordinates for Texas center if no property coordinates available")
    recommendations.append("   • Add error boundaries around map components to handle coordinate issues gracefully")
    recommendations.append("   • Consider showing property list instead of map when coordinates are missing")
    
    return recommendations

def main():
    """Main function to investigate coordinate fields"""
    print("🗺️  SEEK Property Platform - Coordinate Investigation")
    print("=" * 60)
    
    try:
        # Load environment and create client
        env_vars = load_environment()
        print("✅ Environment variables loaded")
        
        supabase = create_supabase_client(env_vars)
        print("✅ Supabase client created")
        
        # Get table schema
        schema = get_table_schema(supabase, 'parcels')
        print(f"✅ Retrieved schema with {len(schema)} columns")
        
        # Identify coordinate columns
        coordinate_columns = identify_coordinate_columns(schema)
        print(f"🎯 Identified coordinate columns: {coordinate_columns}")
        
        # Sample coordinate data
        analysis_results = sample_coordinate_data(supabase, coordinate_columns)
        
        # Generate recommendations
        recommendations = generate_recommendations(analysis_results)
        
        # Prepare final report
        report = {
            'timestamp': '2025-08-06T' + str(hash(str(analysis_results)))[-8:],  # Simple timestamp
            'schema_columns': len(schema),
            'coordinate_columns_found': coordinate_columns,
            'analysis_results': analysis_results,
            'recommendations': recommendations
        }
        
        # Save detailed results to JSON file
        output_file = '/Users/davidcavise/Documents/Windsurf Projects/SEEK/coordinate_investigation_results.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n📋 COORDINATE INVESTIGATION SUMMARY")
        print("=" * 60)
        print(f"Schema Columns: {len(schema)}")
        print(f"Coordinate Columns: {coordinate_columns or 'None found'}")
        
        if analysis_results.get('sample_data'):
            print(f"Sample Records: {len(analysis_results['sample_data'])}")
        
        print("\n🎯 RECOMMENDATIONS:")
        for rec in recommendations:
            print(rec)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Show sample schema for debugging
        if schema:
            print(f"\n📊 SAMPLE SCHEMA (first 10 columns):")
            for col in schema[:10]:
                print(f"   • {col.get('column_name', 'unknown')}: {col.get('data_type', 'unknown')}")
            if len(schema) > 10:
                print(f"   ... and {len(schema) - 10} more columns")
        
        # Show sample data for debugging  
        if analysis_results.get('sample_data'):
            print(f"\n📝 SAMPLE RECORD (first record keys):")
            first_record = analysis_results['sample_data'][0]
            keys = list(first_record.keys())
            for key in keys[:15]:  # First 15 keys
                value = first_record[key]
                print(f"   • {key}: {value} ({type(value).__name__})")
            if len(keys) > 15:
                print(f"   ... and {len(keys) - 15} more fields")
        
    except Exception as e:
        print(f"\n❌ Investigation failed: {e}")
        import traceback
        print(f"📍 Full error: {traceback.format_exc()}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)