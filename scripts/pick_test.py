from django.core.urlresolvers import reverse
from backends.api.v2.picks import PickView

def run():

    print("run")
    print(reverse('picks'))
