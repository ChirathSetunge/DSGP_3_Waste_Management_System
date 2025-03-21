document.addEventListener('DOMContentLoaded', function() {
  const ctx = document.getElementById('predictionChart').getContext('2d');
  const predictions = JSON.parse(sessionStorage.getItem('predictions')) || {};
  const labels = Object.keys(predictions);
  const data = Object.values(predictions);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'MSW Prediction (Kg)',
        data: data,
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

  // Clear the predictions after visualization
  sessionStorage.removeItem('predictions');
});
