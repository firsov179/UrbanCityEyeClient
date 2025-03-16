// Function to call a Python function from JavaScript
function callPython(functionPath, ...args) {
  return window.pyodide.runPython(`
    import json
    from ${functionPath} as target_function
    target_function(${args.map(arg => JSON.stringify(arg)).join(', ')})
  `);
}

function navigateToHome() {
  callPython("pyscript.actions.city_actions.CityActions.navigate_to_home");
}

// Make the map instance globally accessible
window.mapInstance = null;

// Handle screen changes
document.addEventListener('DOMContentLoaded', () => {
  // Add click handlers for navigation buttons if they exist
  const backButton = document.getElementById('back-to-home');
  if (backButton) {
    backButton.addEventListener('click', () => navigateToHome());
  }
});
