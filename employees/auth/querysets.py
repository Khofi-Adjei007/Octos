# employees/auth/querysets.py

def branch_safe_queryset(queryset, employee_context, branch_field="branch"):
    """
    Enforce branch-level filtering on a queryset.

    Args:
        queryset: Django queryset
        employee_context: EmployeeContext (authoritative)
        branch_field: field name on model that points to Branch

    Returns:
        Filtered queryset
    """

    # Multi-branch authority (HQ, regional, superuser)
    if employee_context.can_access_multiple_branches:
        return queryset

    # No branch context → empty queryset (fail closed)
    if not employee_context.branch_id:
        return queryset.none()

    return queryset.filter(**{f"{branch_field}_id": employee_context.branch_id})
