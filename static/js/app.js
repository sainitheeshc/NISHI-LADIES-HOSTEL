// NISHI LADIES HOSTEL - Interactive JS Application
document.addEventListener('DOMContentLoaded', function () {
    // 1. Sidebar Toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    if (sidebarCollapse && sidebar) {
        sidebarCollapse.addEventListener('click', function () {
            sidebar.classList.toggle('active');
        });
    }

    // 2. Live Search for Student & Payment tables
    const studentSearchInput = document.getElementById('studentSearch');
    if (studentSearchInput) {
        studentSearchInput.addEventListener('input', function () {
            const filter = this.value.toLowerCase().trim();
            const tableRows = document.querySelectorAll('.searchable-table tbody tr');

            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 3. Counter Animation for Dashboard Cards
    const counters = document.querySelectorAll('.counter-anim');
    counters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-target') || counter.innerText.replace(/[^0-9.]/g, ''));
        if (isNaN(target)) return;

        const isCurrency = counter.innerText.includes('₹');
        let start = 0;
        const duration = 1000;
        const stepTime = 20;
        const steps = duration / stepTime;
        const increment = target / steps;

        const timer = setInterval(() => {
            start += increment;
            if (start >= target) {
                start = target;
                clearInterval(timer);
            }
            if (isCurrency) {
                counter.innerText = '₹' + Math.floor(start).toLocaleString();
            } else {
                counter.innerText = Math.floor(start);
            }
        }, stepTime);
    });

    // 4. Calculate 6 Rolling Months with 3-Day EOM Auto-Advance Rule
    initRollingMonthColumns();
});

// Calculate Rolling 6 Months with 3-Day Threshold Logic
function getVisibleMonths() {
    const monthsName = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const now = new Date();
    
    let currentYear = now.getFullYear();
    let currentMonthIdx = now.getMonth();
    const currentDate = now.getDate();
    
    // Total days in current month
    const daysInMonth = new Date(currentYear, currentMonthIdx + 1, 0).getDate();
    
    // Check if within 3 days of ending (e.g. 28th, 29th, 30th, 31st depending on month length)
    if ((daysInMonth - currentDate) <= 3) {
        currentMonthIdx += 1;
        if (currentMonthIdx > 11) {
            currentMonthIdx = 0;
            currentYear += 1;
        }
    }
    
    // Produce the 6 visible months leading up to currentMonthIdx
    const visibleMonths = [];
    for (let i = 5; i >= 0; i--) {
        let mIdx = currentMonthIdx - i;
        let yr = currentYear;
        if (mIdx < 0) {
            mIdx += 12;
            yr -= 1;
        }
        visibleMonths.push({
            name: monthsName[mIdx],
            year: yr,
            key: `${monthsName[mIdx]}_${yr}`
        });
    }
    return visibleMonths;
}

function initRollingMonthColumns() {
    const monthHeaderRow = document.getElementById('monthHeaders');
    if (!monthHeaderRow) return;

    const visibleMonths = getVisibleMonths();
    
    // Render dynamic table headers
    monthHeaderRow.innerHTML = `
        <th>Name</th>
        <th>Room</th>
        <th>Phone</th>
        ${visibleMonths.map(m => `<th>${m.name} ${m.year}</th>`).join('')}
    `;

    // Render cells for each student row
    const studentRows = document.querySelectorAll('.fee-student-row');
    studentRows.forEach(row => {
        const studentId = row.getAttribute('data-student-id');
        const existingCells = row.querySelectorAll('.month-cell-data');
        
        let cellHtml = '';
        visibleMonths.forEach(m => {
            // Read status from existing data attributes if present
            const statusKey = `${studentId}_${m.name}_${m.year}`;
            const existingStatus = row.getAttribute(`data-pay-${m.name}-${m.year}`) || 'Pending';
            
            const isPaid = existingStatus === 'Paid';
            const btnClass = isPaid ? 'btn-status-paid' : 'btn-status-pending';
            const btnText = isPaid ? 'PAID' : 'PENDING';
            
            cellHtml += `
                <td>
                    <button type="button" 
                            class="btn btn-sm ${btnClass} toggle-pay-btn" 
                            data-student-id="${studentId}" 
                            data-month="${m.name}" 
                            data-year="${m.year}"
                            data-status="${existingStatus}">
                        ${btnText}
                    </button>
                </td>
            `;
        });
        
        // Remove old month cells and append new dynamic cells
        existingCells.forEach(c => c.remove());
        row.insertAdjacentHTML('beforeend', cellHtml);
    });

    // Add click event listeners for dynamic status toggling
    document.querySelectorAll('.toggle-pay-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            togglePaymentStatus(this);
        });
    });
}

// Toggle Paid/Pending Status Instantly
function togglePaymentStatus(btn) {
    const studentId = btn.getAttribute('data-student-id');
    const month = btn.getAttribute('data-month');
    const year = btn.getAttribute('data-year');
    const currentStatus = btn.getAttribute('data-status');

    const newStatus = (currentStatus === 'Paid') ? 'Pending' : 'Paid';

    // Instant UI update for instant feedback
    if (newStatus === 'Paid') {
        btn.className = 'btn btn-sm btn-status-paid toggle-pay-btn';
        btn.innerText = 'PAID';
        btn.setAttribute('data-status', 'Paid');
    } else {
        btn.className = 'btn btn-sm btn-status-pending toggle-pay-btn';
        btn.innerText = 'PENDING';
        btn.setAttribute('data-status', 'Pending');
    }

    // Background server call to persist state
    fetch('/payments/update_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            student_id: studentId,
            month: month,
            year: year,
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to update status on server:', data.error);
        }
    })
    .catch(err => {
        console.error('Network error updating payment:', err);
    });
}
