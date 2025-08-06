import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React, { StrictMode } from 'react';

import { AddressMatchingValidator } from '../AddressMatchingValidator';

// Test data
const mockData = [
  { address: '7445 E LANCASTER AVE', other_field: 'test1' },
  { address: '2100 SE LOOP 820', other_field: 'test2' },
  { address: 'Invalid', other_field: 'test3' },
  { address: '512 W 4TH ST', other_field: 'test4' },
];

describe('AddressMatchingValidator - React 18.3 Strict Mode Compatibility', () => {
  let consoleSpy: jest.SpyInstance;
  
  beforeEach(() => {
    // Spy on console to catch any warnings/errors
    consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  it('should handle Strict Mode double execution without side effects', async () => {
    const onValidationComplete = jest.fn();
    
    const { unmount } = render(
      <StrictMode>
        <AddressMatchingValidator
          data={mockData}
          addressColumn="address"
          onValidationComplete={onValidationComplete}
        />
      </StrictMode>
    );

    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText(/Address Matching Results/)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Verify no console errors from Strict Mode double execution
    expect(consoleSpy).not.toHaveBeenCalled();
    
    // Verify callback was called only once despite Strict Mode
    expect(onValidationComplete).toHaveBeenCalledTimes(1);
    
    // Verify results are correct
    const summary = onValidationComplete.mock.calls[0][0];
    expect(summary.totalAddresses).toBe(4);
    expect(summary.exactMatches).toBeGreaterThan(0);

    unmount();
  });

  it('should clean up properly when unmounted during validation', async () => {
    const onValidationComplete = jest.fn();
    
    const { unmount } = render(
      <StrictMode>
        <AddressMatchingValidator
          data={mockData}
          addressColumn="address"
          onValidationComplete={onValidationComplete}
        />
      </StrictMode>
    );

    // Unmount immediately to test cleanup during validation
    unmount();

    // Wait a bit to ensure any pending operations are handled
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 200));
    });

    // Verify no console errors from cleanup
    expect(consoleSpy).not.toHaveBeenCalled();
  });

  it('should handle export functionality without memory leaks', async () => {
    const mockCreateObjectURL = jest.fn(() => 'mock-url');
    const mockRevokeObjectURL = jest.fn();
    
    // Mock URL methods
    Object.defineProperty(URL, 'createObjectURL', {
      writable: true,
      value: mockCreateObjectURL
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      writable: true,
      value: mockRevokeObjectURL
    });

    const { unmount } = render(
      <StrictMode>
        <AddressMatchingValidator
          data={mockData}
          addressColumn="address"
        />
      </StrictMode>
    );

    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText(/Export Results/)).toBeInTheDocument();
    }, { timeout: 5000 });

    // Test export functionality
    const exportButton = screen.getByText(/Export Results/);
    await userEvent.click(exportButton);

    // Wait for cleanup
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 150));
    });

    // Verify URL was created and revoked (cleanup happened)
    expect(mockCreateObjectURL).toHaveBeenCalled();
    expect(mockRevokeObjectURL).toHaveBeenCalled();

    unmount();

    // Verify no console errors
    expect(consoleSpy).not.toHaveBeenCalled();
  });

  it('should handle rapid component remounting without race conditions', async () => {
    const onValidationComplete = jest.fn();
    
    // Mount and unmount rapidly to test race conditions
    for (let i = 0; i < 3; i++) {
      const { unmount } = render(
        <StrictMode>
          <AddressMatchingValidator
            data={mockData}
            addressColumn="address"
            onValidationComplete={onValidationComplete}
          />
        </StrictMode>
      );

      // Unmount quickly
      setTimeout(unmount, 50);
    }

    // Wait for all operations to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));
    });

    // Verify no console errors from race conditions
    expect(consoleSpy).not.toHaveBeenCalled();
  });

  it('should prevent state updates after unmount', async () => {
    const onValidationComplete = jest.fn();
    
    const { unmount } = render(
      <StrictMode>
        <AddressMatchingValidator
          data={mockData}
          addressColumn="address"
          onValidationComplete={onValidationComplete}
        />
      </StrictMode>
    );

    // Unmount immediately
    unmount();

    // Wait for potential delayed operations
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 500));
    });

    // Should not have completed validation after unmount
    expect(onValidationComplete).not.toHaveBeenCalled();
    
    // Verify no console errors about state updates after unmount
    expect(consoleSpy).not.toHaveBeenCalled();
  });

  it('should handle AbortController properly in different browsers', async () => {
    // Test that our AbortController usage works correctly
    const originalAbortController = global.AbortController;
    
    // Mock AbortController to ensure our code handles it properly
    const mockAbort = jest.fn();
    global.AbortController = jest.fn(() => ({
      signal: { aborted: false },
      abort: mockAbort
    })) as any;

    const { unmount } = render(
      <StrictMode>
        <AddressMatchingValidator
          data={mockData}
          addressColumn="address"
        />
      </StrictMode>
    );

    unmount();

    // Verify abort was called during cleanup
    expect(mockAbort).toHaveBeenCalled();
    
    // Restore original
    global.AbortController = originalAbortController;
  });
});