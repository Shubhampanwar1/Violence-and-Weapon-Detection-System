let lastAlertText = ""; 

setInterval(function() {
    fetch('/get_logs')
        .then(response => response.json())
        .then(data => {
            const weaponContainer = document.getElementById('weapon-logs');
            const violenceContainer = document.getElementById('violence-logs');
            
            if (data.length > 0) {
                if (data[0].text !== lastAlertText) {
                    const alarm = document.getElementById('alert-sound');
                    alarm.currentTime = 0; 
                    alarm.play().catch(e => console.log("Audio requires user interaction to start."));
                    lastAlertText = data[0].text; 
                }
            }

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