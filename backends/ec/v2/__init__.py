from django.conf.urls import url, include

from .brands import router as brand
from .categories import router as category
from .products import router as product
from .users import router as user

urls = [
    url(r'', include(brand.urls)),
    url(r'', include(product.urls)),
    url(r'', include(category.urls)),
    url(r'', include(user.urls)),
]
