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

    // 4. Calculate 6 Rolling Months & Initialize Fee Table
    initRollingMonthColumns();

    // 5. Monthly Excel Download Modal handler
    const downloadMonthlyExcelBtn = document.getElementById('downloadMonthlyExcelBtn');
    if (downloadMonthlyExcelBtn) {
        downloadMonthlyExcelBtn.addEventListener('click', function () {
            const exportMonthInput = document.getElementById('exportMonthInput');
            if (exportMonthInput && exportMonthInput.value) {
                window.location.href = `/payments/export_monthly/${exportMonthInput.value}`;
                const modalEl = document.getElementById('exportMonthlyModal');
                if (modalEl && bootstrap.Modal.getInstance(modalEl)) {
                    bootstrap.Modal.getInstance(modalEl).hide();
                }
            }
        });
    }
});

// Calculate Rolling 6 Months with 3-Day EOM Rule
function getVisibleMonths() {
    const monthsName = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const now = new Date();
    
    let currentYear = now.getFullYear();
    let currentMonthIdx = now.getMonth();
    const currentDate = now.getDate();
    
    const daysInMonth = new Date(currentYear, currentMonthIdx + 1, 0).getDate();
    
    if ((daysInMonth - currentDate) <= 3) {
        currentMonthIdx += 1;
        if (currentMonthIdx > 11) {
            currentMonthIdx = 0;
            currentYear += 1;
        }
    }
    
    const visibleMonths = [];
    for (let i = 5; i >= 0; i--) {
        let mIdx = currentMonthIdx - i;
        let yr = currentYear;
        if (mIdx < 0) {
            mIdx += 12;
            yr -= 1;
        }
        const mNum = String(mIdx + 1).padStart(2, '0');
        visibleMonths.push({
            name: monthsName[mIdx],
            year: yr,
            code: `${yr}-${mNum}`,
            key: `${monthsName[mIdx]}_${yr}`
        });
    }
    return visibleMonths;
}

let activePaymentContext = null;

function initRollingMonthColumns() {
    const monthHeaderRow = document.getElementById('monthHeaders');
    if (!monthHeaderRow) return;

    const visibleMonths = getVisibleMonths();
    
    monthHeaderRow.innerHTML = `
        <th class="sticky-col first-col">Student Name</th>
        <th class="sticky-col second-col">Floor</th>
        <th>Hall</th>
        <th>Phone</th>
        <th>Monthly Fee</th>
        ${visibleMonths.map(m => `<th>${m.name} ${m.year}</th>`).join('')}
    `;

    const studentRows = document.querySelectorAll('.fee-student-row');
    studentRows.forEach(row => {
        const studentId = row.getAttribute('data-student-id');
        const studentName = row.getAttribute('data-student-name') || row.querySelector('.first-col').innerText;
        const monthlyFee = parseFloat(row.getAttribute('data-monthly-fee') || '0');
        const joinMonth = row.getAttribute('data-join-month') || '2026-01';
        const existingCells = row.querySelectorAll('.month-cell-data');
        
        let cellHtml = '';
        visibleMonths.forEach(m => {
            const existingStatus = row.getAttribute(`data-pay-${m.name}-${m.year}`) || 'Pending';
            const existingAmt = row.getAttribute(`data-amt-${m.name}-${m.year}`) || '';
            const existingMethod = row.getAttribute(`data-method-${m.name}-${m.year}`) || '';

            const paidAmt = parseFloat(existingAmt || '0');
            const balAmt = Math.max(0, monthlyFee - paidAmt);

            // Check Join Month N/A Logic (comparing YYYY-MM strings)
            if (m.code < joinMonth) {
                cellHtml += `
                    <td class="month-cell-data text-center">
                        <span class="badge bg-secondary px-3 py-2">Not Applicable</span>
                    </td>
                `;
            } else if (existingStatus === 'Paid') {
                cellHtml += `
                    <td class="month-cell-data text-center" id="cell-${studentId}-${m.name}-${m.year}">
                        <div class="border rounded-3 p-2 shadow-sm bg-white cursor-pointer hover-scale" 
                             onclick="triggerPaymentModal('${studentId}', '${escapeHtml(studentName)}', '${m.name}', '${m.year}', '${existingAmt}', '${existingMethod}', '${monthlyFee}')">
                            <div class="d-flex justify-content-center align-items-center gap-1 mb-1 flex-wrap">
                                <span class="badge bg-success px-2 py-1">PAID: ₹${paidAmt}</span>
                                ${balAmt > 0 
                                    ? `<span class="badge bg-danger px-2 py-1">BAL: ₹${balAmt}</span>` 
                                    : `<span class="badge bg-success-subtle text-success border px-2 py-1">FULL</span>`
                                }
                            </div>
                            <div class="small text-muted fw-semibold">${existingMethod}</div>
                        </div>
                    </td>
                `;
            } else {
                cellHtml += `
                    <td class="month-cell-data text-center" id="cell-${studentId}-${m.name}-${m.year}">
                        <button type="button" 
                                class="btn btn-sm btn-status-pending px-3 py-2 fw-bold" 
                                onclick="triggerPaymentModal('${studentId}', '${escapeHtml(studentName)}', '${m.name}', '${m.year}', '', '', '${monthlyFee}')">
                            PENDING
                        </button>
                    </td>
                `;
            }
        });
        
        existingCells.forEach(c => c.remove());
        row.insertAdjacentHTML('beforeend', cellHtml);
    });

    // Save Payment Modal handler
    const savePaymentBtn = document.getElementById('savePaymentBtn');
    if (savePaymentBtn) {
        savePaymentBtn.onclick = processPaymentSubmission;
    }
    
    const payModalPin = document.getElementById('payModalPin');
    if (payModalPin) {
        payModalPin.onkeypress = function(e) {
            if (e.key === 'Enter') processPaymentSubmission();
        };
    }

    const payModalAmount = document.getElementById('payModalAmount');
    if (payModalAmount) {
        payModalAmount.oninput = updateModalBalanceCalculation;
    }
}

function escapeHtml(text) {
    return text.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

function updateModalBalanceCalculation() {
    if (!activePaymentContext) return;
    const monthlyFee = parseFloat(activePaymentContext.monthlyFee || 0);
    const amountInput = document.getElementById('payModalAmount');
    const enteredAmt = parseFloat(amountInput ? amountInput.value : 0) || 0;
    const bal = Math.max(0, monthlyFee - enteredAmt);

    const balDisplay = document.getElementById('payModalBalanceCalc');
    if (balDisplay) {
        if (monthlyFee > 0) {
            balDisplay.innerHTML = `Remaining Balance: <strong class="${bal > 0 ? 'text-danger' : 'text-success'}">₹${bal}</strong>`;
        } else {
            balDisplay.innerHTML = `Paid Amount: <strong>₹${enteredAmt}</strong>`;
        }
    }
}

function triggerPaymentModal(studentId, studentName, month, year, currentAmt, currentMethod, monthlyFee) {
    activePaymentContext = {
        studentId: studentId,
        studentName: studentName,
        month: month,
        year: year,
        monthlyFee: parseFloat(monthlyFee || 0)
    };

    document.getElementById('payModalStudentName').innerText = studentName;
    document.getElementById('payModalMonthLabel').innerText = `${month} ${year}`;
    document.getElementById('payModalFeeDisplay').innerText = `Fee: ₹${monthlyFee || 0}`;
    document.getElementById('payModalAmount').value = currentAmt || '';
    document.getElementById('payModalMethod').value = currentMethod || '';
    document.getElementById('payModalPin').value = '';

    updateModalBalanceCalculation();

    const errorMsg = document.getElementById('pinErrorMsg');
    errorMsg.classList.add('d-none');
    errorMsg.innerText = '';

    const modal = new bootstrap.Modal(document.getElementById('monthPaymentModal'));
    modal.show();
    setTimeout(() => document.getElementById('payModalAmount').focus(), 400);
}

function processPaymentSubmission() {
    if (!activePaymentContext) return;

    const amountInput = document.getElementById('payModalAmount');
    const methodSelect = document.getElementById('payModalMethod');
    const pinInput = document.getElementById('payModalPin');
    const errorMsg = document.getElementById('pinErrorMsg');

    const amount = amountInput ? amountInput.value.trim() : '';
    const method = methodSelect ? methodSelect.value : '';
    const pin = pinInput ? pinInput.value.trim() : '';

    if (!amount || parseFloat(amount) <= 0) {
        errorMsg.innerText = 'Please enter a valid Amount.';
        errorMsg.classList.remove('d-none');
        amountInput.focus();
        return;
    }

    if (!method) {
        errorMsg.innerText = 'Please select a Payment Method (PhonePe or Cash).';
        errorMsg.classList.remove('d-none');
        methodSelect.focus();
        return;
    }

    if (!pin) {
        errorMsg.innerText = 'Please enter Security PIN.';
        errorMsg.classList.remove('d-none');
        pinInput.focus();
        return;
    }

    const { studentId, studentName, month, year, monthlyFee } = activePaymentContext;

    fetch('/payments/update_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            student_id: studentId,
            month: month,
            year: year,
            amount: amount,
            method: method,
            pin: pin,
            status: 'Paid'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const paidAmt = parseFloat(amount);
            const balAmt = Math.max(0, monthlyFee - paidAmt);

            // Update cell UI
            const cellId = `cell-${studentId}-${month}-${year}`;
            const cell = document.getElementById(cellId);
            if (cell) {
                cell.innerHTML = `
                    <div class="border rounded-3 p-2 shadow-sm bg-white cursor-pointer hover-scale"
                         onclick="triggerPaymentModal('${studentId}', '${escapeHtml(studentName)}', '${month}', '${year}', '${amount}', '${method}', '${monthlyFee}')">
                        <div class="d-flex justify-content-center align-items-center gap-1 mb-1 flex-wrap">
                            <span class="badge bg-success px-2 py-1">PAID: ₹${paidAmt}</span>
                            ${balAmt > 0 
                                ? `<span class="badge bg-danger px-2 py-1">BAL: ₹${balAmt}</span>` 
                                : `<span class="badge bg-success-subtle text-success border px-2 py-1">FULL</span>`
                            }
                        </div>
                        <div class="small text-muted fw-semibold">${method}</div>
                    </div>
                `;
            }

            // Hide Modal
            const modalEl = document.getElementById('monthPaymentModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            if (modalInstance) modalInstance.hide();

            activePaymentContext = null;
        } else {
            errorMsg.innerText = data.error || 'Invalid Security PIN';
            errorMsg.classList.remove('d-none');
        }
    })
    .catch(err => {
        console.error('Error confirming payment:', err);
        errorMsg.innerText = 'Network error. Please try again.';
        errorMsg.classList.remove('d-none');
    });
}
