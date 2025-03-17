// list of routes.
const routes = [
  '01 - VILAWALA', '29B - BORUPANA', '29A - KANDAWALA', '28 - RATMALANA EAST', '27 - ATTIDIYA NORTH',
  '26 - VIHARA', '25 - ATTIDIYA SOUTH', '24 - PIRIVENA', '23 - WEDIKANDA', '21 - ATTIDIYA NORTH',
  '20 - KATUKURUNDUWATTA', '19 - WATARAPPOLA', '18 - VIDYALAYA', '17 - GALKISSA', '16 - KAWDANA WEST',
  '15B - KAWDANA EAST', '22 - WATHUMULLA', '14 - KARAGAMPITIYA', '15A - KAWDANA EAST', '02 - DUTUGAMUNU',
  '02/03 - EKABADDA', '03 - KOHUWALA', '04 - KALUBOWILA', '06 - SARANANKARA', '07 - GALWALA',
  '05 - HATHBODIYA', '09 - DEHIWALA EAST', '10 - UDYANAYA', '11 - NEDIMALA', '12 - MALWATTA',
  '13 - JAYATHILAKA', '08 - DEHIWALA WEST', '05/06 - EKABADDA'
];

const routeInputsDiv = document.getElementById('routeInputs');


routes.forEach(route => {
  const div = document.createElement('div');
  div.className = 'col-md-4 mb-2';

  div.innerHTML = `
    <div class="card p-2">
      <label class="form-label">${route}</label>
      <input type="number" class="form-control waste-input" data-route="${route}" placeholder="Enter waste (Kg)">
    </div>
  `;
  routeInputsDiv.appendChild(div);
});

// Handle the submit button click.
document.getElementById('submitBtn').addEventListener('click', () => {
  const dumpDate = document.getElementById('dumpDate').value;
  const wasteRecords = {};

  document.querySelectorAll('.waste-input').forEach(input => {
    const route = input.getAttribute('data-route');
    const value = input.value;
    if (value.trim()) {
      wasteRecords[route] = value;
    }
  });

  if (!dumpDate || Object.keys(wasteRecords).length === 0) {
    alert("Please enter a date and at least one waste amount.");
    return;
  }

  fetch('/household/waste-entry/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dump_date: dumpDate, waste_records: wasteRecords })
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById('responseMessage').innerText = data.message || data.error;
  })
  .catch(error => console.error('Error:', error));
});
