document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navUl = document.querySelector('nav ul');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            navUl.classList.toggle('active');
        });
    }
    
    // Close flash messages
    const closeButtons = document.querySelectorAll('.closebtn');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });
    
    // Appointment tabs
    const appointmentTabs = document.querySelectorAll('.appointment-tab');
    if (appointmentTabs.length > 0) {
        appointmentTabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                appointmentTabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Show/hide appointment listings based on status
                const status = this.getAttribute('data-status');
                const appointments = document.querySelectorAll('.appointment-card');
                
                appointments.forEach(function(appointment) {
                    if (status === 'all') {
                        appointment.style.display = 'block';
                    } else {
                        const appointmentStatus = appointment.getAttribute('data-status');
                        appointment.style.display = appointmentStatus === status ? 'block' : 'none';
                    }
                });
            });
        });
    }
    
    // Profile tabs
    const profileTabs = document.querySelectorAll('.profile-tab');
    if (profileTabs.length > 0) {
        profileTabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                profileTabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Show the corresponding tab content
                const tabId = this.getAttribute('data-tab');
                const tabContents = document.querySelectorAll('.profile-tab-content');
                
                tabContents.forEach(function(content) {
                    content.classList.remove('active');
                    if (content.getAttribute('id') === tabId) {
                        content.classList.add('active');
                    }
                });
            });
        });
    }
    
    // Ailment tabs
    const ailmentTabs = document.querySelectorAll('.ailment-tab');
    if (ailmentTabs.length > 0) {
        ailmentTabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                ailmentTabs.forEach(t => t.classList.remove('active'));
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Show the corresponding tab content
                const ailmentId = this.getAttribute('data-ailment');
                const ailmentContents = document.querySelectorAll('.ailment-content');
                
                ailmentContents.forEach(function(content) {
                    content.classList.remove('active');
                    if (content.getAttribute('id') === ailmentId) {
                        content.classList.add('active');
                    }
                });
            });
        });
    }
    
    // Form validation for appointment booking
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            const doctor = document.getElementById('doctor_id').value;
            const date = document.getElementById('appointment_date').value;
            const time = document.getElementById('appointment_time').value;
            const reason = document.getElementById('reason').value;
            
            if (!doctor || !date || !time || !reason) {
                e.preventDefault();
                alert('Please fill in all fields to book an appointment.');
            }
        });
    }
    
    // Form validation for registration
    const registerForm = document.querySelector('form[action="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (password !== confirmPassword) {
                e.preventDefault();
                alert('Passwords do not match!');
            }
        });
    }
    
    // Form validation for profile update
    const profileUpdateForm = document.getElementById('profile-update-form');
    if (profileUpdateForm) {
        profileUpdateForm.addEventListener('submit', function(e) {
            const name = document.getElementById('name').value;
            const phone = document.getElementById('phone').value;
            
            if (!name || !phone) {
                e.preventDefault();
                alert('Name and phone number are required fields.');
            }
        });
    }
    
    // Date picker initialization (if using a date picker library)
    const datePicker = document.getElementById('appointment_date');
    if (datePicker) {
        // If you're using a library like flatpickr, you'd initialize it here
        // Example: flatpickr(datePicker, { minDate: "today" });
        // Since we're not using external libraries, we'll set min date manually
        const today = new Date().toISOString().split('T')[0];
        datePicker.setAttribute('min', today);
    }
    
    // Dashboard functionality
    const dashboardNavLinks = document.querySelectorAll('.dashboard-nav a');
    if (dashboardNavLinks.length > 0) {
        dashboardNavLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                // This would be for a single-page dashboard application
                // For a multi-page app, you might not need this
                if (link.getAttribute('href').startsWith('#')) {
                    e.preventDefault();
                    
                    // Remove active class from all links
                    dashboardNavLinks.forEach(l => l.classList.remove('active'));
                    // Add active class to clicked link
                    this.classList.add('active');
                    
                    // Show the corresponding section
                    const sectionId = this.getAttribute('href').substring(1);
                    const sections = document.querySelectorAll('.dashboard-section');
                    
                    sections.forEach(function(section) {
                        section.style.display = 'none';
                        if (section.getAttribute('id') === sectionId) {
                            section.style.display = 'block';
                        }
                    });
                }
            });
        });
    }
});