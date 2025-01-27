from django.db import models

class Employee(models.Model):
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    employee_email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    IT = 'IT'
    HR = 'HR'
    SALES = 'SALES'
    MARKETING = 'MARKETING'
    ACCOUNTING = 'ACCOUNTING'
    DEPARTMENTS = [
        (IT, 'IT'),
        (HR, 'Human Resources'),
        (SALES, 'Sales'),
        (MARKETING, 'Marketing'),
        (ACCOUNTING, 'Accounting'),
    ]
    
    # Work-related Information
    employee_id = models.CharField(max_length=255, unique=True)
    position = models.CharField(max_length=255)
    department = models.CharField(
        max_length=255,
        choices=DEPARTMENTS,  # Use the choices defined above
        default=IT,  # Optional: set a default value
    )
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Employment Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    work_schedule = models.CharField(max_length=50)
    contract_type = models.CharField(max_length=50, choices=[('permanent', 'Permanent'), ('temporary', 'Temporary')])
    
    # Emergency Contact Information
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Qualifications and Certifications
    education_level = models.CharField(max_length=255, blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    
    # Role-Specific Information
    skills = models.TextField(blank=True, null=True)
    shift_preference = models.CharField(max_length=50, blank=True, null=True)
    equipment_assigned = models.TextField(blank=True, null=True)
    
    # Other Details
    profile_picture = models.ImageField(upload_to='employee_pics/', blank=True, null=True)
    date_of_last_performance_review = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
