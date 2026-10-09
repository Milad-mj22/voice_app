from .models import Business


class BusinessMiddleware:
    """
    تشخیص کسب‌وکار از روی slug توی URL
    مثال: merdas.mykaman.ir/ali/dashboard/
    → request.business = Business(slug='ali')
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.business = None

        # اگه کاربر لاگین کرده، business خودش رو داره
        if request.user.is_authenticated and request.user.business_id:
            request.business = request.user.business

        # اگه توی URL یه slug هست، از اون استفاده کن
        resolver = getattr(request, "resolver_match", None)
        if resolver:
            slug = resolver.kwargs.get("business_slug")
            if slug:
                biz = Business.objects.filter(slug=slug, is_active=True).first()
                if biz:
                    request.business = biz

        return self.get_response(request)