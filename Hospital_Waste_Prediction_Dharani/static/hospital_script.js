document.addEventListener("DOMContentLoaded", function () {
    const predictBtn = document.getElementById("predictBtn");
    const predictionResult = document.getElementById("predictionResult");

    document.getElementById("dumpDate").min = new Date().toISOString().split('T')[0];

    predictBtn.addEventListener("click", function () {
        // Get input values
        const date = document.getElementById("dumpDate").value;
        const precipitation = parseFloat(document.getElementById("precipitation").value);
        const dailyPatients = parseInt(document.getElementById("dailyPatients").value);

        if (!date || isNaN(precipitation) || isNaN(dailyPatients)) {
            predictionResult.innerHTML = "<span class='text-danger'>Please enter valid inputs.</span>";
            return;
        }

        if (dailyPatients <= 1) {
            predictionResult.innerHTML = "<span class='text-danger'>Minimum patient count should be 1.</span>";
            return;
        }
        if (precipitation <= 0) {
            predictionResult.innerHTML = "<span class='text-danger'>Precipitation should be greater than 0.</span>";
            return;
        }
        const selectedDate = new Date(date);
        const today = new Date();
        const now = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        if (selectedDate < now) {
            predictionResult.innerHTML = "<span class='text-danger'>Date should be today or in the future.</span>";
            return;
        }

        // Prepare data payload
        const requestData = {
            date: date,
            precipitation_sum: precipitation,
            daily_patients: dailyPatients
        };

        // Send POST request to Flask API
        fetch("/hospital/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                predictionResult.innerHTML = `<span class='text-danger'>Error: ${data.error}</span>`;
            } else {
                predictionResult.innerHTML = `<strong>Predicted Waste Weight:</strong> ${data.predicted_waste_weight.toFixed(2)} kg`;
                // Clear input fields
                document.getElementById("dumpDate").value = "";
                document.getElementById("precipitation").value = "";
                document.getElementById("dailyPatients").value = "";
            }
        })
        .catch(error => {
            predictionResult.innerHTML = "<span class='text-danger'>An error occurred. Please try again.</span>";
            console.error("Error:", error);
        });
    });
});
