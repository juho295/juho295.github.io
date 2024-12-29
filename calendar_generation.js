

// GENERATE PLACEHOLDER TABLE

// Generate hourly time slots between 9am and 10pm
const times = ["9:00am","10:00am","11:00am","12:00pm","1:00pm","2:00pm","3:00pm","4:00pm","5:00pm","6:00pm","7:00pm","8:00pm","9:00pm","10:00pm"]

// Generate dates for the remaining days of the current week and the next 4 weeks
const today = new Date();
const startOfWeek = getStartOfWeek(today);
const totalDays = 5 * 7; // Current week + 4 full weeks
const dates = Array.from({ length: totalDays }, (_, i) => {
  const date = new Date(startOfWeek);
  date.setDate(startOfWeek.getDate() + i);
  return date.toISOString().split('T')[0];
});

// Create the table element
const table = document.createElement('table');
table.id = 'calendarTable';
// table.border = '1';
table.style.width = '100%';
table.style.borderCollapse = 'collapse';

// Generate the header row with placeholders for dates
const headerRow = document.createElement('tr');
const emptyHeader = document.createElement('th');
emptyHeader.textContent = 'Time';
headerRow.appendChild(emptyHeader);


// POPULATE TABLE

// Function to generate the calendar view
function generateCalendar(timesData) {

  // Get all dates for the week viewed
  dates.forEach(date => {
    const dateHeader = document.createElement('th');
    dateHeader.textContent = new Date(date).toDateString();
    dateHeader.dataset.date = date;
    headerRow.appendChild(dateHeader);
  });
  table.appendChild(headerRow);

  // Generate rows for each time slot
  times.forEach(time => {
    const row = document.createElement('tr');

    // First cell in the row is the time
    const timeCell = document.createElement('td');
    timeCell.textContent = time;
    row.appendChild(timeCell);

    // Generate cells for each date
    dates.forEach(date => {
      const cell = document.createElement('td');
      cell.dataset.date = date;
      cell.dataset.time = time;

      // Filter the data for the current date and time
      const entries = timesData.filter(
        entry => entry.Date === date && entry.Time === time && entry.Status === 'available'
      );

      // Group available courts by location
      if (entries.length > 0) {
        const groupedByLocation = entries.reduce((acc, entry) => {
          if (!acc[entry.Location]) {
            acc[entry.Location] = [];
          }
          acc[entry.Location].push(entry.Court.replace('Court ', ''));
          return acc;
        }, {});

        // Populate the cell with grouped information
        cell.textContent = Object.entries(groupedByLocation)
          .map(([location, courts]) => {
            if (courts.length > 4) {
              return `${location}: 5+ courts free`;
            }
            return `${location}: Courts ${courts.join(',')}`;
          })
          .join('; ');
      } else {
        cell.textContent = 'No courts available';
      }

      row.appendChild(cell);
    });

    table.appendChild(row);
  });

  // Append the table to the body (or a specific container)
  document.getElementById("calendarTable-container").appendChild(table);
}


//DATE HELPER FUNCTION

// Helper function to get the start of the week (Monday)
function getStartOfWeek(date) {
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day; // Adjust to Monday
  const startOfWeek = new Date(date);
  startOfWeek.setDate(date.getDate() + diff);
  return startOfWeek;
}

// Helper function to get the current week's dates (Monday to Sunday)
function getCurrentWeekDates(startDate = new Date()) {
  const startOfWeek = getStartOfWeek(startDate);
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(startOfWeek);
    date.setDate(startOfWeek.getDate() + i);
    return date.toISOString().split('T')[0];
  });
}

//UPDATE CALENDAR TO ONLY SHOW BY CHOSEN WEEK

// Function to update the table to show only the current week
function updateWeek(weekOffset) {
  const startOfWeek = getStartOfWeek(new Date());
  startOfWeek.setDate(startOfWeek.getDate() + weekOffset * 7);

  const datesToShow = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(startOfWeek);
    date.setDate(startOfWeek.getDate() + i);
    return date.toISOString().split('T')[0];
  });

  // Show/hide columns based on datesToShow
  const table = document.getElementById('calendarTable');
  const headers = table.querySelectorAll('th[data-date]');
  const cells = table.querySelectorAll('td[data-date]');

  headers.forEach(header => {
    header.style.display = datesToShow.includes(header.dataset.date) ? '' : 'none';
  });

  cells.forEach(cell => {
    cell.style.display = datesToShow.includes(cell.dataset.date) ? '' : 'none';
  });
}

//LOAD CALENDAR

// Initialize the calendar and week navigation
function initCalendar(timesData) {
  generateCalendar(timesData);

  let currentWeekOffset = 0;
  updateWeek(currentWeekOffset);

  // Create navigation buttons
  // const navContainer = document.createElement('div');

  const prevButton = document.getElementById('prev-dates');
  prevButton.onclick = () => {
    currentWeekOffset--;
    updateWeek(currentWeekOffset);
  };

  const nextButton = document.getElementById('next-dates');
  nextButton.onclick = () => {
    currentWeekOffset++;
    updateWeek(currentWeekOffset);
  };

}

// Run the function to initialize the calendar
initCalendar(timesData);
