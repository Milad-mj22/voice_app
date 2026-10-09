def business_context(request):
    """دسترسی Business به همه‌ی تمپلیت‌ها"""
    return {
        "current_business": getattr(request, "business", None),
    }