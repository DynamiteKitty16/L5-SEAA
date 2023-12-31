// Get manager's staff list and requests for users leave requests
document.addEventListener('DOMContentLoaded', function() {
    const employeeItems = document.querySelectorAll('.employee-item');
    const requestsTableBody = document.getElementById('requests-table-body');

    employeeItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            employeeItems.forEach(i => i.classList.remove('active'));

            // Add active class to clicked item
            this.classList.add('active');

            const employeeId = this.getAttribute('data-employee-id');

            fetch(`/get-employee-requests/${employeeId}/`)
                .then(response => response.json())
                .then(data => {
                    // Sort requests with 'Cancelled' status to the end
                    data.sort((a, b) => {
                        if (a.status === 'Cancelled' && b.status !== 'Cancelled') {
                            return 1;
                        }
                        if (a.status !== 'Cancelled' && b.status === 'Cancelled') {
                            return -1;
                        }
                        return 0;
                    });

                    requestsTableBody.innerHTML = '';
                    data.forEach(request => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${request.leave_type}</td>
                            <td>${request.start_date}</td>
                            <td>${request.end_date}</td>
                            <td>${request.status}</td>
                            <td>
                                ${generateActionButtons(request)}
                            </td>
                        `;
                        requestsTableBody.appendChild(row);
                    });
                    attachButtonEvents();
                })
                .catch(error => console.error('Error:', error));
        });
    });

    // Generate buttons based on status of the request
    function generateActionButtons(request) {
        let buttons = '';
        if (request.status === 'Pending') {
            buttons += `<button class="btn btn-success btn-sm approve-btn" data-request-id="${request.id}">Approve</button>`;
            buttons += `<button class="btn btn-danger btn-sm deny-btn" data-request-id="${request.id}">Deny</button>`;
        } else if (request.status === 'Approved') {
            buttons += `<button type="button" class="btn btn-warning btn-sm" data-bs-toggle="modal" data-bs-target="#cancelRequestModal" data-request-id="${request.id}">Cancel</button>`;
        }
        return buttons;
    }

    function attachButtonEvents() {
        document.querySelectorAll('.approve-btn').forEach(button => {
            button.addEventListener('click', function() {
                const requestId = this.getAttribute('data-request-id');
                handleApproval(requestId);
            });
        });

        document.querySelectorAll('.deny-btn').forEach(button => {
            button.addEventListener('click', function() {
                const requestId = this.getAttribute('data-request-id');
                handleDenial(requestId);
            });
        });
    }

    // Handling Approval button and front end logic
    function handleApproval(requestId) {
        fetch(`/approve-leave-request/${requestId}/`, { 
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateRequestStatus(requestId, 'Approved');
            }
        });
    }

    // Handling Denial button and front end logic
    function handleDenial(requestId) {
        fetch(`/deny-leave-request/${requestId}/`, { 
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateRequestStatus(requestId, 'Denied');
            }
        });
    }

    // Handling Cancellation button and front end logic
    function handleCancellation(requestId) {
        fetch(`/cancel-leave-request/`, { 
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ request_id: requestId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateRequestStatus(requestId, 'Cancelled');
            }
        });
    }

    // Update Request Status dependent on button
    function updateRequestStatus(requestId, newStatus) {
        const requestRow = document.querySelector(`button[data-request-id="${requestId}"]`).parentNode.parentNode;
        requestRow.cells[3].textContent = newStatus;
        if (newStatus === 'Approved') {
            requestRow.cells[4].innerHTML = `<button class="btn btn-warning btn-sm cancel-btn" data-request-id="${requestId}">Cancel</button>`;
            attachCancelEvent(requestRow.querySelector('.cancel-btn'));
        } else {
            requestRow.cells[4].innerHTML = '';
        }
    }

    // Allow manager to cancel if required
    function attachCancelEvent(button) {
        button.addEventListener('click', function() {
            const requestId = this.getAttribute('data-request-id');
            var confirmButton = document.getElementById('confirmCancel');
            confirmButton.setAttribute('data-request-id', requestId);
            var modal = new bootstrap.Modal(document.getElementById('cancelRequestModal'));
            modal.show();
        });
    }

    function getCsrfToken() {
        return document.cookie.split('; ').find(row => row.startsWith('csrftoken=')).split('=')[1];
    }
});
