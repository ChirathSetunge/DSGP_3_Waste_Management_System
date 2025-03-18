document.addEventListener("DOMContentLoaded", function () {
    const predictBtn = document.getElementById("predictBtn");
    const predictionResult = document.getElementById("predictionResult");

    predictBtn.addEventListener("click", function () {


        const date = document.getElementById("dumpDate").value;
        const precipitation = parseFloat(document.getElementById("precipitation").value);
        const dailyPatients = parseInt(document.getElementById("dailyPatients").value);

        if (!date || isNaN(precipitation) || isNaN(dailyPatients)) {
            predictionResult.innerHTML = "<span class='text-danger'>Please enter valid inputs.</span>";
            return;
        }


        const requestData = {
            date: date,
            precipitation_sum: precipitation,
            daily_patients: dailyPatients
        };
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
            }
        })
        .catch(error => {
            predictionResult.innerHTML = "<span class='text-danger'>An error occurred. Please try again.</span>";
            console.error("Error:", error);
        });
    });
});