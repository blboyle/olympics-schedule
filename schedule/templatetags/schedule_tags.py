from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Build query string preserving existing params."""
    request = context.get("request")
    if not request:
        return urlencode(kwargs)

    params = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        elif key in params:
            del params[key]
    return params.urlencode()


@register.filter
def toggle_dir(current_dir):
    """Toggle sort direction."""
    return "desc" if current_dir == "asc" else "asc"


# Map Olympic country codes to ISO 2-letter codes for flag emojis
NOC_TO_ISO = {
    "AIN": "XX", "ALB": "AL", "AND": "AD", "ARG": "AR", "ARM": "AM",
    "AUS": "AU", "AUT": "AT", "AZE": "AZ", "BEL": "BE", "BEN": "BJ",
    "BIH": "BA", "BOL": "BO", "BRA": "BR", "BUL": "BG", "CAN": "CA",
    "CHI": "CL", "CHN": "CN", "COL": "CO", "CRO": "HR", "CYP": "CY",
    "CZE": "CZ", "DEN": "DK", "ECU": "EC", "ERI": "ER", "ESP": "ES",
    "EST": "EE", "FIN": "FI", "FRA": "FR", "GBR": "GB", "GEO": "GE",
    "GER": "DE", "GRE": "GR", "GBS": "GW", "HAI": "HT", "HKG": "HK",
    "HUN": "HU", "IND": "IN", "IRI": "IR", "IRL": "IE", "ISL": "IS",
    "ISR": "IL", "ITA": "IT", "JAM": "JM", "JPN": "JP", "KAZ": "KZ",
    "KEN": "KE", "KGZ": "KG", "KOR": "KR", "KOS": "XK", "KSA": "SA",
    "LAT": "LV", "LBN": "LB", "LIE": "LI", "LTU": "LT", "LUX": "LU",
    "MAD": "MG", "MAS": "MY", "MDA": "MD", "MEX": "MX", "MGL": "MN",
    "MKD": "MK", "MLT": "MT", "MNE": "ME", "MON": "MC", "MAR": "MA",
    "NED": "NL", "NGR": "NG", "NOR": "NO", "NZL": "NZ", "PAK": "PK",
    "PHI": "PH", "POL": "PL", "POR": "PT", "PUR": "PR", "ROU": "RO",
    "RSA": "ZA", "SGP": "SG", "SLO": "SI", "SMR": "SM", "SRB": "RS",
    "SUI": "CH", "SVK": "SK", "SWE": "SE", "THA": "TH", "TPE": "TW",
    "TTO": "TT", "TUR": "TR", "UAE": "AE", "UKR": "UA", "URU": "UY",
    "USA": "US", "UZB": "UZ", "VEN": "VE",
}


@register.filter
def country_flag(noc_code):
    """Convert NOC code to flag emoji."""
    iso = NOC_TO_ISO.get(noc_code, noc_code)
    if len(iso) != 2:
        return ""
    # Convert to regional indicator symbols (flag emoji)
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso.upper())
