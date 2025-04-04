// Chart for intent distribution
        let intentChart;

        // Load intent statistics
        function loadStatistics() {
            const days = document.getElementById('timeRange').value;

            // Get statistics
            fetch(`/chat/admin/intents?days=${days}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('statistics').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                        return;
                    }

                    // Update statistics display
                    let statsHtml = `<p><strong>Total Messages Analyzed:</strong> ${data.total_analyzed}</p>`;
                    statsHtml += '<div class="list-group">';

                    // Sort intents by percentage (descending)
                    const sortedIntents = Object.entries(data.percentages)
                        .sort((a, b) => b[1] - a[1]);

                    // Display each intent with percentage
                    sortedIntents.forEach(([intent, percentage]) => {
                        statsHtml += `
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                ${formatIntentName(intent)}
                                <span class="badge bg-primary rounded-pill">${percentage.toFixed(1)}%</span>
                            </div>
                        `;
                    });

                    statsHtml += '</div>';
                    document.getElementById('statistics').innerHTML = statsHtml;

                    // Update chart
                    updateChart(data);
                })
                .catch(error => {
                    console.error('Error loading statistics:', error);
                    document.getElementById('statistics').innerHTML =
                        `<div class="alert alert-danger">Error loading statistics: ${error.message}</div>`;
                });
        }

        // Load recent intents
        function loadRecentIntents() {
            fetch('/chat/admin/recent-intents')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('recentIntentsTable').innerHTML =
                            `<tr><td colspan="4" class="text-center text-danger">${data.error}</td></tr>`;
                        return;
                    }

                    if (!data.length) {
                        document.getElementById('recentIntentsTable').innerHTML =
                            `<tr><td colspan="4" class="text-center">No intent data available yet</td></tr>`;
                        return;
                    }

                    // Build table rows
                    let tableHtml = '';
                    data.forEach(record => {
                        const timestamp = new Date(record.timestamp).toLocaleString();
                        tableHtml += `
                            <tr>
                                <td>${timestamp}</td>
                                <td>${escapeHtml(record.user_message)}</td>
                                <td><span class="badge bg-secondary">${formatIntentName(record.predicted_intent)}</span></td>
                                <td>${(record.confidence * 100).toFixed(1)}%</td>
                            </tr>
                        `;
                    });

                    document.getElementById('recentIntentsTable').innerHTML = tableHtml;
                })
                .catch(error => {
                    console.error('Error loading recent intents:', error);
                    document.getElementById('recentIntentsTable').innerHTML =
                        `<tr><td colspan="4" class="text-center text-danger">Error: ${error.message}</td></tr>`;
                });
        }

        // Update the chart with new data
        function updateChart(data) {
            const intents = Object.keys(data.counts).map(intent => formatIntentName(intent));
            const counts = Object.values(data.counts);

            // Generate colors for the chart
            const colors = generateColors(intents.length);

            // Destroy previous chart if it exists
            if (intentChart) {
                intentChart.destroy();
            }

            // Create new chart
            const ctx = document.getElementById('intentChart').getContext('2d');
            intentChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: intents,
                    datasets: [{
                        data: counts,
                        backgroundColor: colors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        }
                    }
                }
            });
        }

        // Format intent name for display
        function formatIntentName(intent) {
            return intent
                .replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());
        }

        // Generate random colors for chart
        function generateColors(count) {
            const baseColors = [
                '#4CAF50', '#2196F3', '#9C27B0', '#FF9800', '#F44336',
                '#009688', '#3F51B5', '#FFEB3B', '#795548', '#607D8B'
            ];

            // If we need more colors than our base set, generate additional ones
            const colors = [];
            for (let i = 0; i < count; i++) {
                if (i < baseColors.length) {
                    colors.push(baseColors[i]);
                } else {
                    // Generate random colors if we run out of base colors
                    const hue = (i * 137) % 360; // Golden angle to spread colors evenly
                    colors.push(`hsl(${hue}, 70%, 60%)`);
                }
            }
            return colors;
        }

        function escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function initDashboard() {
            // Load initial data
            loadStatistics();
            loadRecentIntents();

            // Set up refresh interval (every 60 seconds)
            setInterval(() => {
                loadStatistics();
                loadRecentIntents();
            }, 60000);
        }

        document.addEventListener('DOMContentLoaded', initDashboard);

        