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