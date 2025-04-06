const stockSelect = document.getElementById('stockSelect');
const currentDateP = document.getElementById('current_date');
let initialDate = new Date(currentDateP.textContent); // Ensure it's initialized properly
const nextDayBtn = document.getElementById('next-day');
const prevDayBtn = document.getElementById('prev-day');
const spinner = document.getElementById("loadingSpinner");
const hideDiv = document.getElementById("stockChartVisible");

function fetchStockData(text) {
    // Show spinner
    if (text === "pending") {
        hideDiv.classList.add("hidden");
        spinner.classList.remove("hidden");
    } else {

        hideDiv.classList.remove("hidden");
        spinner.classList.add("hidden");
        console.log("stopped")

    }
}

async function runOnceOnLoad() {
    console.log("This function ran once the page finished loading.");
    await displayStock();

    window.removeEventListener('load', runOnceOnLoad);
}

// Attach the event listener to the window's 'load' event
window.addEventListener('load', runOnceOnLoad);

// Add event listener to all required elements
[nextDayBtn, prevDayBtn].forEach((element) => {
    element.addEventListener('click', async function () { // Make function async
        let selectedStockSymbol = stockSelect.value;

        // Handle stock selection or date change
        if (element !== stockSelect) {
            changeDay(element === nextDayBtn ? 1 : -1);
        }
        await displayStock();
    });
}
);
const displayStock = async () => {
    fetchStockData("pending"); // Show spinner before request starts

    let selectedStockSymbol = stockSelect.value;

    console.log('Selected stock symbol:', selectedStockSymbol);
    console.log('Current date:', currentDateP.textContent);

    try {
        // Make an AJAX request to Flask backend
        const response = await fetch('/stock_selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'stock_symbol': selectedStockSymbol,
                'current_date': currentDateP.textContent
            })
        });

        const data = await response.json();
        console.log(data)
        const stockData = Object.values(data.data)
            .map(item => item['Close'])
            .filter(value => !isNaN(value)); // Remove NaN values

        const stockPred = Object.values(data.data).map(item => item['predictions']);

        // Await the chart generation before hiding the spinner
        await generateStockChart(stockData, data.stockName, data.stockSymbol, data.labels, data.color, stockPred);
        fetchStockData("done"); // Hide spinner after everything completes

    } catch (error) {
        console.error('Error sending data to server:', error);
    } finally {

    }
}
// Add event listener to all required elements
[stockSelect].forEach((element) => {
    element.addEventListener('change', async function () { // Make function async
        let selectedStockSymbol = stockSelect.value;

        // Handle stock selection or date change
        if (element !== stockSelect) {
            changeDay(element === nextDayBtn ? 1 : -1);
        }
        await displayStock();
    });
});

function generateStockChart(stockData, stockName, stockSymbol, labels, color, stockPred) {
    return new Promise((resolve, reject) => {

        try {
            const ctx = document.getElementById("stockChart").getContext("2d");

            // Destroy existing chart if it exists
            if (window.stockChartInstance) {
                window.stockChartInstance.destroy();
            }
            Chart.defaults.color = 'white';
            // Create new chart
            window.stockChartInstance = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: `${stockSymbol} - ${stockName} (Actual)`,
                            data: stockData,
                            borderColor: color,
                            backgroundColor: color + "33",
                            fill: true
                        },
                        {
                            label: `${stockSymbol} - ${stockName} (Predicted)`,

                            data: stockPred,
                            borderColor: "rgb(255, 99, 132)",
                            backgroundColor: "rgb(255, 99, 132)" + "55",
                            borderDash: [5, 5], // Optional: dashed line for predicted
                            fill: false,
                            borderWidth: 2,
                            pointRadius: 3,
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    plugins: {
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            titleColor: 'white',
                            bodyColor: 'white',
                            backgroundColor: '#1e293b',
                        },
                    },
                }
            }

            );

            resolve(); // Resolve the promise when chart is generated
        } catch (error) {
            reject(error); // Reject if there's an error
        }
    });
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Adjusted changeDay function to account for weekend restrictions
const changeDay = (num) => {
    console.log("Button clicked with num:", num);

    const currentDateStr = currentDateP.textContent;
    const [year, month, day] = currentDateStr.split('-').map(Number);
    const currentDate = new Date(year, month - 1, day);
    currentDate.setHours(0, 0, 0, 0); // Normalize time

    let newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + num);

    // Skip weekends
    const adjustForWeekend = (date, direction) => {
        const day = date.getDay();
        if (direction > 0) {
            if (day === 6) date.setDate(date.getDate() + 2); // Saturday -> Monday
            if (day === 0) date.setDate(date.getDate() + 1); // Sunday -> Monday
        } else {
            if (day === 0) date.setDate(date.getDate() - 2); // Sunday -> Friday
            if (day === 6) date.setDate(date.getDate() - 1); // Saturday -> Friday
        }
        return date;
    };

    newDate = adjustForWeekend(newDate, num);

    const today = new Date();
    today.setHours(0, 0, 0, 0); // Normalize today's time

    // Prevent navigating into the future
    if (newDate > today) {
        console.warn("Blocked: Attempt to view future data");
        return;
    }

    // Update the display
    const newDateStr = formatDate(newDate);
    currentDateP.textContent = newDateStr;
    console.log("Updated current date:", newDateStr);

    // Check if "Next" should be disabled
    const nextDate = adjustForWeekend(new Date(newDate.getTime() + 24 * 60 * 60 * 1000), 1);
    if (nextDate > today) {
        nextDayBtn.setAttribute('disabled', true);
    } else {
        nextDayBtn.removeAttribute('disabled');
    }
};
