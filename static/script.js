// ==========================================
// Real-Time Alert Logger (Runs every 1 second)
// ==========================================
setInterval(function() {
    fetch('/get_logs')
        .then(response => response.json())
        .then(data => {
            const logContainer = document.getElementById('real-time-logs');
            
            if (data.length > 0) {
                logContainer.innerHTML = ''; // Clear old logs
                
                data.forEach(log => {
                    let li = document.createElement('li');
                    li.textContent = log;
                    li.style.color = "#ff4c4c"; // Red for threats
                    li.style.marginBottom = "8px";
                    li.style.fontFamily = "monospace"; 
                    logContainer.appendChild(li);
                });
            }
        })
        .catch(error => console.error('Error fetching logs:', error));
}, 1000); 

// ==========================================
// ENGINE 1: YOLO model (Runs every 2 seconds)
// ==========================================
setInterval(function() {
    fetch('/system_status')
        .then(response => response.json())
        .then(data => {
            // Update Global System Status
            const globalDot = document.getElementById('global-status-dot');
            const globalText = document.getElementById('global-status-text');
            
            if (data.system_online) {
                globalDot.className = 'status-indicator dot-green';
                globalText.textContent = 'System Active';
            } else {
                globalDot.className = 'status-indicator dot-red';
                globalText.textContent = 'System Inactive';
            }

            // Update YOLO Module Status
            const yoloDot = document.getElementById('yolo-dot');
            yoloDot.className = data.yolo_active ? 'module-dot dot-green' : 'module-dot dot-red';

            // Update MediaPipe Module Status
            const mpDot = document.getElementById('mp-dot');
            mpDot.className = data.mediapipe_active ? 'module-dot dot-green' : 'module-dot dot-red';
        })
        .catch(error => {
            // If the fetch fails (Python server crashed)
            document.getElementById('global-status-dot').className = 'status-indicator dot-red';
            document.getElementById('global-status-text').textContent = 'Connection Lost';
            document.getElementById('yolo-dot').className = 'module-dot dot-red';
            document.getElementById('mp-dot').className = 'module-dot dot-red';
        });
}, 2000);