from django.conf.urls import url, include

from .accounts import (
    sign_in, sign_up, verify_email, inactive_user, chanage_password,
    issue_temporary_password, connection_socialaccount, disconnection_socialaccount,
    auto_login_android, verify_nickname,
    push_token_update
)
from .adrresses import router as address
from .awards import router as award
from .brands import router as brand
from .categories import router as category
from .common import app_message, initialize, user_model_synchronization
from .common import router as service_setting
from .events import router as event
from .filters import router as filter
from .mains import router as main
from .notices import router as notices
from .picks import router as pick
from .products import router as product
from .questions import router as ask
from .recommends import router as recommend
from .reviews import router as review
from .stores import router as store
from .tags import router as tag
from .users import router as user
from .inquiries import router as inquiry
from .faqs import router as faq
from .messages import router as message

urls = [
    url(r'', include(main.urls)),
    url(r'', include(user.urls)),
    url(r'', include(address.urls)),
    url(r'', include(notices.urls)),
    url(r'', include(service_setting.urls)),
    url(r'', include(review.urls)),
    url(r'', include(product.urls)),
    url(r'', include(brand.urls)),
    url(r'', include(store.urls)),
    url(r'', include(category.urls)),
    url(r'', include(tag.urls)),
    url(r'', include(filter.urls)),
    url(r'', include(recommend.urls)),
    url(r'', include(pick.urls)),
    url(r'', include(ask.urls)),
    url(r'', include(event.urls)),
    url(r'', include(award.urls)),
    url(r'', include(inquiry.urls)),
    url(r'', include(faq.urls)),
    url(r'', include(message.urls)),

    # account
    url(r'^account/signin$', sign_in),
    url(r'^account/signup$', sign_up),
    url(r'^account/email-verify$', verify_email),
    url(r'^account/nickname-verify$', verify_nickname),
    url(r'^account/change-password$', chanage_password),
    url(r'^account/temporary-password$', issue_temporary_password),
    url(r'^account/social/connection$', connection_socialaccount),
    url(r'^account/social/disconnection$', disconnection_socialaccount),
    url(r'^account/leave$', inactive_user),
    url(r'^account/signin/short-form$', auto_login_android),
    url(r'^account/token-update', push_token_update),

    # app message, splash product/review counting
    url(r'^app_message/(?P<os>\w+)/$', app_message),

    url(r'^initialization/$', initialize),

    # ec - service user model synchronization
    url(r'^users/ec/synchronization/$', user_model_synchronization),
]
