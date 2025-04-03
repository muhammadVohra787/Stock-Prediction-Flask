const stockSelect = document.getElementById('stockSelect');
const currentDateP = document.getElementById('current_date');
let initialDate = new Date(currentDateP.textContent); // Ensure it's initialized properly
const nextDayBtn = document.getElementById('next-day');
const prevDayBtn = document.getElementById('prev-day');
[stockSelect, nextDayBtn, prevDayBtn].forEach(function (element) {
    element.addEventListener('click', function () {
        let selectedStockSymbol = stockSelect.value; // Get stock symbol from dropdown

        // If the clicked element is a stock select dropdown, handle the logic for changing the stock symbol
        if (element === stockSelect) {
            selectedStockSymbol = this.value;
        } else {
            // For the day change buttons (nextDayBtn and prevDayBtn), calculate the new date
            changeDay(element === nextDayBtn ? 1 : -1); // Pass 1 for next, -1 for prev
        }

        console.log('Selected stock symbol:', selectedStockSymbol);
        console.log('Current date:', currentDateP.textContent);

        // Make an AJAX POST request to the Flask backend
        fetch('/stock_selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'stock_symbol': selectedStockSymbol,
                'current_date': currentDateP.textContent
            })
        })
        .then(response => response.json())
        .then(data => {
            const stockData = Object.values(data.data).map(item => item['Close']); // Assuming 'Close' is the stock price
            generateStockChart(stockData, data.stockName, data.stockSymbol, data.labels, data.color);
        })
        .catch((error) => {
            console.error('Error sending data to server:', error);
        });
    });
});

function pickRandomColorFromList() {
    const colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF']; // Example list of 5 colors (Red, Green, Blue, Yellow, Magenta)
    const randomIndex = Math.floor(Math.random() * colors.length);
    return colors[randomIndex];
  }
  let chartInstance = null;
  let currentDayOffset = 0; 
  
  function generateStockChart(stockdata, stockName, stockSymbol,labels, color) {
      const data = {
          labels: labels,
          datasets: [{
              label: stockSymbol,
              data: stockdata,
              borderColor: color,
              fill: false
          }]
      };
  
      const config = {
          type: 'line',
          data: data,
          options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                  title: {
                      display: true,
                      text: stockName
                  }
              },
              scales: {
                  x: {
                      type: 'category',
                      title: {
                          display: true,
                          text: 'Time'
                      }
                  }
              }
          }
      };
  
      var ctx = document.getElementById('stockChart').getContext('2d');
  
      if (chartInstance) {
          chartInstance.destroy();
      }
  
      chartInstance = new Chart(ctx, config);
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