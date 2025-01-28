from django.db import models

class Employee(models.Model):
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    employee_email = models.EmailField(unique=True)
    phone_number = models.IntegerField(blank=False, null=False)
    date_of_birth = models.DateField(blank=False, null=False)
    address = models.TextField(blank=False, null=False)

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
    

    # Define levels of education
    PRIMARY = 'PRIMARY'
    JHS = 'JHS'  # Junior High School
    SHS = 'SHS'  # Senior High School
    UNDERGRADUATE = 'UNDERGRADUATE'
    POSTGRADUATE = 'POSTGRADUATE'
    DOCTORATE = 'DOCTORATE'
    VOCATIONAL = 'VOCATIONAL'
    OTHER = 'OTHER'

    # Levels of Education
    EDUCATION_LEVELS = [
        (PRIMARY, 'Primary'),
        (JHS, 'Junior High School'),
        (SHS, 'Senior High School'),
        (UNDERGRADUATE, 'Undergraduate'),
        (POSTGRADUATE, 'Postgraduate'),
        (DOCTORATE, 'Doctorate'),
        (VOCATIONAL, 'Vocational Training'),
        (OTHER, 'Other'),
    ]

    # Qualifications and Certifications
    education_level = models.CharField(max_length=255, blank=True, choices=EDUCATION_LEVELS, null=True)
    certifications = models.TextField(blank=True, null=True)
    
    # Role-Specific Information
    skills = models.TextField(blank=True, null=True)
    shift_preference = models.CharField(max_length=50, blank=True, null=True)

    EQUIPMENT_CHOICES = [
        ('LAPTOP', 'Laptop'),
        ('PHONE', 'Mobile Phone'),
        ('PRINTER', 'Printer'),
        ('HEADSET', 'Headset'),
        ('OTHER', 'Other'),
    ]

    equipment_assigned = models.CharField(
        max_length=50,
        choices=EQUIPMENT_CHOICES,
        blank=True,
        null=True,
        help_text="Select assigned equipment or choose 'Other' to specify."
    )

    equipment_other = models.TextField(
        blank=True,
        null=True,
        help_text="Specify equipment if not listed."
    )

    
    # Other Details
    profile_picture = models.ImageField(upload_to='employee_pics/', blank=True, null=True)
    date_of_last_performance_review = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
