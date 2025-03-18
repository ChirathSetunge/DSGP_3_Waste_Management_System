const routes = [
  '01 - VILAWALA', '29B - BORUPANA', '29A - KANDAWALA', '28 - RATMALANA EAST', '27 - RATMALANA WEST',
  '26 - VIHARA', '25 - ATTIDIYA SOUTH', '24 - PIRIVENA', '23 - WEDIKANDA', '21 - ATTIDIYA NORTH',
  '20 - KATUKURUNDUWATTA', '19 - WATARAPPOLA', '18 - VIDYALAYA', '17 - GALKISSA', '16 - KAWDANA WEST',
  '15B - KAWDANA EAST', '22 - WATHUMULLA', '14 - KARAGAMPITIYA', '15A - KAWDANA EAST', '02 - DUTUGAMUNU',
  '02/03 - EKABADDA', '03 - KOHUWALA', '04 - KALUBOWILA', '06 - SARANANKARA', '07 - GALWALA',
  '05 - HATHBODIYA', '09 - DEHIWALA EAST', '10 - UDYANAYA', '11 - NEDIMALA', '12 - MALWATTA',
  '13 - JAYATHILAKA', '08 - DEHIWALA WEST', '05/06 - EKABADDA'
];

let selectedRoutes = [];
const routeButtonsDiv = document.getElementById('routeButtons');
const buttonMap = {};
let predictionsDict = {};


function addDays(dateStr, days) {
  const date = new Date(dateStr);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

function updateDateRangeForRoute(route) {
  fetch(`/household/get-last-date?route=${encodeURIComponent(route)}`)
    .then(response => response.json())
    .then(data => {
      const dumpDateInput = document.getElementById('dumpDate');
      if (data.last_date) {
        // Set min: last_date + 1 day, max: last_date + 5 days.
        const minDate = addDays(data.last_date, 1);
        const maxDate = addDays(data.last_date, 5);
        dumpDateInput.min = minDate;
        dumpDateInput.max = maxDate;
        document.getElementById('dateHelp').innerText = `Select a date between ${minDate} and ${maxDate}.`;
      } else {
        document.getElementById('dateHelp').innerText = `No previous data found for ${route}.`;
      }
      // Enable the date input
      dumpDateInput.disabled = false;
    })
    .catch(error => console.error('Error fetching last date:', error));
}

// Generate route buttons dynamically
routes.forEach(route => {
  const btn = document.createElement('button');
  btn.className = 'btn btn-outline-primary m-1 floating-button';
  btn.innerText = route;

  btn.onclick = () => {
    if (!selectedRoutes.includes(route)) {
      selectedRoutes.push(route);  // Add route to stack
      btn.classList.add('btn-success', 'text-white');  // Mark button as active (green)
      // Update date input range based on the selected route
      updateDateRangeForRoute(route);
    } else {
      alert('This route is already selected.');
    }
  };

  buttonMap[route] = btn;
  routeButtonsDiv.appendChild(btn);
});

// Predict button event handler
document.getElementById('predictBtn').addEventListener('click', () => {
  const dumpDate = document.getElementById('dumpDate').value;
  const mswCollected = document.getElementById('mswCollected').value;

  if (selectedRoutes.length === 0) {
    alert('Please select a route first.');
    return;
  }
  if (!dumpDate) {
    alert('Please select a date.');
    return;
  }
  // Use the last selected route for prediction
  const latestRoute = selectedRoutes[selectedRoutes.length - 1];

  fetch('/household/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      route: latestRoute,
      dump_date: dumpDate,
      msw_collected: mswCollected
    })
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById('predictionResult').innerText = `Predicted MSW: ${data.prediction} Kg`;
    // Clear the selectedRoutes
    predictionsDict[latestRoute] = data.prediction;
    selectedRoutes = [];
  })
  .catch(error => {
    console.error('Error:', error);
    document.getElementById('predictionResult').innerText = 'Error fetching prediction.';
  });
});

document.getElementById('visualizeBtn').addEventListener('click', () => {
  sessionStorage.setItem('predictions', JSON.stringify(predictionsDict));
  window.location.href = '/household/visualize';
});

window.addEventListener('beforeunload', () => {
  selectedRoutes = [];
  Object.values(buttonMap).forEach(btn => {
    btn.classList.remove('btn-success', 'text-white');
  });
});