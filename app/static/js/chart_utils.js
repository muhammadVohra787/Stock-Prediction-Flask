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
const displayStock= async ()=>{
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

        const stockData = Object.values(data.data).map(item => item['Close']); // Extract 'Close' prices

        // Await the chart generation before hiding the spinner
        await generateStockChart(stockData, data.stockName, data.stockSymbol, data.labels, data.color);
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

function generateStockChart(stockData, stockName, stockSymbol, labels, color) {
    return new Promise((resolve, reject) => {
        try {
            const ctx = document.getElementById("stockChart").getContext("2d");

            // Destroy existing chart if it exists
            if (window.stockChartInstance) {
                window.stockChartInstance.destroy();
            }

            // Create new chart
            window.stockChartInstance = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: `${stockSymbol} - ${stockName}`,
                        data: stockData,
                        borderColor: color,
                        backgroundColor: color + "33", // Lighter color
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            console.log("promised resolved")

            resolve(); // Resolve the promise when chart is generated
        } catch (error) {
            reject(error); // Reject if there's an error
        }
    });
}
const changeDay = (num) => {
    const currentDateStr = currentDateP.textContent;
    const [year, month, day] = currentDateStr.split('-').map(Number);
    const currentDate = new Date(year, month - 1, day); // Month is 0-indexed in JS
    currentDate.setHours(0, 0, 0, 0);

    // Create new date based on the current date and the change in days
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + num);

    // Check if the new day is a weekend (Saturday or Sunday) and adjust accordingly
    const dayOfWeek = newDate.getDay(); // 0 is Sunday, 6 is Saturday
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    console.log(days[dayOfWeek], dayOfWeek);

    // Skip weekends
    if (num > 0) { // Moving forward
        if (dayOfWeek === 6) { // Saturday
            console.log("Forward: Saturday found, moving to Monday");
            newDate.setDate(newDate.getDate() + 2); // Move to Monday
        } else if (dayOfWeek === 0) { // Sunday
            console.log("Forward: Sunday found, moving to Monday");
            newDate.setDate(newDate.getDate() + 1); // Move to Monday
        }
    } else if (num < 0) { // Moving backward
        if (dayOfWeek === 0) { // Sunday
            console.log("Backward: Sunday found, moving to Friday");
            newDate.setDate(newDate.getDate() - 2); // Move to Friday
        } else if (dayOfWeek === 6) { // Saturday
            console.log("Backward: Saturday found, moving to Friday");
            newDate.setDate(newDate.getDate() - 1); // Move to Friday
        }
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today); // Create a copy of today's date
    yesterday.setDate(yesterday.getDate() - 1); // Subtract one day
    // Prevent going beyond today's date
    if (num > 0 && newDate >= yesterday) {
        console.log("Cannot go beyond today's date.");
        nextDayBtn.disabled = true;
    } else {
        nextDayBtn.disabled = false; // Enable the next button when valid
    }

    // Calculate difference from initial date and ensure we can't go back more than 5 days
    const initialDateMidnight = new Date(initialDate);
    initialDateMidnight.setHours(0, 0, 0, 0);

    // Format the new date as YYYY-MM-DD
    const [newYear, newMonth, newDay] = [newDate.getFullYear(), newDate.getMonth() + 1, newDate.getDate()];
    const newDateStr = `${newYear}-${String(newMonth).padStart(2, '0')}-${String(newDay).padStart(2, '0')}`;

    // Update the displayed date
    currentDateP.textContent = newDateStr;
};