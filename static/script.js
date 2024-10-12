function updateLog(message) {
    const logElement = document.getElementById("log");
    logElement.value += message + "\n";
    logElement.scrollTop = logElement.scrollHeight;  // Scroll to the bottom
}

document.addEventListener("DOMContentLoaded", function() {
    const logs = {{ logs | tojson }};  // Make sure this line is included only once in your HTML
    logs.forEach(log => updateLog(log)); // Populate initial logs

    document.getElementById("crawlerForm").addEventListener("submit", function(event) {
        event.preventDefault();  // Prevent the default form submission
        const url = document.getElementById("url").value;
        const depth = document.getElementById("depth").value;
        const useSelenium = document.getElementById("selenium").value;

        updateLog(`Starting crawl on ${url} to depth ${depth}...`);

        // Send POST request to the server
        fetch('/crawl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url, depth: parseInt(depth), use_selenium: useSelenium === 'true' }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateLog(data.message); // Update logs with the response message
        })
        .catch((error) => {
            updateLog(`Error: ${error.message}`); // Log errors to the UI
        });
    });
});
