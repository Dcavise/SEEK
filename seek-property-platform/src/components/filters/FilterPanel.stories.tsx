import type { Meta, StoryObj } from '@storybook/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FilterPanel } from './FilterPanel';

// Create a wrapper component to provide React Query context
const FilterPanelWrapper = (props: Parameters<typeof FilterPanel>[0]) => {
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
      <div className="w-80 p-4 bg-gray-50">
        <FilterPanel {...props} />
      </div>
    </QueryClientProvider>
  );
};

const meta = {
  title: 'SEEK/Filters/FilterPanel',
  component: FilterPanelWrapper,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'The main filter panel for SEEK property search with FOIA integration support.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    onFiltersChange: {
      action: 'filters changed',
      description: 'Called when filters are modified',
    },
  },
} satisfies Meta<typeof FilterPanelWrapper>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    onFiltersChange: (filters) => {
      console.log('Filters changed:', filters);
    },
  },
};

export const WithExistingFilters: Story = {
  args: {
    onFiltersChange: (filters) => {
      console.log('Filters changed:', filters);
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows the filter panel with some pre-applied filters for testing.',
      },
    },
  },
};

export const CompactView: Story = {
  args: {
    onFiltersChange: (filters) => {
      console.log('Filters changed:', filters);
    },
  },
  decorators: [
    (Story) => (
      <div className="w-60">
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story: 'Filter panel in a more compact layout for smaller screens.',
      },
    },
  },
};