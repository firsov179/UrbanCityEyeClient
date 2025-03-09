// Helper functions for interacting with PyScript

// Function to call a Python function from JavaScript
function callPython(functionPath, ...args) {
  return window.pyodide.runPython(`
    import json
    from ${functionPath} as target_function
    target_function(${args.map(arg => JSON.stringify(arg)).join(', ')})
  `);
}

// Register global event handlers
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM fully loaded, waiting for PyScript to initialize...');
});

// Make the map instance globally accessible
window.mapInstance = null;

