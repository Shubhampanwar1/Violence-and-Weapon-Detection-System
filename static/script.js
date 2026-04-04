// Global variable to remember the last alert we saw
let lastAlertText = ""; 

// ==========================================
// ENGINE 1: Real-Time Alert Logger & Audio Trigger (Runs every 1 second)
// ==========================================
setInterval(function() {
    fetch('/get_logs')
        .then(response => response.json())
        .then(data => {
            const weaponContainer = document.getElementById('weapon-logs');
            const violenceContainer = document.getElementById('violence-logs');
            
            // --- NEW: THE AUDIO ALARM LOGIC ---
            if (data.length > 0) {
                // Check if the newest alert from Python is different from our saved one
                if (data[0].text !== lastAlertText) {
                    
                    // It's a new threat! Grab the speaker and play the alarm
                    const alarm = document.getElementById('alert-sound');
                    alarm.currentTime = 0; // Rewind to the start in case it's already playing
                    
                    // Browsers block audio unless the user has clicked the screen at least once.
                    // The .catch() prevents the script from crashing if the browser blocks it.
                    alarm.play().catch(e => console.log("Click anywhere on the dashboard to enable audio."));
                    
                    // Save this new alert so we don't play the sound 30 times a second
                    lastAlertText = data[0].text; 
                }
            }

            // Clear existing UI logs
            weaponContainer.innerHTML = '';
            violenceContainer.innerHTML = '';
            
            let weaponCount = 0;
            let violenceCount = 0;
            
            data.forEach(log => {
                let li = document.createElement('li');
                li.textContent = log.text;
                li.style.marginBottom = "8px";
                li.style.fontFamily = "monospace";
                
                if (log.type === 'weapon') {
                    li.style.color = "#ff4c4c"; 
                    weaponContainer.appendChild(li);
                    weaponCount++;
                } else if (log.type === 'violence') {
                    li.style.color = "#f59e0b"; 
                    violenceContainer.appendChild(li);
                    violenceCount++;
                }
            });
            
            if (weaponCount === 0) weaponContainer.innerHTML = '<li style="color: gray;">Awaiting weapon alerts...</li>';
            if (violenceCount === 0) violenceContainer.innerHTML = '<li style="color: gray;">Awaiting violence alerts...</li>';
        })
        .catch(error => console.error('Error fetching logs:', error));
}, 1000);

// ==========================================
// ENGINE 2: System Heartbeat Checker (Runs every 2 seconds)
// ==========================================
setInterval(function() {
    fetch('/system_status')
        .then(response => response.json())
        .then(data => {
            const globalDot = document.getElementById('global-status-dot');
            const globalText = document.getElementById('global-status-text');
            
            if (data.system_online) {
                globalDot.className = 'status-indicator dot-green';
                globalText.textContent = 'System Active';
            } else {
                globalDot.className = 'status-indicator dot-red';
                globalText.textContent = 'System Inactive';
            }

            const yoloDot = document.getElementById('yolo-dot');
            yoloDot.className = data.yolo_active ? 'module-dot dot-green' : 'module-dot dot-red';

            const mpDot = document.getElementById('mp-dot');
            mpDot.className = data.mediapipe_active ? 'module-dot dot-green' : 'module-dot dot-red';
        })
        .catch(error => {
            document.getElementById('global-status-dot').className = 'status-indicator dot-red';
            document.getElementById('global-status-text').textContent = 'Connection Lost';
            document.getElementById('yolo-dot').className = 'module-dot dot-red';
            document.getElementById('mp-dot').className = 'module-dot dot-red';
        });
}, 2000);