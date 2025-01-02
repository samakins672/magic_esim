// Example eSIM API response
const esimsData = [
    {
      plan: "United Arab Emirates 20GB 30Days",
      status: "In Use",
      dataLeft: { gb: 16, percentage: 82 },
      timeLeft: { days: 28, hours: 23 },
      activateBefore: "2025-06-30",
      iccid: "89852240400025687146",
    },
    {
      plan: "United States 10GB 14Days",
      status: "Pending Activation",
      dataLeft: { gb: 10, percentage: 100 },
      timeLeft: { days: 14, hours: 0 },
      activateBefore: "2025-05-01",
      iccid: "89852240400025687147",
    },
  ];
  
  // Function to populate the eSIMs table
  function populateEsimsTable(esims) {
    const $tableBody = $("#esims-table-body");
    $tableBody.empty(); // Clear any existing rows
  
    esims.forEach((esim) => {
      const row = `
        <tr>
          <td>${esim.plan}</td>
          <td><span class="badge ${
            esim.status === "In Use" ? "bg-label-success" : "bg-label-warning"
          }">${esim.status}</span></td>
          <td>≈ ${esim.dataLeft.gb}GB (${esim.dataLeft.percentage}%)</td>
          <td>${esim.timeLeft.days} days ${esim.timeLeft.hours} hours</td>
          <td>${formatDate(esim.activateBefore)}</td>
          <td>${esim.iccid}</td>
        </tr>
      `;
  
      $tableBody.append(row);
    });
  }
  
  // Helper function to format date (e.g., "2025-06-30" -> "Jun 30, 2025")
  function formatDate(dateStr) {
    const date = new Date(dateStr);
    const monthNames = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];
    const day = date.getDate();
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();
    return `${month} ${day}, ${year}`;
  }
  
  // Helper function to truncate text (e.g., ICCID)
  function truncateText(text, charLimit) {
    if (!text) return "";
    if (text.length > charLimit) {
      return text.slice(0, charLimit);
    }
    return text;
  }
  
  // Populate the table on page load
  $(document).ready(function () {
    populateEsimsTable(esimsData);
  });
  