from django.conf import settings
import os
import pickle

from models.products import SubCategory


def make_category_pickle():
    categories = SubCategory.objects.filter(is_display=True)

    import re
    category_dict = {}
    for c in categories:

        for k in set(re.findall("[\w]+", c.name)):
            category_dict.setdefault(k, [])
            category_dict[k].append(c.id)

    with open(os.path.join(settings.BASE_DIR, 'resources', 'sub_category.pkl'), 'wb') as f:
        pickle.dump(category_dict, f)


try:
    with open(os.path.join(settings.BASE_DIR, 'resources', 'sub_category.pkl'), 'rb') as f:
        d = pickle.load(f)
except:
    make_category_pickle()
    with open(os.path.join(settings.BASE_DIR, 'resources', 'sub_category.pkl'), 'rb') as f:
        d = pickle.load(f)


def get_category_id(words):
    if len(words) == 1:
        if len(words[0]) == 1:
            return [item for idlist in (d[word] for word in words if word in d.keys()) for item in idlist]

    return [item for idlist in (d[key] for word in words for key in d.keys() if word in key) for item in idlist]
