import type { Meta, StoryObj } from '@storybook/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SearchOverlay } from './SearchOverlay';

// Wrapper component with React Query context for city search functionality
const SearchOverlayWrapper = (props: Parameters<typeof SearchOverlay>[0]) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <div className="relative h-96 bg-gray-900 flex items-center justify-center">
        <SearchOverlay {...props} />
      </div>
    </QueryClientProvider>
  );
};

const meta = {
  title: 'SEEK/Search/SearchOverlay',
  component: SearchOverlayWrapper,
  parameters: {
    layout: 'fullscreen',
    backgrounds: {
      default: 'dark',
      values: [
        { name: 'dark', value: '#1a1a1a' },
        { name: 'light', value: '#ffffff' },
      ],
    },
    docs: {
      description: {
        component: `
The main search overlay for SEEK property platform with database-powered city search.

**Features:**
- Real-time city search with autocomplete from 1.4M+ parcel database
- Database-powered suggestions (no hardcoded cities)
- Support for Fort Worth, Austin, Dallas, and all Texas cities
- Responsive design for mobile and desktop
- Loading states and error handling
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    onCitySearchClick: {
      action: 'city search clicked',
      description: 'Called when city search overlay is closed',
    },
    onAddressSearchClick: {
      action: 'address search clicked', 
      description: 'Called when address search is initiated',
    },
    onCitySelected: {
      action: 'city selected',
      description: 'Called when a city is selected from autocomplete dropdown',
    },
  },
} satisfies Meta<typeof SearchOverlayWrapper>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    onCitySearchClick: () => console.log('🏙️ City search overlay closed'),
    onAddressSearchClick: () => console.log('🏠 Address search initiated'),
    onCitySelected: (city: string) => console.log('✅ City selected:', city),
  },
  parameters: {
    docs: {
      description: {
        story: 'The default search overlay with two main options: Search by City and Search by Address.',
      },
    },
  },
};

export const CitySearchActive: Story = {
  args: {
    onCitySearchClick: () => console.log('🏙️ City search overlay closed'),
    onAddressSearchClick: () => console.log('🏠 Address search initiated'),
    onCitySelected: (city: string) => console.log('✅ City selected:', city),
  },
  parameters: {
    docs: {
      description: {
        story: `
City search mode with live database autocomplete. Try typing:
- "fort worth" - Should find Fort Worth, TX
- "austin" - Should find Austin, TX  
- "dallas" - Should find Dallas, TX

The search queries your actual Supabase database with 1.4M+ parcels.
        `,
      },
    },
  },
};

export const MobileView: Story = {
  args: {
    onCitySearchClick: () => console.log('🏙️ City search overlay closed'),
    onAddressSearchClick: () => console.log('🏠 Address search initiated'),
    onCitySelected: (city: string) => console.log('✅ City selected:', city),
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
    docs: {
      description: {
        story: 'Search overlay optimized for mobile devices. Notice the responsive layout adjustments.',
      },
    },
  },
};

export const TabletView: Story = {
  args: {
    onCitySearchClick: () => console.log('🏙️ City search overlay closed'),
    onAddressSearchClick: () => console.log('🏠 Address search initiated'),  
    onCitySelected: (city: string) => console.log('✅ City selected:', city),
  },
  parameters: {
    viewport: {
      defaultViewport: 'tablet',
    },
    docs: {
      description: {
        story: 'Search overlay on tablet-sized screens, maintaining usability across different screen sizes.',
      },
    },
  },
};

export const InteractionTest: Story = {
  args: {
    onCitySearchClick: () => {
      alert('🏙️ City search completed! This would normally close the overlay and start property search.');
    },
    onAddressSearchClick: () => {
      alert('🏠 Address search initiated! This would switch to address input mode.');
    },
    onCitySelected: (city: string) => {
      alert(`✅ Selected: ${city}\n\nThis would start searching properties in this city using your 1.4M+ parcel database.`);
    },
  },
  parameters: {
    docs: {
      description: {
        story: `
Interactive version with alert dialogs to demonstrate the callback functions.
Perfect for testing the component behavior and understanding the user flow.
        `,
      },
    },
  },
};