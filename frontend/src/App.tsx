import React from 'react';

import { cn } from '@/utils';

interface AppProps {
  title?: string;
}

const App: React.FC<AppProps> = ({ title = 'Primer Seek Property' }) => {
  const handleClick = () => {
    // Handle app click - placeholder for future functionality
    // eslint-disable-next-line no-console
    console.log('Getting started with Primer Seek Property sourcing system');
  };

  return (
    <div className='min-h-screen bg-gray-50'>
      <header className='bg-white shadow-sm border-b border-gray-200'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
          <div className='flex justify-between items-center py-6'>
            <h1 className='text-3xl font-bold text-gray-900 text-balance'>{title}</h1>
            <button
              type='button'
              onClick={handleClick}
              className={cn(
                'btn-primary',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2'
              )}
            >
              Get Started
            </button>
          </div>
        </div>
      </header>

      <main className='max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8'>
        <div className='card'>
          <h2 className='text-xl font-semibold text-gray-900 mb-4'>
            Welcome to Primer Seek Property
          </h2>
          <p className='text-gray-600 leading-relaxed'>
            Your comprehensive property sourcing system for Texas, Alabama, and Florida.
            Discover investment opportunities with our advanced mapping and data
            visualization tools.
          </p>
          <div className='mt-6 flex gap-4'>
            <button className='btn-secondary'>View Properties</button>
            <button className='btn-primary'>Start Searching</button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
