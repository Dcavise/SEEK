import { Property } from '@/types/property';

export const mockProperties: Property[] = [
  // BOSTON PROPERTIES
  {
    id: 'prop_1',
    address: '123 Main St',
    city: 'Boston',
    state: 'MA',
    zip: '02101',
    latitude: 42.3601,
    longitude: -71.0589,
    parcel_number: 'BOS-001-2023',
    square_feet: 25000,
    zoning_code: 'C-2',
    zoning_by_right: true,
    current_occupancy: 'business',
    fire_sprinkler_status: 'yes',
    assigned_to: 'jarnail',
    status: 'synced',
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    notes: 'Initial property assessment completed. Building meets size requirements.\n\n[COMPLIANCE] Fire sprinkler system needs verification during site visit.',
    sync_status: 'synced',
    last_synced_at: '2024-01-15T11:45:00Z',
    external_system_id: 'SF-PROP-001-2024',
    sync_error: null,
    county: 'Suffolk County',
    listed_owner: 'Boston Commercial Properties LLC',
    folio_int: 'INT-BOS-001-2023',
    municipal_zoning_url: 'https://boston.gov/zoning/c2-commercial',
    city_portal_url: 'https://boston.gov/property/123-main-st',
    parcel_sq_ft: 35000
  },
  {
    id: 'prop_2',
    address: '456 Oak Ave',
    city: 'Cambridge',
    state: 'MA',
    zip: '02139',
    latitude: 42.3736,
    longitude: -71.1097,
    parcel_number: 'CAM-002-2023',
    square_feet: 18000,
    zoning_code: 'I-1',
    zoning_by_right: true,
    current_occupancy: 'industrial',
    fire_sprinkler_status: 'unknown',
    assigned_to: 'david-h',
    status: 'reviewing',
    created_at: '2024-01-10T10:30:00Z',
    updated_at: '2024-01-10T10:30:00Z',
    notes: null,
    sync_status: null,
    last_synced_at: null,
    external_system_id: null,
    sync_error: null,
    county: 'Middlesex County',
    listed_owner: 'Cambridge Industrial Holdings',
    folio_int: 'INT-CAM-002-2023',
    municipal_zoning_url: 'https://cambridge.gov/zoning/i1-industrial',
    city_portal_url: 'https://cambridge.gov/property/456-oak-ave',
    parcel_sq_ft: 28000
  },
  {
    id: 'prop_3',
    address: '789 Pine St',
    city: 'Somerville', 
    state: 'MA',
    zip: '02143',
    latitude: 42.3875,
    longitude: -71.0995,
    parcel_number: 'SOM-003-2023',
    square_feet: 4500, // Below minimum
    zoning_code: 'R-3',
    zoning_by_right: false,
    current_occupancy: 'residential',
    fire_sprinkler_status: 'no',
    assigned_to: 'aly',
    status: 'not_qualified',
    created_at: '2024-01-08T10:30:00Z',
    updated_at: '2024-01-08T10:30:00Z',
    notes: null,
    sync_status: null,
    last_synced_at: null,
    external_system_id: null,
    sync_error: null,
    county: 'Middlesex County',
    listed_owner: 'Somerville Residential Trust',
    folio_int: 'INT-SOM-003-2023',
    municipal_zoning_url: 'https://somerville.gov/zoning/r3-residential',
    city_portal_url: 'https://somerville.gov/property/789-pine-st',
    parcel_sq_ft: 8000
  },
  {
    id: 'prop_4',
    address: '321 Elm St',
    city: 'Brighton',
    state: 'MA', 
    zip: '02135',
    latitude: 42.3483,
    longitude: -71.1469,
    parcel_number: 'BRI-004-2023',
    square_feet: 30000,
    zoning_code: 'C-1',
    zoning_by_right: true,
    current_occupancy: 'assembly',
    fire_sprinkler_status: 'yes',
    assigned_to: null,
    status: 'synced',
    created_at: '2024-01-12T10:30:00Z',
    updated_at: '2024-01-12T10:30:00Z',
    notes: null,
    sync_status: 'synced',
    last_synced_at: '2024-01-12T14:20:00Z',
    external_system_id: 'SF-PROP-004-2024',
    sync_error: null,
    county: 'Suffolk County',
    listed_owner: 'Brighton Community Center',
    folio_int: 'INT-BRI-004-2023',
    municipal_zoning_url: 'https://brighton.gov/zoning/c1-commercial',
    city_portal_url: 'https://brighton.gov/property/321-elm-st',
    parcel_sq_ft: 42000
  },
  {
    id: 'prop_5',
    address: '654 Maple Dr',
    city: 'Brookline',
    state: 'MA',
    zip: '02446',
    latitude: 42.3317,
    longitude: -71.1211,
    parcel_number: 'BRO-005-2023',
    square_feet: 12000,
    zoning_code: 'M-1',
    zoning_by_right: null,
    current_occupancy: 'assembly',
    fire_sprinkler_status: 'yes',
    assigned_to: null,
    status: 'new',
    created_at: '2024-01-05T10:30:00Z',
    updated_at: '2024-01-05T10:30:00Z',
    notes: null,
    sync_status: null,
    last_synced_at: null,
    external_system_id: null,
    sync_error: null,
    county: 'Norfolk County',
    listed_owner: 'Brookline Mixed Use Partners',
    folio_int: 'INT-BRO-005-2023',
    municipal_zoning_url: 'https://brookline.gov/zoning/m1-mixed',
    city_portal_url: 'https://brookline.gov/property/654-maple-dr',
    parcel_sq_ft: 18000
  }
];

// Helper function to generate additional properties for overload testing
export const generateMockProperties = (count: number, baseCoordinates: [number, number] = [-71.0589, 42.3601]): Property[] => {
  const statuses: Property['status'][] = ['synced', 'reviewing', 'new', 'not_qualified'];
  const occupancyTypes = ['business', 'assembly', 'industrial', 'unknown'];
  const sprinklerStatuses = ['yes', 'no', 'unknown'];
  const zoningByRight = [true, false, null];
  const analysts = ['jarnail', 'david-h', 'cavise', 'jb', 'stephen', 'aly', 'ryan-d', null];
  const counties = ['Suffolk County', 'Middlesex County', 'Norfolk County', 'Essex County'];
  
  const streetNames = [
    'Main St', 'Oak Ave', 'Pine St', 'Elm St', 'Maple Dr', 'Cedar Ln', 'Birch Ave', 
    'Walnut St', 'Spruce Rd', 'Chestnut Blvd', 'Poplar Ct', 'Willow Way', 'Hickory Ln',
    'Aspen St', 'Sycamore Ave', 'Dogwood Dr', 'Magnolia Rd', 'Redwood Pl', 'Fir Tree Ln',
    'Palm St', 'Washington Ave', 'Lincoln Blvd', 'Jefferson Dr', 'Madison St', 'Monroe Ln'
  ];
  
  const cities = [
    'Boston', 'Cambridge', 'Somerville', 'Brighton', 'Brookline', 'Newton', 'Quincy',
    'Medford', 'Waltham', 'Arlington', 'Malden', 'Revere', 'Chelsea', 'Everett',
    'Watertown', 'Belmont', 'Lexington', 'Burlington', 'Woburn', 'Winchester'
  ];

  return Array.from({ length: count }, (_, i) => {
    const id = `prop_${mockProperties.length + i + 1}`;
    const streetNum = Math.floor(Math.random() * 9999) + 1;
    const streetName = streetNames[Math.floor(Math.random() * streetNames.length)];
    const city = cities[Math.floor(Math.random() * cities.length)];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    
    // Add some randomness to coordinates
    const latOffset = (Math.random() - 0.5) * 0.1;
    const lngOffset = (Math.random() - 0.5) * 0.1;
    
    return {
      id,
      address: `${streetNum} ${streetName}`,
      city,
      state: 'MA',
      zip: `0${Math.floor(Math.random() * 9) + 1}${Math.floor(Math.random() * 999).toString().padStart(3, '0')}`,
      latitude: baseCoordinates[1] + latOffset,
      longitude: baseCoordinates[0] + lngOffset,
      parcel_number: `${city.substring(0, 3).toUpperCase()}-${id.padStart(3, '0')}-2023`,
      square_feet: Math.floor(Math.random() * 50000) + 5000,
      zoning_code: `${['B', 'C', 'I', 'M', 'R'][Math.floor(Math.random() * 5)]}-${Math.floor(Math.random() * 5) + 1}`,
      zoning_by_right: zoningByRight[Math.floor(Math.random() * zoningByRight.length)],
      current_occupancy: occupancyTypes[Math.floor(Math.random() * occupancyTypes.length)],
      fire_sprinkler_status: sprinklerStatuses[Math.floor(Math.random() * sprinklerStatuses.length)],
      assigned_to: analysts[Math.floor(Math.random() * analysts.length)],
      status,
      created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      notes: Math.random() > 0.7 ? `[GENERAL] Property assessment note for ${streetNum} ${streetName}` : null,
      sync_status: status === 'synced' ? 'synced' : Math.random() > 0.7 ? 'pending' : Math.random() > 0.9 ? 'failed' : null,
      last_synced_at: status === 'synced' ? new Date(Date.now() - Math.random() * 3 * 24 * 60 * 60 * 1000).toISOString() : null,
      external_system_id: status === 'synced' ? `SF-PROP-${id.padStart(3, '0')}-2024` : null,
      sync_error: Math.random() > 0.95 ? 'Connection timeout - retry scheduled' : null,
      county: counties[Math.floor(Math.random() * counties.length)],
      listed_owner: `${city} Properties LLC`,
      folio_int: `INT-${city.substring(0, 3).toUpperCase()}-${id.padStart(3, '0')}-2023`,
      municipal_zoning_url: `https://${city.toLowerCase()}.gov/zoning/${['b', 'c', 'i', 'm', 'r'][Math.floor(Math.random() * 5)]}-${Math.floor(Math.random() * 5) + 1}`,
      city_portal_url: `https://${city.toLowerCase()}.gov/property/${streetNum}-${streetName.replace(' ', '-').toLowerCase()}`,
      parcel_sq_ft: Math.floor(Math.random() * 100000) + 10000
    };
  });
};