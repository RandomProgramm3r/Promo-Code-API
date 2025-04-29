import business.models


def bump_company_token_version(company):
    """
    Increment token_version, save it, and return the fresh instance.
    """
    company = business.models.Company.objects.select_for_update().get(
        id=company.id,
    )
    company.token_version += 1
    company.save(update_fields=['token_version'])
    return company
