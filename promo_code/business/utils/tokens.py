import rest_framework_simplejwt.tokens


def generate_company_tokens(company):
    """
    Generate JWT tokens for a company.
    """
    refresh = rest_framework_simplejwt.tokens.RefreshToken()
    refresh['user_type'] = 'company'
    refresh['company_id'] = str(company.id)
    refresh['token_version'] = company.token_version

    access = refresh.access_token
    access['user_type'] = 'company'
    access['company_id'] = str(company.id)

    return {
        'access': str(access),
        'refresh': str(refresh),
    }
