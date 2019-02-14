import os
from datetime import datetime

from django.conf import settings
from django.db.models import F, Count, FloatField
from django.db.models import Value

from db.raw_queries import get_end_events
from libs.aws.dynamodb import aws_dynamodb_etc_list, aws_dynamodb_events
from libs.utils import iso8601, get_image_ratio
from models.events import Event


class EventService:
    def get_ongoing_evaluation_events(self, limit):
        events = Event.objects.ongoing().filter(is_evaluated=True).order_by('?').all()[:limit]
        for event in events:
            first_product = event.products.select_related(
                'brand'
            ).first()
            setattr(event, 'product', first_product)
        return events

    def get_list(self, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')

        term = kwargs.get('term')

        events = Event.objects.ongoing() if term == 'ongoing' else Event.objects.end_events()

        events = events.order_by(
            '-seq'
        ).select_related(
            'brand'
        ).annotate(
            comments_count=Count('users'),
            brand_name=F('brand__name')
        )

        cursor = int(cursor or 1)
        offset = (cursor - 1) * limit
        results = events.all()[offset: offset + limit + 1]

        if term == 'ongoing':
            for ev in results:
                setattr(ev, 'ratio', get_image_ratio(path=ev.event_image, is_url=True))
        elif term == 'end':
            results = get_end_events(**kwargs)
            # results = results.annotate(
            #     ratio=Value(0.5, output_field=FloatField())
            # )

        if not results:
            return {
                'list': [],
                'next_offset': None,
            }

        if not len(results):
            return {
                'list': [],
                'next_offset': None,
            }

        if len(results) == limit + 1:
            results = list(results)
            next_offset = cursor + 1
            del results[-1]
        else:
            next_offset = None

        return {
            'list': results,
            'next_offset': next_offset
        }

    def get_ongoing_events_by_dynamodb(self, **kwargs):
        limit = kwargs.get('limit', 20)
        cursor = kwargs.get('cursor')
        offset = (int(cursor or 1) - 1) * limit

        results = aws_dynamodb_etc_list.get_events()

        events = list()
        for event in reversed(results):
            item = dict()
            item['id'] = event.get('idAdminBoard').get('N')
            item['title'] = event.get('boardTitle').get('S')
            item['brand_name'] = event.get('brandTitle').get('S')
            item['comments_count'] = event.get('comment').get('S')
            item['seq'] = event.get('orderNum').get('N')
            item['event_image'] = "{}{}/{}".format(
                settings.CDN, event.get('fileDir').get('S'), event.get('fileSaveName').get('S')
            )
            path = os.path.splitext(event.get('fileSaveName').get('S'))
            thumbnail_path = '%s_720%s' % (path[0], path[1])
            item['event_image_720'] = "{}{}/{}".format(
                settings.CDN, event.get('fileDir').get('S'), thumbnail_path
            )
            item['ratio'] = round(float(event.get('ratio').get('S')), 3)
            item['started_at'] = iso8601(datetime.strptime(event.get('start_date').get('S'), "%Y%m%d%H%M%S"))
            item['ended_at'] = iso8601(datetime.strptime(event.get('end_date').get('S'), "%Y%m%d%H%M%S"))
            events.append(item)

        if not results:
            return {
                'list': [],
                'next_offset': None,
            }

        if not len(results):
            return {
                'list': [],
                'next_offset': None,
            }

        if len(events) > limit:
            next_offset = cursor + 1
            del events[limit - 1:]
        else:
            next_offset = None

        return {
            'list': events[offset:offset + limit],
            'next_offset': next_offset,
        }

    def get_event_by_dynamodb(self, event_id):
        res = aws_dynamodb_events.get_event(event_id=event_id)
        event = dict()
        event['id'] = res.get('idEvent').get('S')
        event['title'] = res.get('boardTitle').get('S')
        event['contents'] = res.get('boardText').get('S')

        event['link_type'] = res.get('eventLinkType').get('S')
        event['link_code'] = res.get('eventLinkCode').get('S')

        event['comments_count'] = res.get('requirement_count').get('S')
        event['event_image'] = "{}{}".format(
            settings.CDN, res.get('image_new').get('S')
        )
        event['event_image_720'] = "{}{}".format(
            settings.CDN, res.get('thumbnail_new').get('S')
        )
        event['ratio'] = event.get('ratio').get('S')
        event['started_at'] = iso8601(datetime.strptime(event.get('start_date').get('S'), "%Y%m%d%H%M%S"))
        event['ended_at'] = iso8601(datetime.strptime(event.get('end_date').get('S'), "%Y%m%d%H%M%S"))
        return event


service = EventService()
